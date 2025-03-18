# Copyright (C) 2013  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from lxml import etree

from odoo import api, fields, models

from ..constants.fiscal import (
    NCM_FOR_SERVICE_REF,
    PRODUCT_FISCAL_TYPE,
    PRODUCT_FISCAL_TYPE_SERVICE,
    TAX_DOMAIN_ICMS,
    TAX_ICMS_OR_ISSQN,
)
from ..constants.icms import ICMS_ORIGIN, ICMS_ORIGIN_DEFAULT


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["product.template", "l10n_br_fiscal.product.mixin"]

    def _get_default_ncm_id(self):
        fiscal_type = self.env.context.get("default_fiscal_type")
        if fiscal_type == PRODUCT_FISCAL_TYPE_SERVICE:
            return self.env.ref(NCM_FOR_SERVICE_REF)

    # Some modules of the repo depend on stock and have
    # demo products of type 'product' (this type is added to product.template
    # in the stock module).
    # For some reason when running the tests, some inverse method fields then fail when
    # reading 'product' value for the product type. It seems it is because
    # l10n_br_fiscal doesn't depend on stock. But we don't want such a dependency.
    # So a workaround to avoid the bug we add the 'product' value to the selection.
    type = fields.Selection(
        selection_add=[("product", "Storable Product")],
        ondelete={"product": "set default"},
    )

    fiscal_type = fields.Selection(
        selection=PRODUCT_FISCAL_TYPE,
        company_dependent=True,
    )

    icms_origin = fields.Selection(
        selection=ICMS_ORIGIN,
        string="ICMS Origin",
        company_dependent=True,
        default=ICMS_ORIGIN_DEFAULT,
    )

    ncm_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.ncm",
        index=True,
        default=_get_default_ncm_id,
        string="NCM",
    )

    nbm_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.nbm", index=True, string="NBM"
    )

    tax_icms_or_issqn = fields.Selection(
        selection=TAX_ICMS_OR_ISSQN,
        string="ICMS or ISSQN Tax",
        default=TAX_DOMAIN_ICMS,
    )

    fiscal_genre_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.product.genre", string="Fiscal Product Genre"
    )

    service_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.service.type",
        string="Service Type LC 166",
        domain="[('internal_type', '=', 'normal')]",
    )

    city_taxation_code_id = fields.Many2many(
        comodel_name="l10n_br_fiscal.city.taxation.code", string="City Taxation Code"
    )

    fiscal_genre_code = fields.Char(
        related="fiscal_genre_id.code", store=True, string="Fiscal Product Genre Code"
    )

    ipi_guideline_class_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.ipi.guideline.class",
        string="IPI Guideline Class",
    )

    ipi_control_seal_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.ipi.control.seal", string="IPI Control Seal"
    )

    nbs_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.nbs", index=True, string="NBS"
    )

    cest_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cest",
        index=True,
        string="CEST",
        domain="[('ncm_ids', '=', ncm_id)]",
    )

    uoe_id = fields.Many2one(
        comodel_name="uom.uom", related="ncm_id.uoe_id", store=True, string="Export UoM"
    )

    uoe_factor = fields.Float(string="Export UoM Factor", default=1.00)

    uot_id = fields.Many2one(comodel_name="uom.uom", string="Tax UoM")

    uot_factor = fields.Float(string="Tax UoM Factor")

    tax_definition_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax.definition",
        relation="tax_definition_product_rel",
        column1="product_id",
        column2="tax_definition_id",
        readonly=True,
        string="Tax Definition",
    )

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        """Modifica a view para adicionar seller_ids e variant_seller_ids apenas se o
        módulo purchase NÃO estiver instalado."""

        # Verifica se o módulo purchase está instalado
        purchase_installed = (
            self.env["ir.module.module"]
            .sudo()
            .search_count([("name", "=", "purchase"), ("state", "=", "installed")])
            > 0
        )

        # Obtém a visão original
        res = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )

        if not purchase_installed and view_type == "form":
            # Converte a string XML para um objeto manipulável
            doc = etree.fromstring(res["arch"])

            # Localiza a aba "Purchase"
            purchase_page = doc.xpath("//page[@name='purchase']")
            if purchase_page:
                purchase_page = purchase_page[0]

                # Criar um grupo para os campos antes do grupo "purchase"
                purchase_group = purchase_page.xpath(".//group[@name='purchase']")
                if purchase_group:
                    purchase_group = purchase_group[0]

                    # Criar novo grupo antes do existente
                    new_group = etree.Element("group")

                    # Criar os campos com os atributos dinâmicos
                    field_seller_ids = etree.Element(
                        "field",
                        name="seller_ids",
                        attrib={
                            "context": """{
                                'default_product_tmpl_id': context.get(
                                    'product_tmpl_id', active_id
                                ),
                                'product_template_invisible_variant': True,
                                'tree_view_ref':'purchase.product_supplierinfo_tree_view2'
                                }""",
                            "nolabel": "1",
                        },
                    )

                    # Adicionar os campos ao novo grupo
                    new_group.append(field_seller_ids)

                    # Inserir o novo grupo antes do grupo "purchase"
                    purchase_group.addprevious(new_group)

                    # Atualiza a visão
                    res["arch"] = etree.tostring(doc, encoding="unicode")

        return res
