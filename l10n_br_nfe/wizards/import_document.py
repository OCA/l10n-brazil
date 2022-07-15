# Copyright (C) 2021  Gabriel Cardoso de Faria - Kmee
# Copyright (C) 2022  Renan Hiroki Bastos - Kmee
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64

from erpbrasil.base.fiscal.edoc import detectar_chave_edoc

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import FISCAL_IN_OUT_ALL
from odoo.addons.l10n_br_nfe.models.document import parse_xml_nfe

IMPORTING_TYPES = [
    ("xml_file", "NFe XML File"),
    ("nfe_key", "NFe key (Not Implemented)"),
    ("manually", "Manually (Not Implemented)"),
]


class NfeImport(models.TransientModel):
    """Importar XML Nota Fiscal Eletrônica"""

    _name = "l10n_br_nfe.import_xml"
    _inherit = "l10n_br_fiscal.base.wizard.mixin"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.user.company_id,
    )

    importing_type = fields.Selection(
        string="Importing Type", selection=IMPORTING_TYPES, required=True
    )

    nfe_xml = fields.Binary(
        string="NFe XML to Import",
    )

    fiscal_operation_type = fields.Selection(
        string="Fiscal Operation Type", selection=FISCAL_IN_OUT_ALL
    )

    partner_cpf_cnpj = fields.Char(string="Partner Documentation")

    partner_name = fields.Char(string="Partner Name")

    imported_products_ids = fields.One2many(
        string="Imported Products",
        comodel_name="l10n_br_nfe.import_xml.products",
        inverse_name="import_xml_id",
    )

    def _parse_xml_import_wizard(self, xml):
        parsed_xml = parse_xml_nfe(xml)
        document = detectar_chave_edoc(parsed_xml.infNFe.Id[3:])

        return parsed_xml, document

    @api.onchange("nfe_xml")
    def _onchange_partner_id(self):
        if self.nfe_xml:
            parsed_xml, document = self._parse_xml_import_wizard(
                base64.b64decode(self.nfe_xml)
            )

            nfe_model_code = self.env.ref("l10n_br_fiscal.document_55").code

            if document.modelo_documento != nfe_model_code:
                raise UserError(
                    _(
                        f"Incorrect fiscal document model! "
                        f"Accepted one is {nfe_model_code}"
                    )
                )

            self.document_key = document.chave
            self.document_number = int(document.numero_documento)
            self.document_serie = int(document.numero_serie)
            self.partner_cpf_cnpj = document.cnpj_emitente
            self.partner_name = (
                parsed_xml.infNFe.emit.xFant or parsed_xml.infNFe.emit.xNome
            )
            self.partner_id = self.env["res.partner"].search(
                [
                    "|",
                    ("cnpj_cpf", "=", document.cnpj_emitente),
                    ("nfe40_xNome", "=", parsed_xml.infNFe.emit.xNome),
                ],
                limit=1,
            )
            self._check_nfe_xml_products(parsed_xml)

    def _check_nfe_xml_products(self, parsed_xml):
        product_ids = []
        for product in parsed_xml.infNFe.det:
            product_ids.append(
                self.env["l10n_br_nfe.import_xml.products"]
                .create(
                    {
                        "product_name": product.prod.xProd,
                        "uom_com": product.prod.uCom,
                        "quantity_com": product.prod.qCom,
                        "price_unit_com": product.prod.vUnCom,
                        "uom_trib": product.prod.uTrib,
                        "quantity_trib": product.prod.qTrib,
                        "price_unit_trib": product.prod.vUnTrib,
                        "total": product.prod.vProd,
                        "import_xml_id": self.id,
                    }
                )
                .id
            )
        if product_ids:
            self.imported_products_ids = [(6, 0, product_ids)]

    @api.multi
    def import_nfe_xml(self):

        parsed_xml, document = self._parse_xml_import_wizard(
            base64.b64decode(self.nfe_xml)
        )

        self.fiscal_operation_type = (
            "in" if document.cnpj_emitente != self.company_id.cnpj_cpf else "out"
        )

        edoc = self.env["l10n_br_fiscal.document"].import_xml(
            parsed_xml,
            dry_run=False,
            edoc_type=self.fiscal_operation_type,
        )

        self._set_partner_as_supplier(edoc)
        self._attach_original_nfe_xml_to_document(edoc)

        return {
            "name": _("Documento Importado"),
            "type": "ir.actions.act_window",
            "target": "current",
            "views": [[False, "form"]],
            "res_id": edoc.id,
            "res_model": "l10n_br_fiscal.document",
        }

    def _set_partner_as_supplier(self, edoc):
        edoc.partner_id.supplier = True

    def _attach_original_nfe_xml_to_document(self, edoc):
        vals = {
            "name": "NFe-Importada-{}.xml".format(edoc.document_key),
            "datas": base64.b64decode(self.nfe_xml),
            "datas_fname": "NFe-Importada-{}.xml".format(edoc.document_key),
            "description": "XML NFe - Importada por XML",
            "res_model": "l10n_br_fiscal.document",
            "res_id": edoc.id,
        }
        self.env["ir.attachment"].create(vals)


class NfeImportProducts(models.TransientModel):
    _name = "l10n_br_nfe.import_xml.products"

    product_name = fields.Char(string="Product Name")

    uom_com = fields.Char(string="UOM Comercial")

    quantity_com = fields.Float(string="Comercial Quantity")

    price_unit_com = fields.Float(string="Comercial Price Unit")

    uom_trib = fields.Char(string="UOM Fiscal")

    quantity_trib = fields.Float(string="Fiscal Quantity")

    price_unit_trib = fields.Float(string="Fiscal Price Unit")

    total = fields.Float(string="Total")

    import_xml_id = fields.Many2one(comodel_name="l10n_br_nfe.import_xml")
