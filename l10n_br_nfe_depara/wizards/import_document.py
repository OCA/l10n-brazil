# Copyright (C) 2022  Renan Hiroki Bastos - Kmee
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class NfeImport(models.TransientModel):
    """Importar XML Nota Fiscal Eletrônica"""

    _inherit = "l10n_br_nfe.import_xml"

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

    @api.onchange("nfe_xml")
    def _onchange_partner_id(self):
        super(NfeImport, self)._onchange_partner_id()
        if self.nfe_xml and self.partner_id:
            self._get_product_supplierinfo()
        return

    def _parse_xml_import_wizard(self, xml):
        parsed_xml, document = super(NfeImport, self)._parse_xml_import_wizard(xml)
        parsed_xml = self._edit_parsed_xml(parsed_xml)
        return parsed_xml, document

    def _check_product_data(self):
        for product_line in self.imported_products_ids:
            err_msg = ""
            if not product_line.product_id:
                err_msg += "referência interna"
            if not product_line.uom_internal:
                if err_msg:
                    err_msg += " e "
                err_msg += "unidade de medida"
            if err_msg:
                raise UserError(
                    _(
                        """Há pelo menos uma linha sem {}.
                         Selecione uma {} para cada linha
                         para continuar.""".format(
                            err_msg, err_msg
                        )
                    )
                )

    def _check_ncm(self, xml_product, wizard_product):
        if (
            wizard_product.ncm_id
            and hasattr(xml_product, "NCM")
            and xml_product.NCM
            and xml_product.NCM != wizard_product.ncm_id.code.replace(".", "")
        ):
            raise UserError(
                _(
                    """O NCM do produto {} no cadastro interno é diferente do NCM
                     na nota.\nNCM interno: {}\nNCM na nota: {}""".format(
                        wizard_product.display_name,
                        wizard_product.ncm_id.code,
                        xml_product.NCM,
                    )
                )
            )

    def _edit_parsed_xml(self, parsed_xml):
        for product_line in self.imported_products_ids:
            internal_product = product_line.product_id
            for xml_product in parsed_xml.infNFe.det:
                if xml_product.prod.cProd == product_line.product_code:
                    self._check_ncm(xml_product.prod, product_line.product_id)
                    xml_product.prod.xProd = internal_product.name
                    xml_product.prod.cEAN = internal_product.barcode
                    xml_product.prod.cEANTrib = internal_product.barcode
                    xml_product.prod.uCom = product_line.uom_internal.code
        return parsed_xml

    @api.multi
    def import_nfe_xml(self):
        self._check_product_data()
        res = super(NfeImport, self).import_nfe_xml()
        edoc = self.env["l10n_br_fiscal.document"].browse(res.get("res_id"))
        self._set_product_supplierinfo(edoc)
        return res


class NfeImportProducts(models.TransientModel):
    _inherit = "l10n_br_nfe.import_xml.products"

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product Internal Reference",
    )

    uom_internal = fields.Many2one(
        "uom.uom",
        "Internal UOM",
        help="Internal UoM, equivalent to the comercial one in the document",
    )
