# Copyright (C) 2022  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models
from odoo.tests.common import Form


class Settlement(models.Model):
    _inherit = "sale.commission.settlement"

    def _prepare_invoice_header(self, settlement, journal, date=False):
        invoice_dict = super()._prepare_invoice_header(settlement, journal, date)
        if self.env.context.get("document_type_id"):
            invoice_dict.update(
                {
                    "document_type_id": self.env.context.get("document_type_id"),
                    "fiscal_operation_id": self.env.context.get("fiscal_operation_id"),
                    "issuer": "partner" if journal.type == "purchase" else "company",
                }
            )
            invoice = self.env["account.move"].new(invoice_dict)

            invoice_dict = invoice._convert_to_write(invoice._cache)
        return invoice_dict

    def _prepare_invoice_line(self, settlement, invoice, product):
        invoice_line_dict = super()._prepare_invoice_line(settlement, invoice, product)
        if self.env.context.get("fiscal_operation_id"):
            invoice_line_dict.update(
                {
                    "fiscal_operation_id": self.env.context.get("fiscal_operation_id"),
                }
            )
            invoice_line = self.env["account.move.line"].new(invoice_line_dict)
            invoice_line._onchange_product_id_fiscal()
            # Put commission fee after product onchange
            if invoice_line.invoice_id.type == "in_refund":
                invoice_line.price_unit = -settlement.total
            else:
                invoice_line.price_unit = settlement.total
            invoice_line._onchange_fiscal_operation_id()
            invoice_line_dict = invoice_line._convert_to_write(invoice_line._cache)
        return invoice_line_dict

    def _prepare_invoice(self, journal, product, date=False):
        """
        This method uses Form.new() to prepare invoice data before creation.
        For some reason there's no accessible field called settlement_id in
        the account.move form (probably because of document.mixin ?)
        !!WARNING WE COULD NOT CALL SUPER!!
        """
        move_form = Form(
            self.env["account.move"].with_context(default_move_type="in_invoice")
        )

        if date:
            move_form.invoice_date = date
        partner = self._get_invoice_partner()
        move_form.partner_id = partner
        move_form.journal_id = journal
        for settlement in self:
            with move_form.invoice_line_ids.new() as line_form:
                line_form.product_id = product
                line_form.quantity = -1 if settlement.total < 0 else 1
                line_form.price_unit = abs(settlement.total)
                # Put period string
                lang = self.env["res.lang"].search(
                    [
                        (
                            "code",
                            "=",
                            partner.lang or self.env.context.get("lang", "en_US"),
                        )
                    ]
                )
                date_from = fields.Date.from_string(settlement.date_from)
                date_to = fields.Date.from_string(settlement.date_to)
                line_form.name += "\n" + _("Period: from %s to %s") % (
                    date_from.strftime(lang.date_format),
                    date_to.strftime(lang.date_format),
                )
                line_form.currency_id = (
                    settlement.currency_id
                )  # todo or compute agent currency_id?
                # todo change creation structure to support assigning
                #   settlement_id here
                # line_form.settlement_id = settlement
                settlement._post_process_line(line_form)
        vals = move_form._values_to_save(all_fields=True)
        return vals

    def make_invoices(self, journal, product, date=False, grouped=False):
        """
        Because settlement_id could't be set in '_prepare_invoice'
        we have to set it here
        """
        invoices = super().make_invoices(journal, product, date, grouped)
        for move in invoices:
            for move_line in move.invoice_line_ids:
                move_line.settlement_id = self
        return invoices
