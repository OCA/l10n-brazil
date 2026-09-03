# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from lxml import etree

from odoo import api, fields, models

from .. import tools
from ..constants.fiscal import (
    FINAL_CUSTOMER_YES,
    FISCAL_IN,
    FISCAL_OUT,
    NFE_IND_IE_DEST_9,
    STATE_CODES,
    TAX_DOMAIN_ICMS,
    TAX_DOMAIN_ICMS_FCP,
    TAX_DOMAIN_ICMS_FCP_ST,
    TAX_DOMAIN_ICMS_ST,
)
from ..constants.icms import ICMS_ORIGIN_TAX_IMPORTED

VIEW = """
<page name="uf_{0}" string="{1}">
    <notebook>
        <page name="uf_{0}_internal" string="Interno">
            <separator name="icms_internal_{0}" string="Internal" />
            <field name="icms_internal_{0}_ids" context="{{'tree_view_ref': 'l10n_br_fiscal.tax_definition_icms_tree', 'default_icms_regulation_id': id, 'default_tax_group_id': {2}, 'default_state_from_id': {6}}}"/>
            <separator name="icms_external_{0}" string="External" />
            <field name="icms_external_{0}_ids" context="{{'tree_view_ref': 'l10n_br_fiscal.tax_definition_icms_tree', 'default_icms_regulation_id': id, 'default_tax_group_id': {2}, 'default_state_from_id': {6}}}"/>
        </page>
        <page name="uf_{0}_st" string="ST">
            <field name="icms_st_{0}_ids" context="{{'tree_view_ref': 'l10n_br_fiscal.tax_definition_icms_tree', 'default_icms_regulation_id': id, 'default_tax_group_id': {3}, 'default_state_from_id': {6}}}"/>
        </page>
        <page name="uf_{0}_others" string="Outros">
            <group name="icms_fcp_{0}" string="FCP">
                <field name="icms_fcp_{0}_ids" nolabel="1" colspan="2" context="{{'tree_view_ref': 'l10n_br_fiscal.tax_definition_icms_tree', 'default_icms_regulation_id': id, 'default_tax_group_id': {4}, 'default_state_from_id': {6}}}"/>
            </group>
            <group name="icms_fcp_st_{0}" string="FCP-ST">
                <field name="icms_fcp_st_{0}_ids" nolabel="1" colspan="2" context="{{'tree_view_ref': 'l10n_br_fiscal.tax_definition_icms_tree', 'default_icms_regulation_id': id, 'default_tax_group_id': {5}, 'default_state_from_id': {6}}}"/>
            </group>
        </page>
        <page name="uf_{0}_benefit" string="Tax Benefit">
            <field name="tax_benefit_{0}_ids" context="{{'tree_view_ref': 'l10n_br_fiscal.tax_definition_icms_benefit_tree', 'default_icms_regulation_id': id, 'default_is_benefit': True, 'default_tax_group_id': {2}, 'default_state_from_id': {6}}}" />
        </page>
    </notebook>
</page>
"""  # noqa

# Modelos dos campos One2many replicados por estado: prefixo do campo, rótulo e
# domínio, sendo que o nome final do campo é "{prefixo}_{uf}_ids", por exemplo
# "icms_internal_sp_ids", o mesmo nome usado pelas abas criadas em
# _apply_state_tax_definition_tabs().
STATE_TAX_DEFINITION_FIELDS = (
    (
        "icms_internal",
        "ICMS Internal",
        lambda uf: [
            ("state_from_id.code", "=", uf),
            ("state_to_ids.code", "=", uf),
            ("tax_group_id.tax_domain", "=", TAX_DOMAIN_ICMS),
            ("is_benefit", "=", False),
        ],
    ),
    (
        "icms_external",
        "ICMS External",
        lambda uf: [
            ("state_from_id.code", "=", uf),
            ("state_to_ids.code", "!=", uf),
            ("tax_group_id.tax_domain", "=", TAX_DOMAIN_ICMS),
            ("is_benefit", "=", False),
        ],
    ),
    (
        "icms_st",
        "ICMS ST",
        lambda uf: [
            ("state_from_id.code", "=", uf),
            ("tax_group_id.tax_domain", "=", TAX_DOMAIN_ICMS_ST),
            ("is_benefit", "=", False),
        ],
    ),
    (
        "icms_fcp",
        "ICMS FCP",
        lambda uf: [
            ("state_from_id.code", "=", uf),
            ("tax_group_id.tax_domain", "=", TAX_DOMAIN_ICMS_FCP),
            ("is_benefit", "=", False),
        ],
    ),
    (
        "icms_fcp_st",
        "ICMS FCP ST",
        lambda uf: [
            ("state_from_id.code", "=", uf),
            ("tax_group_id.tax_domain", "=", TAX_DOMAIN_ICMS_FCP_ST),
            ("is_benefit", "=", False),
        ],
    ),
    (
        "tax_benefit",
        "Tax Benefit",
        lambda uf: [
            ("state_from_id.code", "in", (uf, False)),
            ("tax_group_id.tax_domain", "=", TAX_DOMAIN_ICMS),
            ("is_benefit", "=", True),
        ],
    ),
)


class ICMSRegulation(models.Model):
    _name = "l10n_br_fiscal.icms.regulation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Tax ICMS Regulation"

    name = fields.Char(required=True, index=True)

    icms_imported_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="ICMS Tax Imported",
        domain=[("tax_group_id.tax_domain", "=", TAX_DOMAIN_ICMS)],
    )

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == "form":
            arch = self._apply_state_tax_definition_tabs(arch)
        return arch, view

    @api.model
    def _apply_state_tax_definition_tabs(self, view_arch):
        br_states = self.env["res.country.state"].search(
            [
                ("country_id", "=", self.env.ref("base.br").id),
                ("code", "in", STATE_CODES),
            ],
            order="name",
        )
        tax_group_icms = self.env.ref("l10n_br_fiscal.tax_group_icms").id
        tax_group_icmsst = self.env.ref("l10n_br_fiscal.tax_group_icmsst").id
        tax_group_icmsfcp = self.env.ref("l10n_br_fiscal.tax_group_icmsfcp").id
        tax_group_icmsfcp_st = self.env.ref("l10n_br_fiscal.tax_group_icmsfcp_st").id

        for node in view_arch.xpath("//notebook"):
            for i, state in enumerate(br_states, start=1):
                state_page = VIEW.format(
                    state.code.lower(),
                    state.name,
                    tax_group_icms,
                    tax_group_icmsst,
                    tax_group_icmsfcp,
                    tax_group_icmsfcp_st,
                    state.id,
                )
                node_page = etree.fromstring(state_page)
                node.insert(i, node_page)

        return view_arch

    def _build_map_tax_def_domain(
        self,
        company,
        partner,
        tax_group_icms=None,
        ncm=None,
        nbm=None,
        cest=None,
        ind_final=None,
    ):
        self.ensure_one()
        domain = [
            ("icms_regulation_id", "=", self.id),
            ("state", "=", "approved"),
            ("tax_group_id", "=", tax_group_icms.id),
            "|",
            ("ind_final", "=", ind_final),
            ("ind_final", "=", False),
        ]
        domain += tools.date_validity_domain(fields.Datetime.now())

        if tax_group_icms.tax_domain in (TAX_DOMAIN_ICMS, TAX_DOMAIN_ICMS_ST):
            domain += [
                ("state_from_id", "=", company.state_id.id),
                ("state_to_ids", "=", partner.state_id.id),
            ]

        if tax_group_icms.tax_domain == TAX_DOMAIN_ICMS_ST:
            domain += [
                "|",
                ("state_to_ids", "=", partner.state_id.id),
                ("state_to_ids", "=", company.state_id.id),
                "|",
                ("ncm_ids", "=", False),
                ("ncm_ids", "=", ncm.id),
                "|",
                ("nbm_ids", "=", False),
                ("nbm_ids", "=", nbm.id),
                "|",
                ("cest_ids", "=", False),
                ("cest_ids", "=", cest.id),
            ]

        if tax_group_icms.tax_domain == TAX_DOMAIN_ICMS_FCP:
            domain += [("state_to_ids", "=", partner.state_id.id)]

        if tax_group_icms.tax_domain == TAX_DOMAIN_ICMS_FCP_ST:
            domain += [
                ("state_from_id", "=", company.state_id.id),
                ("state_to_ids", "=", partner.state_id.id),
                "|",
                ("ncm_ids", "=", False),
                ("ncm_ids", "=", ncm.id),
                "|",
                ("nbm_ids", "=", False),
                ("nbm_ids", "=", nbm.id),
                "|",
                ("cest_ids", "=", False),
                ("cest_ids", "=", cest.id),
            ]

        return domain

    def _tax_definition_search(self, domain, ncm, nbm, cest, product, ind_final=None):
        tax_definitions = self.env["l10n_br_fiscal.tax.definition"]
        icms_defs = tax_definitions.search(domain)

        if len(icms_defs) == 1:
            tax_definitions |= icms_defs
        else:
            icms_defs_benefit = icms_defs.filtered(
                lambda d: (
                    ncm.id in d.ncm_ids.ids
                    or nbm.id in d.nbm_ids.ids
                    or cest.id in d.cest_ids.ids
                    or product.id in d.product_ids.ids
                )
                and d.is_benefit
            )
            icms_defs_specific = icms_defs.filtered(
                lambda d: (
                    ncm.id in d.ncm_ids.ids
                    or nbm.id in d.nbm_ids.ids
                    or cest.id in d.cest_ids.ids
                    or product.id in d.product_ids.ids
                )
                and not d.is_benefit
            )
            icms_defs_generic = icms_defs.filtered(
                lambda d: not d.ncm_ids.ids
                and not d.nbm_ids.ids
                and not d.cest_ids.ids
                and not d.product_ids.ids
                and not d.is_benefit
            )

            if icms_defs_benefit:
                tax_definitions |= icms_defs_benefit
            else:
                if icms_defs_specific:
                    tax_definitions |= icms_defs_specific
                else:
                    tax_definitions |= icms_defs_generic

            tax_definitions_with_ind_final = tax_definitions.filtered(
                lambda d: d.ind_final == FINAL_CUSTOMER_YES
            )

            if tax_definitions_with_ind_final:
                tax_definitions = tax_definitions.filtered(
                    lambda d: ind_final == d.ind_final
                )

        return tax_definitions

    def _map_tax_def_icms(
        self,
        company,
        partner,
        product,
        ncm=None,
        nbm=None,
        cest=None,
        operation_line=None,
        ind_final=None,
    ):
        self.ensure_one()
        icms_taxes = self.env["l10n_br_fiscal.tax"]
        tax_definitions = self.env["l10n_br_fiscal.tax.definition"]
        tax_group_icms = self.env.ref("l10n_br_fiscal.tax_group_icms")

        # ICMS tax imported
        if (
            product.icms_origin in ICMS_ORIGIN_TAX_IMPORTED
            and company.state_id != partner.state_id
            and operation_line.fiscal_operation_type == FISCAL_OUT
            or operation_line.fiscal_operation_id.fiscal_type == "return_in"
            and operation_line.fiscal_operation_type == FISCAL_IN
        ):
            icms_taxes |= self.icms_imported_tax_id
        else:
            # ICMS
            domain = self._build_map_tax_def_domain(
                company, partner, tax_group_icms, ncm, nbm, cest, ind_final
            )

            tax_definitions = self._tax_definition_search(
                domain, ncm, nbm, cest, product, ind_final
            )
        return icms_taxes, tax_definitions

    def _map_tax_def_icmsst(
        self,
        company,
        partner,
        product,
        ncm=None,
        nbm=None,
        cest=None,
        operation_line=None,
        ind_final=None,
    ):
        self.ensure_one()
        tax_group_icmsst = self.env.ref("l10n_br_fiscal.tax_group_icmsst")

        # ICMS ST
        domain = self._build_map_tax_def_domain(
            company, partner, tax_group_icmsst, ncm, nbm, cest, ind_final
        )

        tax_definitions = self._tax_definition_search(
            domain, ncm, nbm, cest, product, ind_final
        )
        return tax_definitions

    def map_tax_def_icms_difal(
        self,
        company,
        partner,
        product,
        ncm=None,
        nbm=None,
        cest=None,
        operation_line=None,
        ind_final=None,
    ):
        self.ensure_one()
        tax_definitions = self.env["l10n_br_fiscal.tax.definition"]
        tax_group_icms = self.env.ref("l10n_br_fiscal.tax_group_icms")

        if (
            company.state_id != partner.state_id
            and partner.ind_ie_dest == NFE_IND_IE_DEST_9
            and operation_line.fiscal_operation_type == FISCAL_OUT
            or operation_line.fiscal_operation_id.fiscal_type != "return_in"
            and operation_line.fiscal_operation_type == FISCAL_IN
        ):
            domain = self._build_map_tax_def_domain(
                partner, partner, tax_group_icms, ncm, nbm, cest, ind_final
            )

            tax_definitions = self._tax_definition_search(
                domain, ncm, nbm, cest, product, ind_final
            )
        return tax_definitions.mapped("tax_id"), tax_definitions

    def _map_tax_def_icmsfcp(
        self,
        company,
        partner,
        product,
        ncm=None,
        nbm=None,
        cest=None,
        operation_line=None,
        ind_final=None,
    ):
        self.ensure_one()
        tax_definitions = self.env["l10n_br_fiscal.tax.definition"]
        tax_group_icmsfcp = self.env.ref("l10n_br_fiscal.tax_group_icmsfcp")

        # ICMS FCP for DIFAL
        if (
            company.state_id != partner.state_id
            and partner.ind_ie_dest == NFE_IND_IE_DEST_9
            and operation_line.fiscal_operation_type == FISCAL_OUT
            or operation_line.fiscal_operation_id.fiscal_type == "return_in"
            and operation_line.fiscal_operation_type == FISCAL_IN
        ):
            domain = self._build_map_tax_def_domain(
                partner, partner, tax_group_icmsfcp, ncm, nbm, cest, ind_final
            )

            tax_definitions = self._tax_definition_search(
                domain, ncm, nbm, cest, product, ind_final
            )

        return tax_definitions

    def _map_tax_def_icmsfcpst(
        self,
        company,
        partner,
        product,
        ncm=None,
        nbm=None,
        cest=None,
        operation_line=None,
        ind_final=None,
    ):
        self.ensure_one()
        tax_definitions = self.env["l10n_br_fiscal.tax.definition"]
        tax_group_icmsfcpst = self.env.ref("l10n_br_fiscal.tax_group_icmsfcp_st")

        # FCP ST
        domain = self._build_map_tax_def_domain(
            company, partner, tax_group_icmsfcpst, ncm, nbm, cest, ind_final
        )

        tax_definitions = self._tax_definition_search(
            domain, ncm, nbm, cest, product, ind_final
        )

        return tax_definitions

    # TODO adicionar o argumento CFOP????
    def map_tax(
        self,
        company,
        partner,
        product,
        ncm=None,
        nbm=None,
        cest=None,
        operation_line=None,
        ind_final=None,
    ):
        if product:
            if not ncm:
                ncm = product.ncm_id

            if not nbm:
                nbm = product.nbm_id

            if not cest:
                cest = product.cest_id

        icms_taxes, icms_def_taxes = self._map_tax_def_icms(
            company, partner, product, ncm, nbm, cest, operation_line, ind_final
        )

        icms_def_taxes |= self._map_tax_def_icmsst(
            company, partner, product, ncm, nbm, cest, operation_line, ind_final
        )

        icms_def_taxes |= self._map_tax_def_icmsfcp(
            company, partner, product, ncm, nbm, cest, operation_line, ind_final
        )

        icms_def_taxes |= self._map_tax_def_icmsfcpst(
            company, partner, product, ncm, nbm, cest, operation_line, ind_final
        )

        icms_taxes |= icms_def_taxes.mapped("tax_id")

        return icms_taxes, icms_def_taxes


def _add_state_tax_definition_fields(model_cls):
    """Declara os campos de definição fiscal de ICMS por estado.

    São 162 campos One2many (27 estados x 6 definições) que só diferem pelo
    código da UF, então são criados aqui ao invés de serem escritos um a um.
    Os campos são registrados da mesma forma que os campos escritos no corpo
    da classe (ver odoo.models.MetaModel.__init__), portanto podem ser
    herdados e sobrescritos normalmente por outros módulos.
    """
    for uf in STATE_CODES:
        for prefix, string, build_domain in STATE_TAX_DEFINITION_FIELDS:
            name = f"{prefix}_{uf.lower()}_ids"
            field = fields.One2many(
                comodel_name="l10n_br_fiscal.tax.definition",
                inverse_name="icms_regulation_id",
                string=f"{string} {uf}",
                domain=build_domain(uf),
            )
            setattr(model_cls, name, field)
            field.__set_name__(model_cls, name)


_add_state_tax_definition_fields(ICMSRegulation)
