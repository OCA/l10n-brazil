# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models

from ..constants.fiscal import FISCAL_IN, TAX_FRAMEWORK_SIMPLES_ALL

# icmsst, issqn and irpj have no general input credit: their flags are manual.
CREDITABLE_TAX_DOMAINS = ("icms", "ipi", "pis", "cofins")

RESTRICTED_DESTINATIONS = ("purchase_ownuse", "purchase_asset")


class TaxCreditabilityMixin(models.AbstractModel):
    """Whether a fiscal line may credit its taxes, decided from the buyer
    regime, the CFOP and the CST. It holds no field: a line that stores the
    decision (stock price mixin) and a line that only reads it (fiscal
    document line) share the same rule.
    """

    _name = "l10n_br_fiscal.tax.creditability.mixin"
    _description = "Tax Creditability Mixin"

    def _is_non_cumulative(self):
        """Whether the company is under the non-cumulative PIS/COFINS regime.

        Lucro Real companies listed in art. 10 of Lei 10.833/2003 stay
        cumulative, so the company PIS/COFINS regime wins over
        ``profit_calculation``, which is only the fallback when unset.
        """
        self.ensure_one()
        regime = self.company_id.piscofins_id
        if not regime:
            return self.company_id.profit_calculation == "real"
        non_cumulative = self.env.ref(
            "l10n_br_fiscal.tax_pis_cofins_nao_columativo", raise_if_not_found=False
        )
        return bool(non_cumulative) and regime == non_cumulative

    def _creditable_tax_regime_gates(self):
        """Which tax domains the BUYER company may credit, by tax regime.

        - Simples Nacional takes no credit at all (LC 123/2006, art. 23);
        - IPI is only creditable by industries and assimilated (RIPI,
          arts. 226 and 251);
        - PIS/COFINS credits only exist in the non-cumulative regime
          (Leis 10.637/2002 e 10.833/2003, art. 3 of both).
        """
        self.ensure_one()
        company = self.company_id
        simples = company.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL
        industry = company.is_industry or company.ripi
        non_cumulative = self._is_non_cumulative()
        return {
            "icms": not simples,
            "ipi": not simples and industry,
            "pis": not simples and non_cumulative,
            "cofins": not simples and non_cumulative,
        }

    def _creditable_tax_destination_gates(self):
        """Which tax domains the DESTINATION of the goods forbids.

        A veto, never a permission: it only closes domains for the
        destinations the law restricts.

        - own use and consumption: no ICMS credit until 2033 (LC 87/96,
          art. 33, I, as amended by LC 171/2019), no IPI (RIPI, art. 226)
          and no PIS/COFINS, since it is not an input (PN COSIT/RFB 5/2018);
        - fixed assets: no IPI. ICMS (CIAP) and PIS/COFINS (Lei 10.833/2003,
          art. 3, par. 14) are credited over 48 months, which is not
          implemented, so the tax stays in the cost of the asset.
        """
        self.ensure_one()
        if self.cfop_id.type_move in RESTRICTED_DESTINATIONS:
            return dict.fromkeys(CREDITABLE_TAX_DOMAINS, False)
        return {}

    def _is_simples_supplier_without_credit(self):
        """Simples supplier that transferred no ICMS credit on the document.

        A Simples Nacional supplier only transfers the credit stated under
        CSOSN 101/201 (LC 123/2006, art. 23, par. 1 and 2), which arrives in
        ``icmssn_credit_value``. PIS and COFINS do not depend on the supplier
        regime (ADI SRF 15/2007).
        """
        self.ensure_one()
        partner = self.partner_id
        if not partner or partner.tax_framework not in TAX_FRAMEWORK_SIMPLES_ALL:
            return False
        return not self.icmssn_credit_value

    def _tax_credit_gates_allow(self, tax_domain):
        """Whether the BUYER regime, the DESTINATION of the goods (CFOP) and
        a Simples supplier allow the credit of ``tax_domain``, whatever the
        CST. The CST of an entry is derived from these gates, so they never
        read it.
        """
        self.ensure_one()
        if not self._creditable_tax_regime_gates().get(tax_domain):
            return False
        if not self._creditable_tax_destination_gates().get(tax_domain, True):
            return False
        if tax_domain == "icms":
            return not self._is_simples_supplier_without_credit()
        return True

    def _get_creditability_cst(self, tax_domain):
        """The CST whose nature decides the credit of ``tax_domain``."""
        self.ensure_one()
        return self[f"{tax_domain}_cst_id"]

    def _resolve_tax_creditability(self, tax_domain):
        """Whether this line may credit ``tax_domain``.

        All three gates must allow it: the BUYER regime, the DESTINATION
        of the goods (CFOP) and the NATURE of the operation (the CST).
        """
        self.ensure_one()
        if tax_domain not in CREDITABLE_TAX_DOMAINS:
            return False
        if not self._tax_credit_gates_allow(tax_domain):
            return False
        return bool(self._get_creditability_cst(tax_domain).default_creditable_tax)

    def _get_tax_creditability_map(self):
        """Which taxes of an incoming line are a credit and which a cost,
        derived from the tax rules at call time, never stored.

        A line that is not an entry, or has no CFOP, reports every tax as a
        credit, as the books always did.

        :return: {tax_domain: 'credit' | 'cost'} for icms, ipi, pis, cofins
        """
        self.ensure_one()
        if self.cfop_id.type_in_out != FISCAL_IN:
            return dict.fromkeys(CREDITABLE_TAX_DOMAINS, "credit")
        return {
            domain: "credit" if self._resolve_tax_creditability(domain) else "cost"
            for domain in CREDITABLE_TAX_DOMAINS
        }
