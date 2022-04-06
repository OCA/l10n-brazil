# Copyright (C) 2021  Gabriel Cardoso de Faria - Kmee
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
    """ Importar XML Nota Fiscal Eletrônica """

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

            # Validação comentada para realização de testes
            # TODO: Descomentar essa validação
            # if self.env['l10n_br_fiscal.document'].search(
            # [('document_key', '=', parsed_xml.infNFe.Id.replace('NFe', ''))]
            # ):
            #     raise UserError(_("Esta nota fiscal já foi importada.\nChave: {}"
            #     .format(parsed_xml.infNFe.Id.replace('NFe', ''))))

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
                [("cnpj_cpf", "=", document.cnpj_emitente)]
            )

            self._check_nfe_xml_products(parsed_xml)
            if self.partner_id:
                self.get_partner_product_relation()

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

    def _check_ncm_nbm_cest(self, nfe_product, wizard_product):
        if (
            wizard_product.ncm_id
            and hasattr(nfe_product, "NCM")
            and nfe_product.NCM
            and nfe_product.NCM != wizard_product.ncm_id.code.replace(".", "")
        ):
            raise UserError(
                _(
                    """O NCM do produto {} no cadastro interno é diferente do NCM
                     na nota.\nNCM interno: {}\nNCM na nota: {}""".format(
                        wizard_product.display_name,
                        wizard_product.ncm_id.code,
                        nfe_product.NCM,
                    )
                )
            )
        if (
            wizard_product.nbm_id
            and hasattr(nfe_product, "NBM")
            and nfe_product.NBM
            and nfe_product.NBM != wizard_product.ncm_id.replace(".", "")
        ):
            raise UserError(
                _(
                    """O NBM do produto {} no cadastro interno é diferente do NBM
                     na nota.\nNBM interno: {}\nNBM na nota: {}""".format(
                        wizard_product.display_name,
                        wizard_product.nbm_id.code,
                        nfe_product.NBM,
                    )
                )
            )
        if (
            wizard_product.cest_id
            and hasattr(nfe_product, "CEST")
            and nfe_product.CEST
            and nfe_product.CEST != wizard_product.cest_id.replace(".", "")
        ):
            raise UserError(
                _(
                    """O Cest do produto {} no cadastro interno é diferente do Cest
                     na nota.\nCest interno: {}\nCest na nota: {}""".format(
                        wizard_product.display_name,
                        wizard_product.cest_id.code,
                        nfe_product.CEST,
                    )
                )
            )

    @api.multi
    def import_nfe_xml(self):

        parsed_xml, document = self._parse_xml_import_wizard(
            base64.b64decode(self.nfe_xml)
        )

        parsed_xml = self.edit_parsed_xml(parsed_xml)

        self.fiscal_operation_type = (
            "in" if document.cnpj_emitente != self.company_id.cnpj_cpf else "out"
        )

        edoc = self.env["l10n_br_fiscal.document"].import_xml(
            parsed_xml,
            dry_run=False,
            edoc_type=self.fiscal_operation_type,
        )

        self._set_partner_as_supplier(edoc.partner_id)
        self.save_partner_product_relation(edoc)
        self._attach_original_nfe_xml_to_document(edoc)

        return {
            "name": _("Documento Importado"),
            "type": "ir.actions.act_window",
            "target": "current",
            "views": [[False, "form"]],
            "res_id": edoc.id,
            "res_model": "l10n_br_fiscal.document",
        }

    def edit_parsed_xml(self, parsed_xml):
        for wizard_product in self.imported_products_ids:
            database_product = wizard_product.product_id
            if not database_product:
                raise UserError(
                    _(
                        """Há pelo menos uma linha sem produto selecionado.
                         Selecione um produto para cada linha
                         para continuar."""
                    )
                )
            if not wizard_product.uom_internal:
                raise UserError(
                    _(
                        """Há pelo menos uma linha sem unidade de medida selecionada.
                         Selecione uma unidade de medida para cada linha
                         para continuar."""
                    )
                )
            for xml_product in parsed_xml.infNFe.det:
                if xml_product.prod.xProd == wizard_product.product_name:
                    # Validação comentada para realização de testes
                    # TODO: Descomentar essa validação
                    # self._check_ncm_nbm_cest(
                    #   xml_product.prod, wizard_product.product_id)
                    xml_product.prod.xProd = database_product.name
                    xml_product.prod.cEAN = database_product.barcode
                    xml_product.prod.cEANTrib = database_product.barcode
                    xml_product.prod.cProd = database_product.default_code
                    xml_product.prod.uCom = wizard_product.uom_internal.code
        return parsed_xml

    def _set_partner_as_supplier(self, partner_id):
        partner_id.supplier = True

    def save_partner_product_relation(self, edoc):
        for product_line in self.imported_products_ids:
            partner_product_relation = self.env["product.supplierinfo"].search(
                [
                    ("name", "=", edoc.partner_id.id),
                    ("product_id", "=", product_line.product_id.id),
                ],
                limit=1,
            )
            if partner_product_relation:
                values = {
                    "product_id": product_line.product_id.id,
                    "product_name": product_line.product_name,
                    "price": self.env["uom.uom"]
                    .browse(product_line.uom_internal.id)
                    ._compute_price(
                        product_line.price_unit_com, product_line.product_id.uom_id
                    ),
                    "partner_uom": product_line.uom_internal.id,
                }
                partner_product_relation.update(values)
            else:
                supplier_info = self.env["product.supplierinfo"].create(
                    {
                        "name": edoc.partner_id.id,
                        "product_name": product_line.product_name,
                        "product_id": product_line.product_id.id,
                        "partner_uom": product_line.uom_internal.id,
                        "price": self.env["uom.uom"]
                        .browse(product_line.uom_internal.id)
                        ._compute_price(
                            product_line.price_unit_com, product_line.product_id.uom_id
                        ),
                    }
                )
                supplier_info.product_id.write({"seller_ids": [(4, supplier_info.id)]})

    def get_partner_product_relation(self):
        for product_line in self.imported_products_ids:
            partner_product_relation = self.env["product.supplierinfo"].search(
                [
                    ("name", "=", self.partner_id.id),
                    ("product_name", "=", product_line.product_name),
                ],
                limit=1,
            )
            if partner_product_relation:
                product_line.product_id = partner_product_relation.product_id
                product_line.uom_internal = partner_product_relation.partner_uom

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

    product_id = fields.Many2one(
        comodel_name="product.product", string="Internal Reference"
    )

    uom_internal = fields.Many2one(
        "uom.uom",
        "Internal UOM",
        help="Internal UoM, equivalent to the one in the document",
    )

    uom_com = fields.Char(string="UOM Comercial")

    quantity_com = fields.Float(string="Comercial Quantity")

    price_unit_com = fields.Float(string="Comercial Price Unit")

    uom_trib = fields.Char(string="UOM Fiscal")

    quantity_trib = fields.Float(string="Fiscal Quantity")

    price_unit_trib = fields.Float(string="Fiscal Price Unit")

    total = fields.Float(string="Total")

    import_xml_id = fields.Many2one(comodel_name="l10n_br_nfe.import_xml")
