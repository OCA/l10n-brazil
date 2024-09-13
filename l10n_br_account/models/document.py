# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime, time

from pytz import UTC, timezone

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    DOCUMENT_ISSUER_PARTNER,
    MODELO_FISCAL_CTE,
    MODELO_FISCAL_NFE,
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
    fiscal_proxy_partner_id = fields.Many2one(
        string="Fiscal Partner",
        related="partner_id",
        readonly=False,
    )
    fiscal_proxy_company_id = fields.Many2one(
        string="Fiscal Company",
        related="company_id",
        readonly=False,
    )
    fiscal_proxy_currency_id = fields.Many2one(
        string="Fiscal Currency",
        related="currency_id",
        readonly=False,
    )
    fiscal_proxy_user_id = fields.Many2one(
        string="Fiscal User",
        related="user_id",
        readonly=False,
    )

    # commented out because of badly written TestInvoiceDiscount.test_date_in_out
    #    def write(self, vals):
    #        if self.document_type_id:
    #            return super().write(vals)

    fiscal_line_ids = fields.One2many(
        copy=False,
    )

    # For some reason, perhaps limitation of _inhertis,
    # the related directly in the account.move does not work correctly.
    incoterm_id = fields.Many2one(
        string="Fiscal Inconterm",
        related="move_ids.invoice_incoterm_id",
    )

    document_date = fields.Datetime(
        compute="_compute_document_date", inverse="_inverse_document_date", store=True
    )

    date_in_out = fields.Datetime(
        compute="_compute_date_in_out", inverse="_inverse_date_in_out", store=True
    )

    document_type_id = fields.Many2one(inverse="_inverse_document_type_id")

    def _inverse_document_type_id(self):
        pass  # (meant to be overriden in account.move)

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
        """
        It's not allowed to create a fiscal document line without a document_type_id
        anyway. But instead of letting Odoo crash in this case we simply avoid creating
        the record. This makes it possible to create an account.move without a
        fiscal_document_id despite the _inherits system:
        Odoo will write NULL as the value in this case.
        """
        if self._context.get("create_from_move"):
            filtered_vals_list = []
            for values in vals_list:
                if values.get("document_type_id") or values.get("document_serie_id"):
                    # we also disable the fiscal_line_ids creation here to
                    # let the ORM create them later from the account.move.line records
                    values.update({"fiscal_line_ids": False})
                    filtered_vals_list.append(values)
            return super().create(filtered_vals_list)
        else:
            return super().create(vals_list)

    def _update_cache(self, values, validate=True):
        """
        Overriden to avoid raising error with ensure_one() in super()
        when called from some account.move onchange
        as we allow empty fiscal document in account.move.
        """
        if len(self) == 0:
            return
        return super()._update_cache(values, validate)

    @api.returns("mail.message", lambda value: value.id)
    def message_post(self, **kwargs):
        """
        broadcast message_post to all related account.move so
        messages in a fiscal document chatter are visible in the
        related account moves.
        """
        for doc in self:
            for move in doc.move_ids:
                move.message_post(**kwargs)

    def cancel_move_ids(self):
        for record in self:
            if record.move_ids:
                self.move_ids.button_cancel()

    def _document_cancel(self, justificative):
        result = super()._document_cancel(justificative)
        msg = f"Cancelamento: {justificative}"
        self.cancel_move_ids()
        self.message_post(body=msg)
        return result

    def _document_correction(self, justificative):
        result = super()._document_correction(justificative)
        msg = f"Carta de correção: {justificative}"
        self.message_post(body=msg)
        return result

    def _document_deny(self):
        msg = _(
            "Canceled due to the denial of document %(document_number)s",
            document_number=self.document_number,
        )
        self.cancel_move_ids()
        self.message_post(body=msg)

    def action_document_confirm(self):
        result = super().action_document_confirm()
        if not self._context.get("skip_post"):
            move_ids = self.move_ids.filtered(lambda move: move.state == "draft")
            move_ids._post()
        return result

    def action_document_back2draft(self):
        result = super().action_document_back2draft()
        if self.move_ids:
            self.move_ids.button_draft()
        return result

    def exec_after_SITUACAO_EDOC_DENEGADA(self, old_state, new_state):
        self.ensure_one()
        models_cancel_on_deny = [MODELO_FISCAL_NFE, MODELO_FISCAL_CTE]
        if (
            self.document_type_id.code in models_cancel_on_deny
            and self.issuer == DOCUMENT_ISSUER_COMPANY
        ):
            self._document_deny()
        return super().exec_after_SITUACAO_EDOC_DENEGADA(old_state, new_state)
