# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models

from odoo.addons.l10n_br_assisted_assessment.constants import SERVICE_TYPES

from ..constants import PAYMENT_TYPES


class CbsAssessmentPayment(models.Model):
    _name = "l10n_br_cbs_assisted_assessment.payment"
    _description = "CBS payment returned by the assessment APIs"
    _order = "collection_date desc, darf_number, id"

    request_id = fields.Many2one(
        comodel_name="l10n_br_assisted_assessment.request",
        string="Last Request",
        ondelete="set null",
        index=True,
        help="Request that last delivered this DARF. An increment updates the "
        "stored payment instead of creating another one.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    service = fields.Selection(selection=SERVICE_TYPES, required=True, index=True)
    collection_date = fields.Date(required=True)
    darf_number = fields.Char(required=True, size=17, index=True)
    payment_type = fields.Selection(selection=PAYMENT_TYPES, required=True)
    counterparty_vat = fields.Char(
        string="Counterparty Tax ID",
        help="Tax id of the other party of the payment: the acquirer for a RAD "
        "that extinguished this taxpayer's debit, or the taxpayer for a payment "
        "made by the taxpayer.",
    )
    line_ids = fields.One2many(
        comodel_name="l10n_br_cbs_assisted_assessment.payment.line",
        inverse_name="payment_id",
    )

    _sql_constraints = [
        (
            "payment_natural_key",
            "unique(company_id, service, darf_number, payment_type)",
            "This DARF was already stored for the company and service.",
        ),
    ]

    @api.depends("darf_number", "payment_type")
    def _compute_display_name(self):
        payment_types = dict(
            self._fields["payment_type"]._description_selection(self.env)
        )
        for payment in self:
            payment.display_name = " ".join(
                part
                for part in (
                    payment.darf_number,
                    payment_types.get(payment.payment_type),
                )
                if part
            ) or _("New")

    @api.model
    def _upsert(self, request, vals):
        """Merge one DARF increment into the payment already stored."""
        lines = vals["lines"]
        header = {
            "company_id": request.company_id.id,
            "request_id": request.id,
            "service": request.service,
            "collection_date": vals["collection_date"],
            "darf_number": vals["darf_number"],
            "payment_type": vals["payment_type"],
            "counterparty_vat": vals.get("counterparty_vat"),
        }
        payment = self.search(
            [
                ("company_id", "=", request.company_id.id),
                ("service", "=", request.service),
                ("darf_number", "=", vals["darf_number"]),
                ("payment_type", "=", vals["payment_type"]),
            ],
            limit=1,
        )
        if payment:
            payment.write(header)
        else:
            payment = self.create(header)
        payment._upsert_lines(lines)
        return payment

    def _upsert_lines(self, vals_list):
        """Update composition lines sent again and keep the ones left out."""
        self.ensure_one()
        stored = {line.sequence: line for line in self.line_ids}
        to_create = []
        for vals in vals_list:
            line = stored.get(vals["sequence"])
            if line:
                if line._values_changed(vals):
                    line.write(vals)
            else:
                to_create.append(dict(vals, payment_id=self.id))
        created = self.env["l10n_br_cbs_assisted_assessment.payment.line"].create(
            to_create
        )
        (self.line_ids | created)._match_document()
        return True


class CbsAssessmentPaymentLine(models.Model):
    _name = "l10n_br_cbs_assisted_assessment.payment.line"
    _description = "CBS payment composition line"
    _order = "sequence, id"

    payment_id = fields.Many2one(
        comodel_name="l10n_br_cbs_assisted_assessment.payment",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(related="payment_id.company_id", store=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    sequence = fields.Integer(required=True)
    period_id = fields.Many2one(
        comodel_name="l10n_br_assisted_assessment.period",
        string="Period",
        ondelete="set null",
        index=True,
    )
    date_due = fields.Date(string="Due Date")
    counterparty_vat = fields.Char(
        string="Counterparty Tax ID",
        help="Supplier of an acquirer withholding, or the taxpayer whose debit "
        "a RAD payment extinguished.",
    )
    document_key = fields.Char(string="DFE Key", size=100, index=True)
    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
    )
    amount_principal = fields.Monetary(string="Principal")
    amount_fine = fields.Monetary(string="Fine")
    amount_interest = fields.Monetary(string="Interest")
    amount_total = fields.Monetary(string="Total")

    _sql_constraints = [
        (
            "payment_sequence_uniq",
            "unique(payment_id, sequence)",
            "This composition sequence was already stored for the DARF.",
        ),
    ]

    def _match_document(self):
        documents = self.env["l10n_br_fiscal.document"]
        for line in self:
            document = documents.browse()
            if line.document_key:
                document = documents.search(
                    [
                        ("document_key", "=", line.document_key),
                        ("company_id", "=", line.company_id.id),
                    ],
                    limit=1,
                )
            line.document_id = document
        return True

    def _values_changed(self, vals):
        self.ensure_one()
        for field_name, value in vals.items():
            if field_name == "payment_id":
                continue
            current = self[field_name]
            if current != value and (current or value):
                return True
        return False
