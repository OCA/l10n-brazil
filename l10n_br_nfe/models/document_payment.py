# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# pylint: disable=consider-merging-classes-inherited

from odoo import Command, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EDOC_PURPOSE_AJUSTE,
    EDOC_PURPOSE_DEVOLUCAO,
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFE,
)
from odoo.addons.l10n_br_fiscal_edi.tools import EdiInstallment, EdiPayment

from ..constants.nfe import (
    A_PRAZO,
    A_VISTA,
    FISCAL_PAYMENT_MODE,
    NFE_IN,
    NFE_OUT,
    SEM_PAGAMENTO,
)

NFE_MODELS = (MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE)


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _edi_get_installments(self):
        """The duplicates (``dup``) declared in the collection of the NF-e."""
        self.ensure_one()
        if self.document_type_id.code not in NFE_MODELS:
            return super()._edi_get_installments()
        installments = [
            EdiInstallment(
                number=dup.nfe40_nDup or "",
                date_due=dup.nfe40_dVenc,
                amount=dup.nfe40_vDup,
            )
            # nfe.40.dup is limited to the NF-e groups, and the invoice of an
            # imported document reads it for accounting users who are not in them.
            for dup in self.sudo().nfe40_dup
        ]
        return installments or super()._edi_get_installments()

    def _edi_get_payments(self):
        """The payments (``detPag``) declared in the NF-e."""
        self.ensure_one()
        if self.document_type_id.code not in NFE_MODELS:
            return super()._edi_get_payments()
        payments = [
            EdiPayment(
                means=payment.nfe40_tPag or "",
                amount=payment.nfe40_vPag,
                term="installments" if payment.nfe40_indPag == "1" else "cash",
                description=payment.nfe40_xPag or "",
            )
            for payment in self.sudo().nfe40_detPag
        ]
        return payments or super()._edi_get_payments()

    def _nfe_register_tag_models(self):
        """Make sure the spec models of the tags are concrete models."""
        self.with_context(
            spec_schema="nfe", spec_version="40"
        )._register_remaining_schema_models_hook()

    def _nfe_without_payment(self):
        """The NF-e declares no payment: devolution, adjustment, entry or no amount."""
        self.ensure_one()
        return bool(
            self.edoc_purpose in (EDOC_PURPOSE_DEVOLUCAO, EDOC_PURPOSE_AJUSTE)
            or not self.amount_financial_total
            or self.nfe40_tpNF == NFE_IN
        )

    def _edi_set_installments(self, installments):
        """Write the duplicates (``dup``) of an NF-e issued on terms."""
        super()._edi_set_installments(installments)
        self._nfe_register_tag_models()
        today = fields.Date.context_today(self)
        if not (
            self._need_compute_nfe_tags()
            and self.amount_financial_total > 0
            and self.nfe40_tpNF == NFE_OUT
            and self.document_type_id.code != MODELO_FISCAL_NFCE
            and any(installment.date_due > today for installment in installments)
        ):
            return
        # The tags are technical records: whoever issues the invoice may not be
        # allowed to delete the ones written by a previous issue.
        document = self.sudo()
        document.nfe40_dup = [Command.delete(dup.id) for dup in document.nfe40_dup] + [
            Command.create(
                {
                    "nfe40_nDup": installment.number,
                    "nfe40_dVenc": installment.date_due,
                    "nfe40_vDup": installment.amount,
                }
            )
            for installment in installments
        ]

    def _edi_set_payments(self, payments):
        """Write the payment (``detPag``) of an NF-e issued by the company."""
        super()._edi_set_payments(payments)
        if not self._need_compute_nfe_tags():
            return
        self._nfe_register_tag_models()
        payment = payments[0] if payments else None
        if self._nfe_without_payment() or not payment or payment.means == SEM_PAGAMENTO:
            values = {
                "nfe40_indPag": A_VISTA,
                "nfe40_tPag": SEM_PAGAMENTO,
                "nfe40_vPag": 0.00,
            }
        else:
            # TODO a payment may be partly in cash and partly on terms: it would
            # take two detPag.
            values = {
                "nfe40_indPag": A_PRAZO if payment.term == "installments" else A_VISTA,
                "nfe40_tPag": payment.means,
                "nfe40_vPag": payment.amount,
            }
        document = self.sudo()
        document.nfe40_detPag = [
            Command.delete(det_pag.id) for det_pag in document.nfe40_detPag
        ] + [Command.create(values)]

    def _edi_payment_means_label(self, means):
        """The name of the tPag of the NF-e and of the NFC-e."""
        if self.document_type_id.code not in NFE_MODELS:
            return super()._edi_payment_means_label(means)
        return dict(FISCAL_PAYMENT_MODE).get(means) or super()._edi_payment_means_label(
            means
        )
