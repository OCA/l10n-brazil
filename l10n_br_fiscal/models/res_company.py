# Copyright (C) 2013  Renato Lima - Akretion
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# Copyright (C) 2023  Antônio S. Pereira Neto - Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from markupsafe import Markup

from odoo import _, api, fields, models

from ..constants.fiscal import (
    CFOP_INDUSTRIALIZATION_FOR_THIRD_PARTY,
    COEFFICIENT_R,
    INDUSTRY_TYPE,
    INDUSTRY_TYPE_TRANSFORMATION,
    PROCESSADOR,
    PROCESSADOR_NENHUM,
    PROFIT_CALCULATION,
    PROFIT_CALCULATION_PRESUMED,
    SIMPLIFIED_TAX_ANNEX_COMMERCE,
    SIMPLIFIED_TAX_ANNEX_INDUSTRY,
    TAX_DOMAIN_CBS,
    TAX_DOMAIN_COFINS,
    TAX_DOMAIN_COFINS_WH,
    TAX_DOMAIN_CSLL,
    TAX_DOMAIN_CSLL_WH,
    TAX_DOMAIN_IBS,
    TAX_DOMAIN_ICMS,
    TAX_DOMAIN_ICMS_SN,
    TAX_DOMAIN_INSS,
    TAX_DOMAIN_INSS_WH,
    TAX_DOMAIN_IPI,
    TAX_DOMAIN_IRPJ,
    TAX_DOMAIN_IRPJ_WH,
    TAX_DOMAIN_ISSQN,
    TAX_DOMAIN_ISSQN_WH,
    TAX_DOMAIN_PIS,
    TAX_DOMAIN_PIS_WH,
    TAX_FRAMEWORK,
    TAX_FRAMEWORK_NORMAL,
    TAX_FRAMEWORK_SIMPLES,
    TAX_FRAMEWORK_SIMPLES_ALL,
)

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    simplified_tax_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.simplified.tax",
        string="Effective Taxes",
        help="Simples Nacional effective tax rate for each annex, "
        "based on the range the company currently falls into.",
        compute="_compute_simplified_tax_ids",
    )

    def _get_company_address_field_names(self):
        partner_fields = super()._get_company_address_field_names()
        return partner_fields + [
            "legal_nature_id",
            "cnae_main_id",
        ]

    def _inverse_legal_nature_id(self):
        """Write the l10n_br specific functional fields."""
        for c in self:
            c.partner_id.legal_nature_id = c.legal_nature_id

    def _inverse_cnae_main_id(self):
        """Write the l10n_br specific functional fields."""
        for c in self:
            c.partner_id.cnae_main_id = c.cnae_main_id

    @api.depends("partner_id", "partner_id.tax_framework")
    def _compute_tax_framework(self):
        for c in self:
            c.tax_framework = c.partner_id.tax_framework

    def _inverse_tax_framework(self):
        """Write the l10n_br specific functional fields."""
        for c in self:
            c.partner_id.tax_framework = c.tax_framework

    legal_nature_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.legal.nature",
        string="Legal Nature",
        compute="_compute_address",
        inverse="_inverse_legal_nature_id",
    )

    cnae_main_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cnae",
        compute="_compute_address",
        inverse="_inverse_cnae_main_id",
        domain="[('internal_type', '=', 'normal'), "
        "('id', 'not in', cnae_secondary_ids)]",
        string="Main CNAE",
    )

    cnae_secondary_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.cnae",
        domain="[('internal_type', '=', 'normal'), " "('id', '!=', cnae_main_id)]",
        string="Secondary CNAE",
    )

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        default=TAX_FRAMEWORK_NORMAL,
        compute="_compute_tax_framework",
        inverse="_inverse_tax_framework",
        store=True,
    )

    profit_calculation = fields.Selection(
        selection=PROFIT_CALCULATION,
        default=PROFIT_CALCULATION_PRESUMED,
    )

    is_industry = fields.Boolean(
        help="If your company is industry or ......",
        default=False,
    )

    industry_type = fields.Selection(
        selection=INDUSTRY_TYPE,
        default=INDUSTRY_TYPE_TRANSFORMATION,
    )

    annual_revenue = fields.Monetary(
        currency_field="currency_id",
        help="Gross revenue accumulated over the 12 months before the current "
        "assessment period (RBT12). Under the Simples Nacional it sets the range "
        "of each annex, hence the effective tax rates and the ICMS credit rate "
        "stated on the invoices, which is the one of the range the company was "
        "in the month before the operation (LC 123/2006, art. 18 and art. 23).",
    )

    payroll_amount = fields.Monetary(
        string="Last Period Payroll Amount",
        currency_field="currency_id",
    )

    simplified_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.simplified.tax",
        string="Main Activity Annex",
        help="Annex of the Simples Nacional of the main activity of the company, "
        "found from its main CNAE and, for the services the R factor moves "
        "between the Annex III and the Annex V, from its R factor. It applies to "
        "the operations whose CFOP does not tell their annex, such as services.",
        compute="_compute_simplified_tax",
        store=True,
        readonly=True,
    )

    simplified_tax_range_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.simplified.tax.range",
        string="Main Activity Range",
        help="Range of the annex of the main activity the company currently "
        "falls into, given its gross revenue of the last 12 months.",
        compute="_compute_simplified_tax",
        store=True,
        readonly=True,
    )

    coefficient_r = fields.Boolean(
        compute="_compute_simplified_tax",
        store=True,
        readonly=True,
    )

    coefficient_r_percent = fields.Float(
        compute="_compute_simplified_tax",
        string="Coefficient R (%)",
        store=True,
        readonly=True,
    )

    ibpt_api = fields.Boolean(string="Use IBPT API", default=False)

    ibpt_token = fields.Char()

    ibpt_update_days = fields.Integer(string="IBPT Token Updates", default=15)

    accountant_id = fields.Many2one(comodel_name="res.partner", string="Accountant")

    accounting_office = fields.Many2one(comodel_name="res.partner")

    technical_support_id = fields.Many2one(
        comodel_name="res.partner", string="Technical Support"
    )

    piscofins_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.pis.cofins",
        string="PIS/COFINS",
        domain="[('piscofins_type', '=', 'company')]",
    )

    tax_cofins_wh_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Default COFINS RET",
        domain=[("tax_domain", "=", TAX_DOMAIN_COFINS_WH)],
    )

    tax_pis_wh_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Default PIS RET",
        domain=[("tax_domain", "=", TAX_DOMAIN_PIS_WH)],
    )

    tax_csll_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Default CSLL",
        domain=[("tax_domain", "=", TAX_DOMAIN_CSLL)],
    )

    tax_csll_wh_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Default CSLL RET",
        domain=[("tax_domain", "=", TAX_DOMAIN_CSLL_WH)],
    )

    ripi = fields.Boolean(string="RIPI")

    tax_ipi_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Default IPI",
        domain=[("tax_domain", "=", TAX_DOMAIN_IPI)],
    )

    tax_icms_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Default ICMS",
        domain=[("tax_domain", "in", (TAX_DOMAIN_ICMS, TAX_DOMAIN_ICMS_SN))],
    )

    icms_regulation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.icms.regulation", string="ICMS Regulation"
    )

    tax_issqn_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Default ISSQN",
        domain=[("tax_domain", "=", TAX_DOMAIN_ISSQN)],
    )

    tax_issqn_wh_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Default ISSQN RET",
        domain=[("tax_domain", "=", TAX_DOMAIN_ISSQN_WH)],
    )

    tax_irpj_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Default IRPJ",
        domain=[("tax_domain", "=", TAX_DOMAIN_IRPJ)],
    )

    tax_irpj_wh_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Default IRPJ RET",
        domain=[("tax_domain", "=", TAX_DOMAIN_IRPJ_WH)],
    )

    tax_inss_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Default INSS",
        domain=[("tax_domain", "=", TAX_DOMAIN_INSS)],
    )

    tax_inss_wh_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Default INSS RET",
        domain=[("tax_domain", "=", TAX_DOMAIN_INSS_WH)],
    )

    tax_classification_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.classification",
        string="Default Tax Classification",
        domain=[("tax_ibs_id", "!=", False), ("tax_cbs_id", "!=", False)],
    )

    tax_definition_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.tax.definition",
        inverse_name="company_id",
        string="Tax Definition",
    )

    processador_edoc = fields.Selection(
        selection=PROCESSADOR,
        string="Processador documentos eletrônicos",
        default=PROCESSADOR_NENHUM,
    )

    document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type", string="Default Document Type"
    )

    document_save_disk = fields.Boolean(
        string="Save Documents to disk",
        default=True,
    )

    delivery_costs = fields.Selection(
        selection=[("line", "By Line"), ("total", "By Total")],
        help="Define if costs of Insurance, Freight and Other Costs"
        " should be informed by Line or by Total.",
        default="line",
    )

    @api.onchange("profit_calculation", "tax_framework")
    def _onchange_profit_calculation(self):
        # Only the default taxes of the company are set here (virtual values).
        # The company tax definitions are reconciled when the company is
        # saved, see _sync_tax_definitions.

        # Get all Simples Nacional default taxes
        sn_piscofins_id = self.env.ref("l10n_br_fiscal.tax_pis_cofins_simples_nacional")

        sn_tax_icms_id = self.env.ref("l10n_br_fiscal.tax_icms_sn_com_credito")

        # If Tax Framework is Simples Nacional
        if self.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
            # Set taxes
            self.piscofins_id = sn_piscofins_id
            self.tax_icms_id = sn_tax_icms_id

        # If Tax Framework is Regine Normal
        if self.tax_framework == TAX_FRAMEWORK_NORMAL:
            pis_cofins_refs = {
                "real": self.env.ref("l10n_br_fiscal.tax_pis_cofins_nao_columativo"),
                "presumed": self.env.ref("l10n_br_fiscal.tax_pis_cofins_columativo"),
                "arbitrary": self.env.ref("l10n_br_fiscal.tax_pis_cofins_columativo"),
            }

            self.piscofins_id = pis_cofins_refs.get(self.profit_calculation)
            self.tax_icms_id = False

        self._onchange_ripi()

    @api.onchange("is_industry")
    def _onchange_is_industry(self):
        if self.is_industry and self.tax_framework == TAX_FRAMEWORK_SIMPLES:
            self.ripi = True
        else:
            self.ripi = False

    @api.onchange("ripi")
    def _onchange_ripi(self):
        if not self.ripi and self.tax_framework == TAX_FRAMEWORK_NORMAL:
            self.tax_ipi_id = self.env.ref("l10n_br_fiscal.tax_ipi_nt")
        elif self.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
            self.tax_ipi_id = self.env.ref("l10n_br_fiscal.tax_ipi_outros")
            self.ripi = False
        else:
            self.tax_ipi_id = False

    def _get_tax_definition_fields(self):
        """Default taxes of the company and the tax domains of the company tax
        definitions that follow each one of them."""
        return {
            "piscofins_id": (TAX_DOMAIN_PIS, TAX_DOMAIN_COFINS),
            "tax_pis_wh_id": (TAX_DOMAIN_PIS_WH,),
            "tax_cofins_wh_id": (TAX_DOMAIN_COFINS_WH,),
            "tax_csll_id": (TAX_DOMAIN_CSLL,),
            "tax_csll_wh_id": (TAX_DOMAIN_CSLL_WH,),
            "tax_ipi_id": (TAX_DOMAIN_IPI,),
            "tax_icms_id": (TAX_DOMAIN_ICMS, TAX_DOMAIN_ICMS_SN),
            "tax_issqn_id": (TAX_DOMAIN_ISSQN,),
            "tax_issqn_wh_id": (TAX_DOMAIN_ISSQN_WH,),
            "tax_irpj_id": (TAX_DOMAIN_IRPJ,),
            "tax_irpj_wh_id": (TAX_DOMAIN_IRPJ_WH,),
            "tax_inss_id": (TAX_DOMAIN_INSS,),
            "tax_inss_wh_id": (TAX_DOMAIN_INSS_WH,),
            "tax_classification_id": (TAX_DOMAIN_CBS, TAX_DOMAIN_IBS),
        }

    def _get_tax_definition_targets(self, field_names):
        """Return the tax that each tax domain must have, according to the
        default taxes of the company. An empty recordset means that the company
        must not have a tax definition in that domain."""
        self.ensure_one()
        tax_model = self.env["l10n_br_fiscal.tax"]
        domains_by_field = self._get_tax_definition_fields()
        targets = {}
        for field_name in field_names:
            for tax_domain in domains_by_field[field_name]:
                targets[tax_domain] = tax_model
            value = self[field_name]
            if field_name == "piscofins_id":
                taxes = value.tax_pis_id | value.tax_cofins_id
            elif field_name == "tax_classification_id":
                taxes = value.tax_cbs_id | value.tax_ibs_id
            else:
                taxes = value
            for tax in taxes:
                targets[tax.tax_domain] = tax
        return targets

    def _sync_tax_definitions(self, field_names):
        """Make the company tax definitions follow the default taxes.

        A definition that does not match the new default tax is not deleted:
        it is expired, with the end of its validity, so the history of what
        was taxed before stays available. The new definition starts when the
        company is saved.
        """
        definition_model = self.env["l10n_br_fiscal.tax.definition"]
        now = fields.Datetime.now()
        for company in self:
            current = definition_model.search(
                [("company_id", "=", company.id), ("state", "!=", "expired")]
            )
            targets = company._get_tax_definition_targets(field_names)
            for tax_domain, tax in targets.items():
                definitions = current.filtered(
                    lambda d, tax_domain=tax_domain: d.tax_group_id.tax_domain
                    == tax_domain
                )
                outdated = definitions.filtered(lambda d, tax=tax: d.tax_id != tax)
                outdated.write({"state": "expired", "date_end": now})
                if tax and not definitions - outdated:
                    definition_model.create(
                        {
                            "type_in_out": "out",
                            "tax_group_id": tax.tax_group_id.id,
                            "is_taxed": True,
                            "is_debit_credit": True,
                            "custom_tax": True,
                            "tax_id": tax.id,
                            "cst_id": tax.cst_out_id.id,
                            "company_id": company.id,
                            "date_start": now,
                        }
                    )

    def _get_tax_regime_snapshot(self):
        """Tax regime and active tax definitions of the company, to audit what
        changed when the tax regime is changed."""
        self.ensure_one()
        definitions = self.env["l10n_br_fiscal.tax.definition"].search(
            [("company_id", "=", self.id), ("state", "!=", "expired")]
        )
        framework = dict(self._fields["tax_framework"]._description_selection(self.env))
        profit = dict(
            self._fields["profit_calculation"]._description_selection(self.env)
        )
        regime = framework.get(self.tax_framework) or ""
        if self.tax_framework == TAX_FRAMEWORK_NORMAL:
            regime = f"{regime} / {profit.get(self.profit_calculation)}"
        return {
            "regime": regime,
            "definitions": sorted(
                f"{d.tax_group_id.name}: {d.tax_id.name} ({d.tax_id.percent_amount:g}%)"
                for d in definitions
            ),
        }

    def _post_tax_regime_change(self, before, after, date_end):
        """Register in the chatter what was taxed before and what is taxed
        after a change of the tax regime. The company has no chatter, so the
        message goes to the partner of the company."""
        self.ensure_one()
        if before == after:
            return

        def _items(lines):
            return Markup("").join(
                Markup("<li>%s</li>") % line for line in lines
            ) or Markup("<li>-</li>")

        body = Markup(
            "<p><b>%(title)s</b> (%(date)s)</p>"
            "<p>%(before_label)s: %(before_regime)s</p><ul>%(before)s</ul>"
            "<p>%(after_label)s: %(after_regime)s</p><ul>%(after)s</ul>"
            "<p>%(note)s</p>"
        ) % {
            "title": _("Tax regime changed"),
            "date": date_end,
            "before_label": _("Before"),
            "before_regime": before["regime"],
            "before": _items(before["definitions"]),
            "after_label": _("After"),
            "after_regime": after["regime"],
            "after": _items(after["definitions"]),
            "note": _(
                "The tax definitions of the previous regime were kept as "
                "Expired, with the end of their validity."
            ),
        }
        self.partner_id.sudo().message_post(body=body, subtype_xmlid="mail.mt_note")

    def write(self, vals):
        tax_fields = self._get_tax_definition_fields()
        sync_fields = [f for f in tax_fields if f in vals]
        regime_fields = {"tax_framework", "profit_calculation"}
        if self.env.context.get("install_mode") or not (
            sync_fields or regime_fields & vals.keys()
        ):
            return super().write(vals)
        snapshots = {c.id: c._get_tax_regime_snapshot() for c in self}
        result = super().write(vals)
        now = fields.Datetime.now()
        for company in self:
            company._sync_tax_definitions(sync_fields)
            company._post_tax_regime_change(
                snapshots[company.id], company._get_tax_regime_snapshot(), now
            )
        return result

    @api.depends("annual_revenue", "payroll_amount", "partner_id.cnae_main_id")
    def _compute_simplified_tax(self):
        for record in self:
            record._calculate_coefficient_r()
            annex = record._get_main_activity_simplified_tax()
            record.simplified_tax_id = annex
            record.simplified_tax_range_id = annex._get_range(record.annual_revenue)

    def _compute_simplified_tax_ids(self):
        annexes = self.env["l10n_br_fiscal.simplified.tax"].search([])
        for record in self:
            record.simplified_tax_ids = annexes

    def _get_main_activity_simplified_tax(self):
        """Return the annex of the Simples Nacional of the main activity of the
        company, found from its main CNAE.

        The CNAE is read on the partner of the company: the cnae_main_id of
        the company mirrors it through the address computation of the core,
        which declares no dependency, so its cached value may be stale.

        The CNAEs of the services the R factor moves between the Annex III and
        the Annex V (LC 123/2006, art. 18, § 5º-J and § 5º-M) belong to both
        annexes, and the R factor of the company tells which one applies. A
        CNAE listed in two annexes the R factor does not tell apart gets the
        first one.
        """
        self.ensure_one()
        annexes = self.env["l10n_br_fiscal.simplified.tax"]
        cnae = self.partner_id.cnae_main_id
        if cnae:
            annexes = annexes.search([("cnae_ids", "=", cnae.id)])
        if len(annexes) > 1:
            annexes = (
                annexes.filtered(lambda a: a.coefficient_r == self.coefficient_r)
                or annexes
            )
        return annexes[:1]

    def _get_simplified_tax(self, cfop):
        """Return the annex of the Simples Nacional that taxes an operation
        with the given CFOP.

        Resale is taxed by the Annex I and the goods industrialized by the
        company by the Annex II (LC 123/2006, art. 18, § 4º, I and II), which
        includes the industrialization ordered by a third party. When the CFOP
        tells neither (e.g. 5910, 5949) or there is none, as for services, the
        annex of the main activity of the company applies, and failing that the
        Annex II for an industry or the Annex I otherwise.
        """
        self.ensure_one()
        type_move = cfop.type_move if cfop else False
        code = cfop.code if cfop else False
        if type_move == "sale_commerce":
            xmlid = SIMPLIFIED_TAX_ANNEX_COMMERCE
        elif (
            type_move == "sale_industry"
            or code in CFOP_INDUSTRIALIZATION_FOR_THIRD_PARTY
        ):
            xmlid = SIMPLIFIED_TAX_ANNEX_INDUSTRY
        elif self.simplified_tax_id:
            return self.simplified_tax_id
        elif self.is_industry:
            xmlid = SIMPLIFIED_TAX_ANNEX_INDUSTRY
        else:
            xmlid = SIMPLIFIED_TAX_ANNEX_COMMERCE
        return (
            self.env.ref(xmlid, raise_if_not_found=False)
            or self.env["l10n_br_fiscal.simplified.tax"]
        )

    def _get_simplified_tax_range(self, cfop):
        """Return the range the company currently falls into, in the annex of
        the Simples Nacional that taxes an operation with the given CFOP.
        There is none without a company, as for a line whose company is not
        set yet, nor for a company outside the Simples Nacional, the MEI and
        the company above the sublimit included, which grant no ICMS credit
        of the Simples Nacional (LC 123/2006, art. 23, § 4º, I)."""
        if len(self) != 1 or self.tax_framework != TAX_FRAMEWORK_SIMPLES:
            return self.env["l10n_br_fiscal.simplified.tax.range"]
        return self._get_simplified_tax(cfop)._get_range(self.annual_revenue)

    def _calculate_coefficient_r(self):
        """R factor: payroll over gross revenue of the last 12 months. From
        28% on, the services of the LC 123/2006, art. 18, § 5º-I are taxed by
        the Annex III instead of the Annex V (§ 5º-J)."""
        for record in self:
            coefficient_r_percent = 0.0
            if record.payroll_amount and record.annual_revenue:
                coefficient_r_percent = record.payroll_amount / record.annual_revenue
            record.coefficient_r_percent = coefficient_r_percent
            record.coefficient_r = coefficient_r_percent >= COEFFICIENT_R
