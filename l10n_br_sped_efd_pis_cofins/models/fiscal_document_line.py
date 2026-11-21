# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    FISCAL_IN,
    PROFIT_CALCULATION_REAL,
    TAX_FRAMEWORK_SIMPLES_ALL,
)

# CST of the credit the EFD Contribuicoes understands without more data than the
# fiscal line carries (see `_sped_credit`)
CREDIT_CST = "50"
# Table 4.3.7 (nature of the base of the credit) by the destination that the CFOP
# of the entry states: bens para revenda and bens utilizados como insumo
NAT_BC_CRED_BY_TYPE_MOVE = {"purchase_commerce": "01", "purchase_industry": "02"}
# Table 4.3.6 (type of the credit) of the CST 50
COD_CRED_BASIC = "101"
COD_CRED_DIFFERENTIATED = "102"


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    def _get_sped_credit_accounts(self):
        """The analytic account (COD_CTA of the C170, 0500) of the lines that the
        PVA asks it for: in a company of the non-cumulative regime, the C170 of
        a sale taxed by PIS or COFINS (CST 01 to 09), of an entry with credit
        (CST 50 to 66) and of an entry without credit (CST 70 to 75). The account
        is the one of the line of the bill; a line without a bill gives none, and
        the C170 then goes out with a blank COD_CTA, which the PVA refuses. The
        Lucro Presumido keeps it blank, which the PVA validates."""
        accounts = self.env["account.account"]
        for line in self:
            if line._sped_needs_account():
                accounts |= line.account_line_ids[:1].account_id
        return accounts

    def _sped_needs_account(self):
        self.ensure_one()
        company = self.company_id
        if (
            company.profit_calculation != PROFIT_CALCULATION_REAL
            or company.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL
        ):
            return False
        if self.fiscal_operation_type == FISCAL_IN:
            codes = (self.entry_pis_cst_id.code, self.entry_cofins_cst_id.code)
        else:
            codes = (self.pis_cst_code, self.cofins_cst_code)
        return any(
            "01" <= (code or "") <= "09"
            or "50" <= (code or "") <= "66"
            or "70" <= (code or "") <= "75"
            for code in codes
        )

    def _get_sped_cfop_label(self):
        """The CFOP of the line as the user reads it."""
        self.ensure_one()
        if not self.cfop_id:
            return _("not informed")
        return f"{self.cfop_id.code} ({self.cfop_id.name})"

    def _sped_credit(self, tax_domain):
        """The credit this entry line books in the C170 (CST 50 to 66) for the
        M100/M105 (PIS) or M500/M505 (COFINS), or None when it books none.

        The fiscal line only has what it takes to tell the credit linked to the
        taxed revenue in the domestic market (CST 50) of a resale or an input
        (industrialization): the type of the credit is 101 at the basic rate of
        the regime and 102 at another, and the nature of the base is 01 or 02 by
        the destination of the CFOP. Any other CST or CFOP would be a guess, so
        the file is not generated and the message says which line it is."""
        self.ensure_one()
        if self.fiscal_operation_type != FISCAL_IN:
            return None
        cst = self[f"entry_{tax_domain}_cst_id"].code or ""
        if not ("50" <= cst <= "66"):
            return None
        nat_bc = NAT_BC_CRED_BY_TYPE_MOVE.get(self.cfop_id.type_move)
        if cst != CREDIT_CST or not nat_bc:
            document = self.document_id
            message = _(
                "The item %(item)s (%(product)s) of the document %(document)s "
                "books %(tax)s credit with the CST %(cst)s and the CFOP %(cfop)s. "
                "This version of the file only derives the credit of a purchase "
                "for resale and for industrialization (CST 50), so it was not "
                "generated. Fix the CFOP or the operation of the line, or handle "
                "this credit outside the system.",
                item=document.fiscal_line_ids.ids.index(self.id) + 1,
                product=self.name or self.product_id.display_name or "",
                document=document.document_number or document.id,
                tax=tax_domain.upper(),
                cst=cst,
                cfop=self._get_sped_cfop_label(),
            )
            if document._can_recompute_entry_cst():
                message += " " + _(
                    "The document is still being typed: the button "
                    '"Recalculate Entry CST" of the document recalculates the CST '
                    "of the lines by the current rule."
                )
            raise UserError(message)
        basic = self.company_id.piscofins_id[f"tax_{tax_domain}_id"].percent_amount
        rate = self[f"{tax_domain}_percent"]
        return {
            "cst": cst,
            "nat_bc": nat_bc,
            "base": self[f"{tax_domain}_base"],
            "rate": rate,
            "value": self[f"{tax_domain}_value"],
            "cod_cred": (
                COD_CRED_BASIC
                if abs(rate - basic) < 0.00005
                else COD_CRED_DIFFERENTIATED
            ),
        }
