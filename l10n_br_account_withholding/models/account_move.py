# Copyright 2022 Renato Lima - Akretion
# Copyright 2024 Marcel Savegnago - Escodoo (https://www.escodoo.com.br)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    wh_invoice_count = fields.Integer(
        string="WH Invoice Count", compute="_compute_wh_invoice_ids", readonly=True
    )
    wh_invoice_ids = fields.Many2many(
        comodel_name="account.move",
        string="WH Invoices",
        compute="_compute_wh_invoice_ids",
        readonly=True,
        copy=False,
    )

    @api.depends("line_ids.wh_move_line_id")
    def _compute_wh_invoice_ids(self):
        """
        Update withholding invoice IDs and their count for an invoice.

        Search for account move lines linked by 'wh_move_line_id' and update
        'wh_invoice_ids' and 'wh_invoice_count' on the invoice.

        :return: None.
        """
        for invoice in self:
            wh_invoices = (
                self.env["account.move.line"]
                .search([("wh_move_line_id", "in", invoice.line_ids.ids)])
                .move_id.ids
            )
            invoice.wh_invoice_ids = wh_invoices
            invoice.wh_invoice_count = len(wh_invoices)

    def action_view_wh_invoice(self):
        """
        Open the view for withholding invoices associated with the current record.

        Map 'wh_invoice_ids' to retrieve the related invoices. Prepare and return an
        action dict to open the invoice view. If no invoices are found, return an
        action to close the window.

        :return: A dictionary with action details to open related invoices or close
        the window.
        """
        invoices = self.mapped("wh_invoice_ids")
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_in_invoice_type"
        )
        if len(invoices):
            action["domain"] = [("id", "in", invoices.ids)]
        else:
            action = {"type": "ir.actions.act_window_close"}
        context = {
            "default_move_type": "in_invoice",
        }
        action["context"] = context
        return action

    def _prepare_wh_invoice(self, move_line, fiscal_group):
        """
        Prepare a withholding tax invoice based on the provided move line and fiscal
        group.

        :param move_line: The move line.
        :param fiscal_group: The fiscal group.

        :return: Dictionary of invoice values.
        """
        wh_date_invoice = move_line.move_id.date
        wh_due_invoice = wh_date_invoice.replace(day=fiscal_group.wh_due_day)
        values = {
            "partner_id": fiscal_group.partner_id.id,
            "date": wh_date_invoice,
            "invoice_date": wh_date_invoice,
            "invoice_date_due": wh_due_invoice + relativedelta(months=1),
            "move_type": "in_invoice",
            "journal_id": fiscal_group.journal_id.id or move_line.journal_id.id,
            "invoice_origin": move_line.move_id.name,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": move_line.name,
                        "price_unit": abs(move_line.balance),
                        "account_id": move_line.account_id.id,
                        "wh_move_line_id": move_line.id,
                        "analytic_account_id": move_line.analytic_account_id.id,
                    },
                )
            ],
        }
        return values

    def create_wh_invoices(self):
        """
        Create withholding tax invoices for applicable lines in the move.

        Iterate over each move in the recordset. For each tax line in the move
        that matches the criteria, create a withholding tax invoice if the line
        belongs to a supplier invoice and is associated with a tax that requires
        withholding. Prepare and post these invoices.

        :return: None. Generate withholding tax invoices and post them.
        """
        for move in self:
            for line in move.line_ids.filtered(lambda line: line.tax_line_id):
                # Create Wh Invoice only for supplier invoice
                if line.move_id and line.move_id.move_type != "in_invoice":
                    continue

                account_tax_group = line.tax_line_id.tax_group_id
                if account_tax_group and account_tax_group.fiscal_tax_group_id:
                    fiscal_group = account_tax_group.fiscal_tax_group_id
                    if (
                        fiscal_group.generate_wh_invoice
                        and fiscal_group.tax_withholding
                    ):
                        wh_invoice = self.env["account.move"].create(
                            self._prepare_wh_invoice(line, fiscal_group)
                        )
                        wh_invoice.message_post_with_view(
                            "mail.message_origin_link",
                            values={"self": wh_invoice, "origin": move},
                            subtype_id=self.env.ref("mail.mt_note").id,
                        )
                        wh_invoice.action_post()

    def _withholding_validate(self):
        """
        Validate withholding by updating related invoices' states and clearing their
        withholding move line references.

        For each record in the context, search for related invoices based on the
        withholding move line IDs associated with the record's line items. Set any
        posted invoices to draft, cancel any draft invoices, clear the withholding
        move line ID reference from the invoice lines, and invalidate the cache to
        ensure data coherency.

        :return: None
        """
        for m in self:
            wh_invoices = (
                self.env["account.move.line"]
                .search(
                    [
                        ("wh_move_line_id", "in", m.mapped("line_ids").ids),
                    ]
                )
                .mapped("move_id")
            )
            wh_invoices.filtered(lambda i: i.state == "posted").button_draft()
            wh_invoices.filtered(lambda i: i.state == "draft").button_cancel()
            wh_invoices.line_ids.wh_move_line_id = False
            wh_invoices.invalidate_cache()

    def button_draft(self):
        res = super().button_draft()
        self._withholding_validate()
        return res

    def _post(self, soft=True):
        res = super()._post(soft)
        self.create_wh_invoices()
        return res
