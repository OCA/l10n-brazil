# Copyright (C) 2021  Gabriel Cardoso de Faria - Kmee
# Copyright (C) 2022  Renan Hiroki Bastos - Kmee
# Copyright (C) 2023  Luiz Felipe do Divino - Kmee
# Copyright (C) 2023  Felipe Zago Rodrigues - Kmee
# Copyright (C) 2026  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64
from collections import Counter

from erpbrasil.base.fiscal.cnpj_cpf import formata

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

from odoo.addons.l10n_br_fiscal.constants.fiscal import MODELO_FISCAL_NFE


class DocumentImportWizard(models.TransientModel):
    _inherit = "l10n_br_fiscal.document.import.wizard"

    nat_op = fields.Char(string="Natureza da Operação")

    @api.model
    def _detect_binding(self, binding):
        """
        Register the import_xml NFe importer
        """
        if hasattr(binding, "infNFe") or hasattr(binding, "NFe"):
            return self._detect_document_type(MODELO_FISCAL_NFE)
        return super()._detect_binding(binding)

    def _extract_binding_data(self, binding):
        if hasattr(binding, "NFe"):
            binding = binding.NFe
        res = super()._extract_binding_data(binding)
        if self.document_type == MODELO_FISCAL_NFE:
            self._extract_key_information(binding.infNFe.Id[3:])
            infNFe = binding.infNFe
            self.nat_op = infNFe.ide.natOp
            self.fiscal_operation_id = self._find_fiscal_operation(
                self._most_common_cfop(infNFe),
                self.nat_op,
                self.fiscal_operation_type,
            )
            self._create_imported_products_by_xml(binding)
        return res

    @api.model
    def _most_common_cfop(self, infNFe):
        """Return the CFOP shared by most of the NFe lines.

        A single NFe can mix CFOPs (e.g. a freight or one-off line), so
        picking the first line's CFOP is unreliable. The majority CFOP
        better represents the document's fiscal operation.
        """
        cfops = [det.prod.CFOP for det in infNFe.det if det.prod.CFOP]
        if not cfops:
            return False
        return Counter(cfops).most_common(1)[0][0]

    def _destination_partner_from_binding(self, binding):
        if self.document_type == MODELO_FISCAL_NFE:
            if hasattr(binding, "NFe"):
                binding = binding.NFe
            self.destination_partner_id = self._search_partner(
                cnpj=binding.infNFe.dest.CNPJ,
                legal_name=binding.infNFe.dest.xNome,
            )
            self.issuer_legal_name = binding.infNFe.emit.xNome
            self.issuer_name = binding.infNFe.emit.xFant

            self.destination_cnpj = formata(binding.infNFe.dest.CNPJ)
            self.destination_name = binding.infNFe.dest.xNome

    def _parse_file(self):
        binding = super()._parse_file()
        if hasattr(binding, "NFe"):
            binding = binding.NFe
        if self.document_type == MODELO_FISCAL_NFE:
            return self._edit_parsed_xml(binding)
        return binding

    def _check_xml_data(self, binding):
        document = self._document_key_from_binding(binding)
        nfe_model_code = self.env.ref("l10n_br_fiscal.document_55").code

        if document.modelo_documento != nfe_model_code:
            raise UserError(
                _(f"Incorrect fiscal document model! Accepted one is {nfe_model_code}")
            )

    def _create_imported_products_by_xml(self, binding):
        product_ids = []
        for product in binding.infNFe.det:
            product_ids.append(
                self.env["l10n_br_fiscal.document.import.wizard.line"]
                .create(self._prepare_imported_product_values(product))
                .id
            )

        self.imported_products_ids = [Command.set(product_ids)]

    def _prepare_imported_product_values(self, product):
        taxes = self._get_taxes_from_xml_product(product)
        supplier_id = self._search_product_supplier_by_product_code(product.prod.cProd)
        product_id = self._match_product(product.prod)
        uom_id = self._match_uom_by_code(product.prod.uCom, product.prod.uTrib)

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
        product_id = self._match_product_by_purchase(xml_product)
        if product_id:
            return product_id

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

    def _match_product_by_purchase(self, xml_product):
        """Priority match from the referenced purchase order.

        When the XML line references the buyer's purchase order, take the
        product from the matching purchase order line first: it is the most
        authoritative match since the buyer already stated which product was
        ordered.

        On an inbound supplier NF-e, ``xPed`` holds the buyer's purchase order
        name and ``nItemPed`` holds the item number inside that order, so they
        map to ``purchase.order.name`` and ``purchase.order.line.sequence``
        (NOT to the partner_order / partner_order_line fields, which store the
        *supplier's* own order reference).
        """
        pol_model = self.env.get("purchase.order.line")
        if pol_model is None:
            return False
        xped = (getattr(xml_product, "xPed", "") or "").strip()
        if not xped:
            return False

        partner = self.partner_id.id
        pol = pol_model.sudo()
        nitemped = (getattr(xml_product, "nItemPed", "") or "").strip()

        # 1) exact reference: buyer PO name + line item number.
        if nitemped:
            try:
                sequence = int(nitemped)
            except ValueError:
                sequence = None
            if sequence is not None:
                line = pol.search(
                    [
                        ("order_id.partner_id", "=", partner),
                        ("order_id.name", "=", xped),
                        ("sequence", "=", sequence),
                    ],
                    limit=1,
                )
                if line:
                    return line.product_id

        # 2) heuristic: narrow to the referenced order, then disambiguate the
        # line by the XML product code / barcode.
        lines = pol.search(
            [("order_id.partner_id", "=", partner), ("order_id.name", "=", xped)]
        )
        if len(lines) == 1:
            return lines.product_id
        cprod = getattr(xml_product, "cProd", None)
        ean = getattr(xml_product, "cEANTrib", None)
        for line in lines:
            if cprod and line.product_id.default_code == cprod:
                return line.product_id
            if ean and ean != "SEM GTIN" and line.product_id.barcode == ean:
                return line.product_id
        return False

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
        if self.document_type == MODELO_FISCAL_NFE:
            binding = self._parse_file()
            edoc = self.env["l10n_br_fiscal.document"].import_binding_nfe(
                binding,
                edoc_type=self.fiscal_operation_type,
            )
            edoc.document_type_id = self.env.ref("l10n_br_fiscal.document_55").id
            edoc.fiscal_operation_id = self.fiscal_operation_id
            wizard_lines_by_code = {
                w.product_code: w for w in self.imported_products_ids
            }
            for line in edoc.fiscal_line_ids:
                # Preserve the XML price_unit because setting
                # fiscal_operation_id triggers _compute_price_unit_fiscal
                # which would overwrite it with the product's list/cost price
                # (which is 0 when the product is created during import).
                price_unit = line.price_unit
                line.fiscal_operation_id = self.fiscal_operation_id
                line.price_unit = price_unit
                line.uom_id = line.uot_id
                if not line.uom_id:
                    # When the product was created during this import its uom
                    # was not resolved from the XML at line-creation time (the
                    # line compute ran before the product's units were set), so
                    # fall back to the unit the wizard matched from uCom/uTrib
                    # and align the created product's units with it.
                    wl = (
                        wizard_lines_by_code.get(line.product_id.default_code)
                        if line.product_id
                        else None
                    )
                    if wl and wl.uom_internal:
                        line.uom_id = wl.uom_internal
                        if not wl.product_id:
                            line.product_id.uom_id = wl.uom_internal
                            line.product_id.uom_po_id = wl.uom_internal

            if not self.partner_id:
                self.partner_id = edoc.partner_id

            self._attach_original_nfe_xml_to_document(edoc)

            if self.fiscal_operation_type == "in":
                self.imported_products_ids._find_or_create_product_supplierinfo()

            return binding, edoc
        return super()._create_edoc_from_file()

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
            for xml_product in parsed_xml.infNFe.det:
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


class DocumentImportWizardLine(models.TransientModel):
    """NFe specialization of the generic fiscal import wizard line.

    It only adds the NFe specific data: the commercial/tax unit split and
    the ICMS/IPI taxes read from the XML. It also injects the partner UoM
    de-para into the generated ``product.supplierinfo``.
    """

    _inherit = "l10n_br_fiscal.document.import.wizard.line"

    uom_trib = fields.Char(string="UOM Fiscal")

    quantity_trib = fields.Float()

    price_unit_trib = fields.Float(string="Fiscal Price Unit")

    icms_percent = fields.Char(string="Alíquota ICMS")

    icms_value = fields.Char(string="ICMS Value")

    ipi_percent = fields.Char(string="Alíquota IPI")

    ipi_value = fields.Char(string="IPI Value")

    product_domain = fields.Json(
        compute="_compute_product_domain",
        help="Domain applied to the product_id picker (Json so the web "
        "client evaluates it as an array, not as a Char string).",
    )

    @api.depends("imported_partner_id", "product_id")
    def _compute_product_domain(self):
        """Restrict the selectable products to those ordered from this supplier.

        When a product cannot be auto-matched, the user picks it from the
        many2one; with the purchase module installed (soft-dependency, like
        ``_match_product_by_purchase``), propose only the products that have a
        purchase order line from the NFe supplier with quantity still to be
        billed — mirroring the legacy akretion importer. The picker stays
        bounded: core sets ``qty_to_invoice`` to 0 on draft/cancelled orders
        and on fully billed lines, so only the "open supply pipeline"
        (confirmed POs awaiting/partially billed) is offered instead of the
        whole supplier product history. When there is no candidate (no
        purchase module / no open PO line), fall back to the plain
        purchasable-products domain so the user is never stuck.
        """
        purchase_line_model = self.env.get("purchase.order.line")
        candidates_by_partner = {}
        if purchase_line_model is not None:
            for partner in self.mapped("imported_partner_id"):
                lines = purchase_line_model.sudo().search(
                    [
                        ("order_id.partner_id", "=", partner.id),
                        ("qty_to_invoice", ">", 0),
                    ]
                )
                candidates_by_partner[partner.id] = lines.product_id.ids
        for line in self:
            domain = [("purchase_ok", "=", True)]
            product_ids = candidates_by_partner.get(line.imported_partner_id.id)
            if product_ids and not line.product_id:
                domain.append(("id", "in", product_ids))
            line.product_domain = domain

    def _prepare_supplierinfo_vals(self):
        vals = super()._prepare_supplierinfo_vals()
        vals.update(
            {
                "partner_uom_id": self.uom_internal.id,
                "partner_uom_factor": self.uom_conversion_factor,
            }
        )
        return vals
