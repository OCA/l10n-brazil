# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime, time

from pytz import UTC, timezone

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_PARTNER,
    SITUACAO_EDOC_EM_DIGITACAO,
)


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    move_ids = fields.One2many(
        comodel_name="account.move",
        inverse_name="fiscal_document_id",
        string="Invoices",
    )

    # proxy fields to enable writing the related (shadowed) fields
    # to the fiscal document from the account.move through the _inherits system
    # despite they have the same names.
    fiscal_partner_id = fields.Many2one(related="partner_id", readonly=False)
    fiscal_company_id = fields.Many2one(related="company_id", readonly=False)
    fiscal_currency_id = fields.Many2one(related="currency_id", readonly=False)
    fiscal_partner_shipping_id = fields.Many2one(
        related="partner_shipping_id", readonly=False
    )
    fiscal_user_id = fields.Many2one(related="user_id", readonly=False)

    # commented out because of badly written TestInvoiceDiscount.test_date_in_out
    #    def write(self, vals):
    #        if self.document_type_id:
    #            return super().write(vals)

    fiscal_line_ids = fields.One2many(
        copy=False,
    )

    # For some reason, perhaps limitation of _inhertis,
    # the related directly in the account.move does not work correctly.
    incoterm_id = fields.Many2one(related="move_ids.invoice_incoterm_id")

    document_date = fields.Datetime(
        compute="_compute_document_date", inverse="_inverse_document_date", store=True
    )

    date_in_out = fields.Datetime(
        compute="_compute_date_in_out", inverse="_inverse_date_in_out", store=True
    )

    @api.depends("move_ids", "move_ids.invoice_date")
    def _compute_document_date(self):
        for record in self:
            if record.move_ids and record.issuer == DOCUMENT_ISSUER_PARTNER:
                move_id = record.move_ids[0]
                if move_id.invoice_date:
                    user_tz = timezone(self.env.user.tz or "UTC")
                    doc_date = datetime.combine(move_id.invoice_date, time.min)
                    record.document_date = (
                        user_tz.localize(doc_date).astimezone(UTC).replace(tzinfo=None)
                    )

    def _inverse_document_date(self):
        for record in self:
            if record.move_ids and record.issuer == DOCUMENT_ISSUER_PARTNER:
                move_id = record.move_ids[0]
                if record.document_date:
                    move_id.invoice_date = record.document_date.date()

    @api.depends("move_ids", "move_ids.date")
    def _compute_date_in_out(self):
        for record in self:
            if record.move_ids and record.issuer == DOCUMENT_ISSUER_PARTNER:
                move_id = record.move_ids[0]
                if move_id.date:
                    user_tz = timezone(self.env.user.tz or "UTC")
                    doc_date = datetime.combine(move_id.date, time.min)
                    record.date_in_out = (
                        user_tz.localize(doc_date).astimezone(UTC).replace(tzinfo=None)
                    )

    def _inverse_date_in_out(self):
        for record in self:
            if record.move_ids and record.issuer == DOCUMENT_ISSUER_PARTNER:
                move_id = record.move_ids[0]
                if record.date_in_out:
                    move_id.date = record.date_in_out.date()

    def unlink(self):
        non_draft_documents = self.filtered(
            lambda d: d.state != SITUACAO_EDOC_EM_DIGITACAO
        )

        if non_draft_documents:
            UserError(
                _("You cannot delete a fiscal document " "which is not draft state.")
            )
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        self.env.cr.execute(
            "alter table account_move alter column fiscal_document_id drop not null;"
        )  # FIXME move to _auto_init
        # OVERRIDE
        # force creation of fiscal_document_line only when creating an AML record
        # In order not to affect the creation of the dummy document, a test was included
        # that verifies that the ACTIVE field is not False. As the main characteristic
        # of the dummy document is the ACTIVE field is False
        records = []
        for values in vals_list:
            if not values.get("document_type_id") and not values.get(
                "document_serie_id"
            ):
                # means we should skip the fiscal document creation
                continue
            if (
                values.get("fiscal_line_ids") and values.get("active") is not False
            ):  # TODO can we remove the active test?
                values.update({"fiscal_line_ids": False})
            records.append(super().create(values))  # TODO repair batch create
        return records
