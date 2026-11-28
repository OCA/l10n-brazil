# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from odoo import models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EDOC_PURPOSE_COMPLEMENTAR,
    SITUACAO_FISCAL_CANCELADO,
    SITUACAO_FISCAL_COMPLEMENTAR,
    SITUACAO_FISCAL_DENEGADO,
    SITUACAO_FISCAL_INUTILIZADO,
    SITUACAO_FISCAL_REGULAR,
    SITUACAO_FISCAL_SPED_CONSIDERA_CANCELADO,
)

# state_edoc -> SPED document situation (table 4.1.2 of the EFD ICMS/IPI and
# EFD Contribuicoes guides). Anything else (draft, in the middle of the
# transmission) is not a document the books must carry.
SPED_COD_SIT_BY_STATE_EDOC = {
    "autorizada": SITUACAO_FISCAL_REGULAR,
    "cancelada": SITUACAO_FISCAL_CANCELADO,
    "denegada": SITUACAO_FISCAL_DENEGADO,
    "inutilizada": SITUACAO_FISCAL_INUTILIZADO,
}

# IND_PGTO of the C100: a vista, a prazo, sem pagamento
SPED_IND_PGTO_CASH = "0"
SPED_IND_PGTO_TERM = "1"
SPED_IND_PGTO_NONE = "9"


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _get_sped_cod_sit(self):
        """COD_SIT of the C100, shared by every SPED.

        ``state_fiscal`` is only written when a document is cancelled, so it
        cannot be the only source: when it is empty the situation comes from
        the state of the document (``state_edoc``) and from its purpose
        (complementary).

        The extemporaneous situations (01, 07) are for a document booked
        OUTSIDE the period it belonged to: the entry date of the document is of
        an earlier period than the one of the declaration. A document that is
        in a declaration because its entry date is in the period is regular
        (an invoice emitted last month and received this month is 00 here), and
        the PVA refuses 01 when DT_E_S is inside the period.
        """
        self.ensure_one()
        if self.state_fiscal:
            return self.state_fiscal
        cod_sit = SPED_COD_SIT_BY_STATE_EDOC.get(
            self.state_edoc, SITUACAO_FISCAL_REGULAR
        )
        if (
            cod_sit == SITUACAO_FISCAL_REGULAR
            and self.edoc_purpose == EDOC_PURPOSE_COMPLEMENTAR
        ):
            cod_sit = SITUACAO_FISCAL_COMPLEMENTAR
        return cod_sit

    def _has_sped_c100(self):
        """Does this document go into the C100 (and its children)?

        A denied note and an unused number do not: the situation codes 04
        (denied) and 05 (unused number) of the table 4.1.2 were discontinued in
        the Guia Pratico from 01/2023 and the information is no longer
        required. A cancelled note still goes in, with COD_SIT 02. The one place
        to bring the old codes back is this method (return True).
        """
        self.ensure_one()
        return self._get_sped_cod_sit() not in (
            SITUACAO_FISCAL_DENEGADO,
            SITUACAO_FISCAL_INUTILIZADO,
        )

    def _is_sped_cancelled(self):
        """Cancelled, denied and unused numbers carry no values, no items and no
        analytic registers (Guia Pratico, C100)."""
        self.ensure_one()
        return self._get_sped_cod_sit() in SITUACAO_FISCAL_SPED_CONSIDERA_CANCELADO

    def _get_sped_ind_pgto(self):
        """IND_PGTO of the C100 (and of the A100), shared by every SPED: 0 paid
        on the spot, 1 on terms, 9 without payment (Guia Pratico). It comes from
        the installments of the bill of the document: all due on the emission
        date is "a vista", any later one is "a prazo", no installment is "sem
        pagamento"."""
        self.ensure_one()
        # move_ids comes from l10n_br_account, which both SPED modules depend on
        moves = (
            self.move_ids if "move_ids" in self._fields else self.env["account.move"]
        )
        terms = moves.filtered(lambda move: move.state != "cancel").line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        if not terms:
            return SPED_IND_PGTO_NONE
        invoice_date = self.document_date and self.document_date.date()
        if all(
            not line.date_maturity
            or not invoice_date
            or line.date_maturity <= invoice_date
            for line in terms
        ):
            return SPED_IND_PGTO_CASH
        return SPED_IND_PGTO_TERM

    def _is_sped_without_access_key(self):
        """NF-e or NFC-e (55, 65) with no access key."""
        self.ensure_one()
        return self.document_type_id.code in ("55", "65") and not self.document_key

    def _get_sped_entry_date(self):
        """DT_E_S of an entry: the entry date, never before the emission (the
        PVA warns when DT_E_S is earlier than DT_DOC). Without an entry date it
        is the emission."""
        self.ensure_one()
        entry = self.date_in_out
        if not entry or (
            self.document_date and entry.date() < self.document_date.date()
        ):
            return self.document_date
        return entry

    def _get_sped_icms_amounts(self):
        """(VL_BC_ICMS, VL_ICMS) of the document as the books carry them: the
        ones of the document less the lines of an entry without credit right,
        which carry none in the C170."""
        self.ensure_one()
        lines = self.fiscal_line_ids.filtered(
            lambda line: line._sped_icms_without_credit()
        )
        return (
            self.amount_icms_base - sum(lines.mapped("icms_base")),
            self.amount_icms_value - sum(lines.mapped("icms_value")),
        )

    def _get_sped_ipi_value(self):
        """VL_IPI of the document as the books carry it: the one of the document
        less the lines of an entry without credit right."""
        self.ensure_one()
        lines = self.fiscal_line_ids.filtered(
            lambda line: line._sped_ipi_without_credit()
        )
        return self.amount_ipi_value - sum(lines.mapped("ipi_value"))

    def _get_sped_pis_cofins_values(self):
        """(VL_PIS, VL_COFINS) of the document as the books carry them: what the
        C170 of its lines carry, so the header equals the items. An entry booked
        without credit right (CST 70 to 75) carries no value in the C170, and so
        none in the total."""
        self.ensure_one()
        pis = cofins = 0.0
        for line in self.fiscal_line_ids:
            # the entry CST of the line is not in the l10n_br_fiscal of 18.0 yet
            without_credit = getattr(
                line, "_entry_piscofins_without_credit", lambda tax_domain: False
            )
            if not without_credit("pis"):
                pis += line.pis_value
            if not without_credit("cofins"):
                cofins += line.cofins_value
        return pis, cofins

    def _is_sped_own_issue(self):
        """NF-e or NFC-e issued by the company: the books carry the C100 and
        the C190 only, never the items (C170), as the Guia Pratico says."""
        self.ensure_one()
        return self.issuer == "company" and self.document_type_id.code in ("55", "65")
