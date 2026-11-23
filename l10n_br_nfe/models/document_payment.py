# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# pylint: disable=consider-merging-classes-inherited

from odoo import models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFE,
)
from odoo.addons.l10n_br_fiscal_edi.tools import EdiInstallment, EdiPayment

from ..constants.nfe import FISCAL_PAYMENT_MODE

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
            for dup in self.nfe40_dup
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
            for payment in self.nfe40_detPag
        ]
        return payments or super()._edi_get_payments()

    def _edi_payment_means_label(self, means):
        """The name of the tPag of the NF-e and of the NFC-e."""
        if self.document_type_id.code not in NFE_MODELS:
            return super()._edi_payment_means_label(means)
        return dict(FISCAL_PAYMENT_MODE).get(means) or super()._edi_payment_means_label(
            means
        )
