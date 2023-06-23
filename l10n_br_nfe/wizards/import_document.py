# Copyright (C) 2021  Gabriel Cardoso de Faria - Kmee
# Copyright (C) 2022  Renan Hiroki Bastos - Kmee
# Copyright (C) 2023  Luiz Felipe do Divino - Kmee
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64

from erpbrasil.base.fiscal.edoc import detectar_chave_edoc

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_nfe.models.document import parse_xml_nfe


class NfeImport(models.TransientModel):
    """Importar XML Nota Fiscal Eletrônica"""

    _name = "l10n_br_nfe.import_xml"
    _inherit = "l10n_br_fiscal.document.import.wizard.mixin"

    xml_partner_cpf_cnpj = fields.Char(string="Imported Partner Identification")

    xml_partner_name = fields.Char(string="Imported Partner Name")

    imported_products_ids = fields.One2many(
        string="Imported Products",
        comodel_name="l10n_br_nfe.import_xml.products",
        inverse_name="import_xml_id",
    )

    nat_op = fields.Char(string="Natureza da Operação")

    @api.onchange("xml")
    def _onchange_xml(self):
        if self.xml:
            self.set_fields_by_xml_data()

            if self.partner_id:
                self._get_product_supplierinfo()

    def parse_xml(self):
        return self._edit_parsed_xml(parse_xml_nfe(base64.b64decode(self.xml)))

    def create_edoc_from_xml(self):
        self.set_fiscal_operation_type()

        edoc = self.env["l10n_br_fiscal.document"].import_nfe_xml(
            self.parse_xml(),
            edoc_type=self.fiscal_operation_type,
        )

        self._attach_original_nfe_xml_to_document(edoc)
        self._set_product_supplierinfo(edoc)

        return edoc

    def set_fiscal_operation_type(self):
        document = self.get_document_by_xml(self.parse_xml())

        if document.cnpj_cpf_emitente == self.company_id.cnpj_cpf:
            self.fiscal_operation_type = "out"
        else:
            self.fiscal_operation_type = "in"

    def set_fields_by_xml_data(self):
        parsed_xml = self.parse_xml()
        document = self.get_document_by_xml(parsed_xml)

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
        self.xml_partner_cpf_cnpj = document.cnpj_cpf_emitente
        self.xml_partner_name = (
            parsed_xml.infNFe.emit.xFant or parsed_xml.infNFe.emit.xNome
        )
        self.partner_id = self.env["res.partner"].search(
            [
                "|",
                ("cnpj_cpf", "=", document.cnpj_cpf_emitente),
                ("nfe40_xNome", "=", parsed_xml.infNFe.emit.xNome),
            ],
            limit=1,
        )
        self.nat_op = parsed_xml.infNFe.ide.natOp
        self._check_nfe_xml_products(parsed_xml)

    def get_document_by_xml(self, xml):
        if not hasattr(xml, "infNFe"):
            return

        return detectar_chave_edoc(xml.infNFe.Id[3:])

    def _check_nfe_xml_products(self, parsed_xml):
        product_ids = []
        for product in parsed_xml.infNFe.det:
            vICMS = 0
            pICMS = 0
            pIPI = 0
            vIPI = 0
            icms_tags = [
                tag for tag in dir(product.imposto.ICMS) if tag.startswith("ICMS")
            ]
            for tag in icms_tags:
                if getattr(product.imposto.ICMS, tag) is not None:
                    icms_choice = getattr(product.imposto.ICMS, tag)
            if hasattr(icms_choice, "pICMS"):
                pICMS = icms_choice.pICMS
            if hasattr(icms_choice, "vICMS"):
                vICMS = icms_choice.vICMS
            ipi_trib = product.imposto.IPI.IPITrib
            if ipi_trib is not None:
                if hasattr(ipi_trib, "pIPI"):
                    pIPI = ipi_trib.pIPI
                if hasattr(ipi_trib, "vIPI"):
                    vIPI = ipi_trib.vIPI
            product_ids.append(
                self.env["l10n_br_nfe.import_xml.products"]
                .create(
                    {
                        "product_name": product.prod.xProd,
                        "product_code": product.prod.cProd,
                        "ncm_xml": product.prod.NCM,
                        "cfop_xml": product.prod.CFOP,
                        "icms_percent": pICMS,
                        "icms_value": vICMS,
                        "ipi_percent": pIPI,
                        "ipi_value": vIPI,
                        "uom_internal": self.env["uom.uom"]
                        .search([("code", "=", product.prod.uCom)], limit=1)
                        .id,
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

    def _attach_original_nfe_xml_to_document(self, edoc):
        return self.env["ir.attachment"].create(
            {
                "name": "NFe-Importada-{}.xml".format(edoc.document_key),
                "datas": base64.b64decode(self.xml),
                "description": "XML NFe - Importada por XML",
                "res_model": "l10n_br_fiscal.document",
                "res_id": edoc.id,
            }
        )

    def _search_supplierinfo(self, partner_id, product_name, product_code):
        return self.env["product.supplierinfo"].search(
            [
                ("name", "=", partner_id.id),
                "|",
                ("product_name", "=", product_name),
                ("product_code", "=", product_code),
            ],
            limit=1,
        )

    def _get_product_supplierinfo(self):
        for product_line in self.imported_products_ids:
            product_supplierinfo = self._search_supplierinfo(
                self.partner_id, product_line.product_name, product_line.product_code
            )
            if product_supplierinfo:
                product_line.product_id = product_supplierinfo.product_id
                product_line.uom_internal = product_supplierinfo.partner_uom

    def _set_product_supplierinfo(self, edoc):
        for product_line in self.imported_products_ids:
            product_supplierinfo = self._search_supplierinfo(
                edoc.partner_id, product_line.product_name, product_line.product_code
            )
            values = {
                "product_id": product_line.product_id.id,
                "product_name": product_line.product_name,
                "product_code": product_line.product_code,
                "price": self.env["uom.uom"]
                .browse(product_line.uom_internal.id)
                ._compute_price(
                    product_line.price_unit_com, product_line.product_id.uom_id
                ),
                "partner_uom": product_line.uom_internal.id,
            }
            if product_supplierinfo:
                product_supplierinfo.update(values)
            else:
                values["name"] = edoc.partner_id.id
                supplier_info = self.env["product.supplierinfo"].create(values)
                supplier_info.product_id.write({"seller_ids": [(4, supplier_info.id)]})

    def _edit_parsed_xml(self, parsed_xml):
        for product_line in self.imported_products_ids.filtered("product_id"):
            internal_product = product_line.product_id
            for xml_product in parsed_xml.infNFe.det:
                if xml_product.prod.cProd == product_line.product_code:
                    xml_product.prod.xProd = internal_product.name
                    xml_product.prod.cProd = internal_product.default_code
                    xml_product.prod.cEAN = internal_product.barcode or "SEM GTIN"
                    xml_product.prod.cEANTrib = internal_product.barcode or "SEM GTIN"
                    xml_product.prod.uCom = product_line.uom_internal.code
                    if product_line.new_cfop_id:
                        xml_product.prod.CFOP = product_line.new_cfop_id.code
        return parsed_xml


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

    product_code = fields.Char(string="Partner Product Code")

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product Internal Reference",
    )

    uom_internal = fields.Many2one(
        "uom.uom",
        "Internal UOM",
        help="Internal UoM, equivalent to the comercial one in the document",
    )

    ncm_xml = fields.Char(string="Código NCM no XML")

    ncm_internal = fields.Char(
        string="Código NCM Interno", related="product_id.ncm_id.code"
    )

    cfop_xml = fields.Char(string="CFOP no XML")

    new_cfop_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="Alterar CFOP",
        default=False,
        required=False,
    )

    icms_percent = fields.Char(string="Alíquota ICMS")

    icms_value = fields.Char(string="Valor ICMS")

    ipi_percent = fields.Char(string="Alíquota IPI")

    ipi_value = fields.Char(string="Valor IPI")

    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id and not self.product_id.ncm_id:
            raise UserError(_("Product without NCM!"))
