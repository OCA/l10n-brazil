# Copyright 2025 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class L10nBrFiscalDocumentLineImportWizard(models.TransientModel):
    _name = "l10n_br_fiscal.document.line.import.wizard"
    _description = "Wizard for Importing Fiscal Document Lines"

    document_line_id = fields.Many2one("l10n_br_fiscal.document.line", readonly=True)
    document_code = fields.Char(string="Code")
    document_ean = fields.Char(string="EAN")
    document_name = fields.Char(string="Product")

    document_qty = fields.Float()
    document_uom = fields.Char()
    document_uom_trib = fields.Char()
    document_ncm_id = fields.Many2one("l10n_br_fiscal.ncm")
    document_cfop_id = fields.Many2one("l10n_br_fiscal.cfop")

    import_product_id = fields.Many2one("product.product", string="Product to Import")
    import_qty = fields.Float(string="Quantity to Import")
    import_ncm_id = fields.Many2one("l10n_br_fiscal.ncm")
    import_cfop_id = fields.Many2one("l10n_br_fiscal.cfop", string="CFOP to Import")
    import_uom_id = fields.Many2one("uom.uom", string="UoM to Import")

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        values["document_line_id"] = self.env.context.get("active_id")
        self._prepare_default_values(values)
        values.update(values)
        return values

    def _prepare_default_values(self, values):
        return {}

    def _prepare_update_values(self, values):
        return {}

    def _prepare_onchange_document_line_id(self):
        return {}

    @api.onchange("document_line_id")
    def onchange_document_line_id(self):
        if self.document_line_id:
            self.update(self._prepare_onchange_document_line_id())

    def update_document_data(self):
        self.ensure_one()
        document_line_id = self.env.context.get("active_id")
        if document_line_id:
            document_line = self.env["l10n_br_fiscal.document.line"].browse(
                document_line_id
            )
            values = {}
            self._prepare_update_values(values)
            document_line.write(values)

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
