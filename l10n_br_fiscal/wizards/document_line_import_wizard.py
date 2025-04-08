# Copyright 2025 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    PRODUCT_FISCAL_TYPE,
)


class L10nBrFiscalDocumentLineImportWizard(models.TransientModel):
    _name = "l10n_br_fiscal.document.line.import.wizard"
    _description = "Wizard for Importing Fiscal Document Lines"

    document_line_id = fields.Many2one("l10n_br_fiscal.document.line", readonly=True)

    # Doc session is readonly
    document_code = fields.Char(string="Code")
    document_ean = fields.Char(string="EAN")
    document_name = fields.Char(string="Product")
    document_qty = fields.Float()
    document_uom = fields.Char()
    document_uom_trib = fields.Char()
    document_ncm_id = fields.Many2one("l10n_br_fiscal.ncm")
    document_cfop_id = fields.Many2one("l10n_br_fiscal.cfop")

    # Import session will be written to l10n_br_fiscal.document
    import_product_id = fields.Many2one("product.product", string="Product to Import")
    import_qty = fields.Float(string="Quantity to Import")
    import_ncm_id = fields.Many2one("l10n_br_fiscal.ncm")
    import_cfop_id = fields.Many2one("l10n_br_fiscal.cfop", string="CFOP to Import")
    import_uom_id = fields.Many2one("uom.uom", string="UoM to Import")
    import_uom_trib_id = fields.Many2one("uom.uom", string="UoM Trib to Import")

    # Product details will be read/written from/to product
    import_product_fiscal_type = fields.Selection(
        selection=PRODUCT_FISCAL_TYPE, string="Tipo Fiscal"
    )
    product_supplierinfo_id = fields.Many2one("product.supplierinfo", readonly=True)

    # Advanced features
    allow_xml_data_edit = fields.Boolean("Allow XML Data Edit", default=False)

    @api.onchange("import_product_id")
    def _onchange_import_product_id(self):
        """
        Updates the product fields based on the selected `import_product_id`.
        """
        self.import_qty = self.document_qty

        if self.import_product_id:
            if self.import_product_id.uom_id:
                self.import_uom_id = self.import_product_id.uom_id
            if self.import_product_id.fiscal_type:
                self.import_product_fiscal_type = self.import_product_id.fiscal_type
            self._check_product_supplierinfo()

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)

        # Obter o ID da linha do documento fiscal do contexto
        document_line_id = self.env.context.get("active_id")
        if document_line_id:
            document_line = self.env["l10n_br_fiscal.document.line"].browse(
                document_line_id
            )

            # Definir os valores padrão com base na linha do documento fiscal
            values.update(
                {
                    "document_line_id": document_line_id,
                    # XML
                    "document_ncm_id": document_line.ncm_id.id,
                    "document_cfop_id": document_line.cfop_id.id,
                    # L10n_br_fiscal.document
                    "import_product_id": document_line.product_id.id,
                    "import_qty": document_line.quantity,
                    "import_ncm_id": document_line.ncm_id.id,
                    "import_cfop_id": document_line.cfop_id.id,
                    "import_uom_id": document_line.uom_id.id,
                }
            )

        return values

    def _prepare_onchange_document_line_id(self):
        return {}

    def _prepare_default_values(self, values):
        return {}

    def _prepare_update_values(self):
        # Preencher todos as unidades que forem iguais do documento, para acelerar o
        # processo
        # Preencher a unidade alternativa
        return {
            "product_id": self.import_product_id.id,
            "quantity": self.import_qty,
            "ncm_id": self.import_ncm_id.id,
            "cfop_id": self.import_cfop_id.id,
            "uom_id": self.import_uom_id.id,
        }

    @api.onchange("document_line_id")
    def onchange_document_line_id(self):
        if self.document_line_id:
            self.update(self._prepare_onchange_document_line_id())

    def update_document_data(self):
        self.ensure_one()
        if self.document_line_id:
            values = self._prepare_update_values()
            self.document_line_id.write(values)
            self._check_product_supplierinfo(create=True)
            self._check_other_lines_info(values)

    def action_create_product(self):
        # Remove previously linked product if needed
        if self.import_product_id or self.document_line_id.product_id:
            self.import_product_id = False
            self.document_line_id.product_id = False

        # Apply wizard specific values to match_or_create (MoC)
        context = {
            "moc_default_uom_id": self.import_uom_id.id,
            "moc_default_ncm_id": self.import_ncm_id.id,
            "moc_default_fiscal_type": self.import_product_fiscal_type,
        }

        action = self.document_line_id.with_context(context).action_create_product()
        product_id = action.get("res_id", False)
        self.import_product_id = product_id
        self.update_document_data()
        return action

    def _navigate_product(self, direction=False):
        self.ensure_one()
        self.update_document_data()

        if direction:
            document_line_model = self.env["l10n_br_fiscal.document.line"]
            document_lines = document_line_model.search([], order="id asc")
            current_index = document_lines.ids.index(self.env.context.get("active_id"))
            new_index = current_index + direction
            new_line = (
                document_lines[new_index]
                if 0 <= new_index < len(document_lines)
                else None
            )
            if new_line:
                return {
                    "type": "ir.actions.act_window",
                    "res_model": self._name,
                    "view_mode": "form",
                    "target": "new",
                    "context": {"active_id": new_line.id},
                }
        return {"type": "ir.actions.act_window_close"}

    def action_done(self):
        return self._navigate_product()

    def action_next_product(self):
        return self._navigate_product(1)

    def action_previous_product(self):
        return self._navigate_product(-1)

    def _check_alternative_uom(self, uom_id, alternative):
        if uom_id and uom_id.code != alternative:
            alternative_ids = uom_id.alternative_ids.filtered(
                lambda r: r.code == alternative
            )
            if not alternative_ids:
                self.env["uom.uom.alternative"].create(
                    {
                        "code": alternative,
                        "name": alternative,
                        "uom_id": uom_id.id,
                    }
                )

    def _check_product_supplierinfo(self, create=False):
        if self.import_product_id:
            supplier_info = self.env["product.supplierinfo"].search(
                [
                    ("name", "=", self.document_line_id.partner_id.id),
                    ("product_id", "=", self.import_product_id.id),
                    ("product_name", "=", self.document_name),
                    ("product_code", "=", self.document_code),
                    ("partner_uom", "=", self.document_uom),
                ],
                limit=1,
            )

            self.product_supplierinfo_id = False

            if supplier_info:
                self._set_supplier_info(supplier_info)
            elif create:
                partner_uom_factor = (
                    self.import_qty / self.document_qty if self.document_qty else 1
                )
                supplier_info = self.env["product.supplierinfo"].create(
                    {
                        "name": self.document_line_id.partner_id.id,
                        "product_id": self.import_product_id.id,
                        "product_tmpl_id": self.import_product_id.product_tmpl_id.id,
                        "product_name": self.document_name,
                        "partner_uom": self.document_uom,
                        "partner_uom_factor": partner_uom_factor,
                        "product_code": self.document_code,
                    }
                )

    def _set_supplier_info(self, supplier_info):
        self.product_supplierinfo_id = supplier_info
        self.import_qty = self.document_qty * supplier_info.partner_uom_factor
        if self.document_line_id.line_import_json:
            line_json = self.document_line_id.line_import_json
            price_unit_json = float(line_json.get("nfe40_vUnCom", False))

            if supplier_info.partner_uom_factor == 0:
                raise ValueError("The partner UoM factor cannot be zero.")

            if price_unit_json:
                self.document_line_id.price_unit = (
                    price_unit_json / supplier_info.partner_uom_factor
                )

    def _check_other_lines_info(self, values):
        pass
