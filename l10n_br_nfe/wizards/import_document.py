# Copyright (C) 2021  Gabriel Cardoso de Faria - Kmee
# Copyright (C) 2022  Renan Hiroki Bastos - Kmee
# Copyright (C) 2023  Luiz Felipe do Divino - Kmee
# Copyright (C) 2023  Felipe Zago Rodrigues - Kmee
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64

from erpbrasil.base.fiscal.edoc import detectar_chave_edoc

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

from odoo.addons.l10n_br_fiscal.constants.fiscal import MODELO_FISCAL_NFE


class DocumentImporterWizardMixin(models.TransientModel):
    _inherit = "l10n_br_fiscal.document.import.wizard.mixin"

    @api.model
    def _detect_binding(self, binding):
        """
        Register the import_xml NFe importer
        """
        if hasattr(binding, "NFe"):
            return (MODELO_FISCAL_NFE, "l10n_br_nfe.import_xml")
        return super()._detect_binding(binding)


class NfeImport(models.TransientModel):
    """Importar XML Nota Fiscal Eletrônica"""

    _name = "l10n_br_nfe.import_xml"
    _description = "Import XML Brazilian Fiscal Document"
    _inherit = "l10n_br_fiscal.document.import.wizard.mixin"

    xml_partner_cpf_cnpj = fields.Char(string="Imported Partner Identification")

    xml_partner_name = fields.Char(string="Imported Partner Name")

    imported_products_ids = fields.One2many(
        string="Imported Products",
        comodel_name="l10n_br_nfe.import_xml.products",
        inverse_name="import_xml_id",
    )

    nat_op = fields.Char(string="Natureza da Operação")

    def _fill_wizard_from_binding(self):
        binding = self._parse_file()
        document_key = self._document_key_from_binding(binding)
        infNFe = binding.NFe.infNFe

        self._find_existing_document()
        self._check_xml_data(binding)
        self._set_fiscal_operation_type()
        self.document_key = document_key.chave
        self.document_number = int(document_key.numero_documento)
        self.document_serie = int(document_key.numero_serie)
        self.xml_partner_cpf_cnpj = document_key.cnpj_cpf_emitente
        self.xml_partner_name = infNFe.emit.xFant or infNFe.emit.xNome
        self.partner_id = self.env["res.partner"].search(
            [
                "|",
                ("vat", "=", infNFe.emit.CNPJ),
                ("nfe40_xNome", "=", infNFe.emit.xNome),
            ],
            limit=1,
        )
        self.nat_op = infNFe.ide.natOp
        self.fiscal_operation_id = self._find_fiscal_operation(
            infNFe.det[0].prod.CFOP, self.nat_op, self.fiscal_operation_type
        )
        self._create_imported_products_by_xml()

    def _parse_file(self):
        binding = super()._parse_file()
        return self._edit_parsed_xml(binding)

    def _document_key_from_binding(self, binding):
        return detectar_chave_edoc(binding.NFe.infNFe.Id[3:])

    def _check_xml_data(self, binding):
        document = self._document_key_from_binding(binding)
        nfe_model_code = self.env.ref("l10n_br_fiscal.document_55").code

        if document.modelo_documento != nfe_model_code:
            raise UserError(
                _(f"Incorrect fiscal document model! Accepted one is {nfe_model_code}")
            )

    def _create_imported_products_by_xml(self):
        xml = self._parse_file()
        product_ids = []
        for product in xml.NFe.infNFe.det:
            product_ids.append(
                self.env["l10n_br_nfe.import_xml.products"]
                .create(self._prepare_imported_product_values(product))
                .id
            )

        self.imported_products_ids = [Command.set(product_ids)]

    def _prepare_imported_product_values(self, product):
        taxes = self._get_taxes_from_xml_product(product)
        supplier_id = self._search_product_supplier_by_product_code(product.prod.cProd)
        product_id = self._match_product(product.prod)
        # if self.fiscal_operation_type == "in"
        # and product_id and product_id.purchase_ok:
        if False:  # seems former test is always true after you
            # imported the product once -> it screws the UOM.
            uom_id = product_id.uom_po_id
        else:
            uom_id = self.env["uom.uom"].search(
                [
                    "|",
                    ("code", "=", product.prod.uCom),
                    ("code", "=", product.prod.uTrib),
                ],
                limit=1,
            )
            if not uom_id:  # search for alias
                uom_id = self.env["uom.uom"].search(
                    [
                        "|",
                        ("name", "=", product.prod.uCom),
                        ("name", "=", product.prod.uTrib),
                    ],
                    limit=1,
                )

        return {
            "product_name": product.prod.xProd,
            "product_code": product.prod.cProd,
            "ncm_xml": product.prod.NCM,
            "cfop_xml": product.prod.CFOP,
            "product_id": product_id and product_id.id or False,
            "icms_percent": taxes["pICMS"],
            "icms_value": taxes["vICMS"],
            "ipi_percent": taxes["pIPI"],
            "ipi_value": taxes["vIPI"],
            "uom_internal": uom_id.id,
            "uom_com": product.prod.uCom,
            "quantity_com": product.prod.qCom,
            "price_unit_com": product.prod.vUnCom,
            "uom_trib": product.prod.uTrib,
            "quantity_trib": product.prod.qTrib,
            "price_unit_trib": product.prod.vUnTrib,
            "total": product.prod.vProd,
            "import_xml_id": self.id,
            "product_supplier_id": supplier_id.id,
            "uom_conversion_factor": supplier_id.partner_uom_factor or 1,
        }

    def _search_product_supplier_by_product_code(self, code):
        return self.env["product.supplierinfo"].search(
            [
                ("partner_id", "=", self.partner_id.id),
                ("product_code", "=", code),
            ],
            limit=1,
        )

    def _get_product_by_supplier(self, code):
        supplier_id = self._search_product_supplier_by_product_code(code)
        if not supplier_id:
            return False

        if supplier_id.product_id:
            return supplier_id.product_id

        variant_ids = supplier_id.product_tmpl_id.product_variant_ids
        return variant_ids[0]

    def _match_product(self, xml_product):
        product_id = self._get_product_by_supplier(xml_product.cProd)
        if product_id:
            return product_id

        domain = []
        if hasattr(xml_product, "cProd") and xml_product.cProd:
            domain = expression.OR([domain, [("default_code", "=", xml_product.cProd)]])

        if hasattr(xml_product, "cEANTrib") and xml_product.cEANTrib != "SEM GTIN":
            domain = expression.OR([domain, [("barcode", "=", xml_product.cEANTrib)]])

        rec_id = False
        if domain:
            rec_id = self.env["product.product"].search(domain, limit=1)
        return rec_id

    def _get_taxes_from_xml_product(self, product):
        vICMS = 0
        pICMS = 0
        pIPI = 0
        vIPI = 0
        icms_tags = [tag for tag in dir(product.imposto.ICMS) if tag.startswith("ICMS")]
        for tag in icms_tags:
            if getattr(product.imposto.ICMS, tag) is not None:
                icms_choice = getattr(product.imposto.ICMS, tag)
        if hasattr(icms_choice, "pICMS"):
            pICMS = icms_choice.pICMS
        if hasattr(icms_choice, "vICMS"):
            vICMS = icms_choice.vICMS
        if hasattr(product.imposto.IPI, "IPITrib"):
            ipi_trib = product.imposto.IPI.IPITrib
            if hasattr(ipi_trib, "pIPI"):
                pIPI = ipi_trib.pIPI
            if hasattr(ipi_trib, "vIPI"):
                vIPI = ipi_trib.vIPI

        return {"vICMS": vICMS, "pICMS": pICMS, "vIPI": vIPI, "pIPI": pIPI}

    def _create_edoc_from_file(self):
        binding = self._parse_file()
        edoc = self.env["l10n_br_fiscal.document"].import_binding_nfe(
            binding,
            edoc_type=self.fiscal_operation_type,
        )
        edoc.document_type_id = self.env.ref("l10n_br_fiscal.document_55").id
        edoc.fiscal_operation_id = self.fiscal_operation_id
        for line in edoc.fiscal_line_ids:
            line.fiscal_operation_id = self.fiscal_operation_id
            line.uom_id = line.uot_id

        if not self.partner_id:
            self.partner_id = edoc.partner_id

        self._attach_original_nfe_xml_to_document(edoc)

        if self.fiscal_operation_type == "in":
            self.imported_products_ids._find_or_create_product_supplierinfo()

        return binding, edoc

    def _set_fiscal_operation_type(self):
        document_key = self._document_key_from_binding(self._parse_file())
        if document_key.cnpj_cpf_emitente == self.company_id.cnpj_cpf:
            self.fiscal_operation_type = "out"
        else:
            self.fiscal_operation_type = "in"

    def _attach_original_nfe_xml_to_document(self, edoc):
        return self.env["ir.attachment"].create(
            {
                "name": f"NFe-Importada-{edoc.document_key}.xml",
                "datas": base64.b64decode(self.file),
                "description": "XML NFe - Importada por XML",
                "res_model": "l10n_br_fiscal.document",
                "res_id": edoc.id,
            }
        )

    def _edit_parsed_xml(self, parsed_xml):
        for product_line in self.imported_products_ids.filtered("product_id"):
            internal_product = product_line.product_id
            for xml_product in parsed_xml.NFe.infNFe.det:
                if xml_product.prod.cProd == product_line.product_code:
                    xml_product.prod.cProd = internal_product.default_code
                    xml_product.prod.xProd = internal_product.name
                    xml_product.prod.cEAN = internal_product.barcode or "SEM GTIN"
                    xml_product.prod.cEANTrib = internal_product.barcode or "SEM GTIN"
                    xml_product.prod.uCom = product_line.uom_internal.code
                    xml_product.prod.uTrib = product_line.uom_internal.code
                    if product_line.new_cfop_id:
                        xml_product.prod.CFOP = product_line.new_cfop_id.code
        return parsed_xml


class NfeImportProducts(models.TransientModel):
    _name = "l10n_br_nfe.import_xml.products"
    _description = "Import XML NFe Products"

    product_name = fields.Char()

    uom_com = fields.Char(string="UOM Comercial")

    quantity_com = fields.Float(string="Comercial Quantity")

    price_unit_com = fields.Float(string="Comercial Price Unit")

    uom_trib = fields.Char(string="UOM Fiscal")

    quantity_trib = fields.Float()

    price_unit_trib = fields.Float(string="Fiscal Price Unit")

    total = fields.Float()

    import_xml_id = fields.Many2one(comodel_name="l10n_br_nfe.import_xml")

    product_code = fields.Char(string="XML Product Code")

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product Internal Reference",
    )

    product_supplier_id = fields.Many2one(
        comodel_name="product.supplierinfo",
        string="Product Supplier",
    )

    uom_internal = fields.Many2one(
        comodel_name="uom.uom",
        help="Internal UoM, equivalent to the comercial one in the document",
    )

    ncm_xml = fields.Char(string="XML NCM Code")

    ncm_internal = fields.Char(
        related="product_id.ncm_id.code",
        string="Internal NCM Code",
    )

    cfop_xml = fields.Char(string="XML CFOP")

    new_cfop_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="Change CFOP",
    )

    icms_percent = fields.Char(string="Alíquota ICMS")

    icms_value = fields.Char(string="ICMS Value")

    ipi_percent = fields.Char(string="Alíquota IPI")

    ipi_value = fields.Char(string="IPI Value")

    imported_partner_id = fields.Many2one(related="import_xml_id.partner_id")

    uom_conversion_factor = fields.Float(string="UOM Conversion Factor", default=1)

    def _find_or_create_product_supplierinfo(self):
        for product in self:
            if not product.product_id:
                continue

            if not product.product_supplier_id:
                product._create_product_supplier()
            else:
                product._update_product_supplier()

    def _create_product_supplier(self):
        if self.uom_internal:
            price = self.uom_internal._compute_price(
                self.price_unit_com, self.product_id.uom_id
            )
        else:
            price = self.product_id.lst_price

        self.product_supplier_id = self.env["product.supplierinfo"].create(
            {
                "product_id": self.product_id.id,
                "product_name": self.product_name,
                "product_code": self.product_code,
                "price": price,
                "partner_id": self.imported_partner_id.id,
                "partner_uom_id": self.uom_internal.id,
                "partner_uom_factor": self.uom_conversion_factor,
            }
        )
        self.product_id.write(
            {"seller_ids": [Command.link(self.product_supplier_id.id)]}
        )

    def _update_product_supplier(self):
        self.product_supplier_id.write(
            {
                "product_id": self.product_id.id,
                "product_name": self.product_name,
                "product_code": self.product_code,
                "price": self.uom_internal._compute_price(
                    self.price_unit_com, self.product_id.uom_id
                ),
                "partner_uom_id": self.uom_internal.id,
                "partner_uom_factor": self.uom_conversion_factor,
            }
        )
