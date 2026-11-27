# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# pylint: disable=consider-merging-classes-inherited

from dataclasses import replace

from odoo import _, api, fields, models


class Document(models.Model):
    """What a fiscal document declares to be paid, and the page that shows it.

    The installments and the payments are read from the document by the module of
    its type (NF-e ``dup`` and ``detPag``, CT-e ``cobr``). Nothing here creates a
    payable: the titles are born when the invoice is generated.
    """

    _inherit = "l10n_br_fiscal.document"

    edi_payment_summary = fields.Html(
        compute="_compute_edi_payment_summary",
        sanitize=False,
        help="Installments and payments declared by the document and the totals "
        "that go with them. It is not stored.",
    )

    def _edi_get_installments(self):
        """Installments declared by the document, as a list of ``EdiInstallment``."""
        self.ensure_one()
        return []

    def _edi_get_payments(self):
        """Payments declared by the document, as a list of ``EdiPayment``."""
        self.ensure_one()
        return []

    def _edi_display_installments(self):
        """Installments the page shows. Who knows more than the declaration (the
        invoice that will issue the document) overrides it."""
        self.ensure_one()
        return self._edi_get_installments()

    def _edi_display_payments(self):
        """Payments the page shows."""
        self.ensure_one()
        return self._edi_get_payments()

    def _edi_payment_means_label(self, means):
        """Name of a means of payment (tPag), to show instead of its code. The module
        that knows the selection of the means answers; the base shows the code."""
        self.ensure_one()
        return means

    def _edi_payment_totals(self):
        """Gross total, withholdings and net amount payable, as ``(gross, withholding,
        net)``. The total of the document is already net of the withholdings and is
        the same for every type, but it is only computed when the document has a
        fiscal operation: a CT-e imported without one would show zero, so the lines,
        which carry the amounts declared in the file, answer instead."""
        self.ensure_one()
        if self.fiscal_operation_id:
            net, withholding = self.fiscal_amount_total, self.amount_tax_withholding
        else:
            lines = self.fiscal_line_ids
            net = sum(lines.mapped("fiscal_amount_total"))
            withholding = sum(lines.mapped("amount_tax_withholding"))
        return net + withholding, withholding, net

    def _edi_installment_difference(self):
        """Net amount payable minus the sum of the installments shown."""
        self.ensure_one()
        installments = self._edi_display_installments()
        if not installments:
            return 0.0
        declared = sum(installment.amount for installment in installments)
        return self.currency_id.round(self._edi_payment_totals()[2] - declared)

    def _edi_installment_warning(self):
        """Message when the installments do not add up to the net amount payable."""
        self.ensure_one()
        if not self._edi_installment_difference():
            return False
        declared = sum(i.amount for i in self._edi_display_installments())
        return _(
            "The declared installments add up to %(declared)s; the net amount "
            "payable is %(net)s. The invoice spreads the difference by the weight "
            "of each installment."
        ) % {
            "declared": f"{declared:.2f}",
            "net": f"{self._edi_payment_totals()[2]:.2f}",
        }

    def _edi_payment_summary_values(self):
        """Values of the template ``document_payment_summary``, which the invoice
        reuses to show the same page. Empty when there is nothing to show."""
        self.ensure_one()
        installments = self._edi_display_installments()
        payments = self._edi_display_payments()
        gross, withholding, net = self._edi_payment_totals()
        if not (installments or payments or (self.imported_document and withholding)):
            return {}
        return {
            "currency": self.currency_id,
            "installments": installments,
            "payments": [
                replace(payment, label=self._edi_payment_means_label(payment.means))
                for payment in payments
            ],
            "totals": [
                (_("Document total"), gross),
                (_("Withholdings"), withholding),
                (_("Net amount payable"), net),
            ],
            "warning": self._edi_installment_warning(),
        }

    @api.depends(
        "imported_document",
        "state_edoc",
        "fiscal_operation_id",
        "fiscal_amount_total",
        "amount_tax_withholding",
        "fiscal_line_ids.fiscal_amount_total",
        "fiscal_line_ids.amount_tax_withholding",
    )
    def _compute_edi_payment_summary(self):
        for document in self:
            values = document._edi_payment_summary_values()
            document.edi_payment_summary = (
                self.env["ir.qweb"]._render(
                    "l10n_br_fiscal_edi.document_payment_summary", values
                )
                if values
                else False
            )

    def _edi_import_warnings(self):
        messages = super()._edi_import_warnings()
        warning = self._edi_installment_warning()
        if self.imported_document and warning:
            messages.append(warning)
        return messages

    def _edi_set_installments(self, installments):
        """Write the installments of an issued document in the tags of its type.

        :param installments: list of ``EdiInstallment``. The module of each
            document type overrides it; the base has nothing to write.
        """
        self.ensure_one()

    def _edi_set_payments(self, payments):
        """Write the payments of an issued document in the tags of its type.

        :param payments: list of ``EdiPayment``. The module of each document type
            overrides it; the base has nothing to write.
        """
        self.ensure_one()
