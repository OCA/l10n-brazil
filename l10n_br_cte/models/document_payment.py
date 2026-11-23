# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# pylint: disable=consider-merging-classes-inherited

from odoo import Command, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import MODELO_FISCAL_CTE
from odoo.addons.l10n_br_fiscal_edi.tools import EdiInstallment

# tpCTe: 0 normal and 3 substitute CT-e; the complement (1) and the annulment (2)
# have no collection in the layout
CTE_WITH_COLLECTION = ("0", "3")


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _edi_get_installments(self):
        """Installments of the collection (cobr) declared by the CT-e."""
        self.ensure_one()
        if self.document_type != MODELO_FISCAL_CTE:
            return super()._edi_get_installments()
        declared = self.cte40_cobr.cte40_dup.filtered(
            lambda dup: dup.cte40_dVenc and dup.cte40_vDup
        ).sorted(lambda dup: (dup.cte40_dVenc, dup.cte40_nDup or ""))
        return [
            EdiInstallment(dup.cte40_nDup or "", dup.cte40_dVenc, dup.cte40_vDup)
            for dup in declared
        ]

    def _cte_has_collection(self, installments):
        """The CT-e carries a collection (cobr) when it is the normal or the
        substitute CT-e (the complement and the annulment have no such group in the
        layout), has an amount to collect and some installment is due after the day
        of the issue: what is paid in cash has no duplicate."""
        today = fields.Date.context_today(self)
        return bool(
            self.cte40_tpCTe in CTE_WITH_COLLECTION
            and self.amount_financial_total > 0
            and any(installment.date_due > today for installment in installments)
        )

    def _edi_set_installments(self, installments):
        """Write the collection (cobr) of a CT-e issued by the company: the invoice
        and one duplicate for each installment of the bill. A CT-e that has none of
        it loses the one that a previous issue wrote."""
        super()._edi_set_installments(installments)
        if self.document_type != MODELO_FISCAL_CTE or self.imported_document:
            return
        # the models of the tags are concrete only once registered
        self.with_context(
            spec_schema="cte", spec_version="40"
        )._register_remaining_schema_models_hook()
        document = self.sudo()  # the tags are technical records
        document.cte40_cobr.cte40_fat.unlink()
        document.cte40_cobr.unlink()
        if not self._cte_has_collection(installments):
            return
        discount = self.amount_financial_discount_value
        invoice = self.env["cte.40.tcte_fat"].sudo()
        document.cte40_cobr = (
            self.env["cte.40.tcte_cobr"]
            .sudo()
            .create(
                {
                    "cte40_fat": invoice.create(
                        {
                            "cte40_vOrig": self.amount_financial_total_gross,
                            "cte40_vDesc": discount if discount > 0 else False,
                            "cte40_vLiq": self.amount_financial_total,
                        }
                    ).id,
                    "cte40_dup": [
                        Command.create(
                            {
                                "cte40_nDup": installment.number,
                                "cte40_dVenc": installment.date_due,
                                "cte40_vDup": installment.amount,
                            }
                        )
                        for installment in installments
                    ],
                }
            )
        )

    def _document_number(self):
        """The invoice of the collection takes the number of the CT-e once it has
        one."""
        result = super()._document_number()
        for document in self.filtered(
            lambda doc: doc.document_type == MODELO_FISCAL_CTE
            and doc.cte40_cobr.cte40_fat
            and not doc.cte40_cobr.cte40_fat.cte40_nFat
        ):
            document.sudo().cte40_cobr.cte40_fat.cte40_nFat = document.document_number
        return result
