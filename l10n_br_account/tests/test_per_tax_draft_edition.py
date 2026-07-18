# Copyright 2026 - TODAY KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import Form

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestPerTaxDraftEdition(AccountMoveBRCommon):
    """Per-tax value regression suite for DRAFT invoice-line editing.

    These tests pin the behaviour that, while an ``out_invoice`` is still in
    draft and edited through a ``Form`` (the UI path, i.e. the full per-line
    onchange cascade), the stored fiscal value fields track the *true* line
    inputs:

      (a) overriding a per-tax selector (``icms_tax_id``, ``ipi_tax_id`` ...)
          makes base/percent/value recompute with the NEW tax rate;
      (b) changing ``quantity`` / ``price_unit`` rescales the values;
      (c) changing ``fiscal_operation_line_id`` remaps CFOP and taxes.

    They guard the #4721 class of regressions, where a draft fiscal value could
    be left stale -- e.g. ICMS stuck at the mapped rate after the user selected
    another tax. Assertions are relationship based (value == base * rate) so
    they hold regardless of the company-specific mapped rates.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.configure_normal_company_taxes()
        nfe_group = cls.env.ref("l10n_br_nfe.group_user", raise_if_not_found=False)
        if nfe_group:
            cls.env.user.write({"groups_id": [Command.link(nfe_group.id)]})
        cls.currency = cls.company_data["currency"]
        cls.document_55 = cls.env.ref("l10n_br_fiscal.document_55")
        cls.fo_venda = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.fo_venda_venda = cls.env.ref("l10n_br_fiscal.fo_venda_venda")
        cls.fo_venda_revenda = cls.env.ref("l10n_br_fiscal.fo_venda_revenda")
        cls.tax_icms_7 = cls.env.ref("l10n_br_fiscal.tax_icms_7")
        cls.tax_icms_18 = cls.env.ref("l10n_br_fiscal.tax_icms_18")
        cls.tax_ipi_10 = cls.env.ref("l10n_br_fiscal.tax_ipi_10")
        cls.tax_pis_1_65 = cls.env.ref("l10n_br_fiscal.tax_pis_1_65")
        cls.tax_cofins_7_6 = cls.env.ref("l10n_br_fiscal.tax_cofins_7_6")

    # ------------------------------------------------------------------ helpers

    def _invoice_form(self):
        """A draft out_invoice Form with the fiscal header already filled in."""
        move_form = Form(
            self.env["account.move"].with_context(default_move_type="out_invoice")
        )
        move_form.partner_id = self.partner_a
        move_form.document_type_id = self.document_55
        move_form.document_serie_id = self.empresa_lc_document_55_serie_1
        move_form.fiscal_operation_id = self.fo_venda
        return move_form

    def _init_line(self, line, price_unit=1000.0, quantity=1.0):
        line.product_id = self.product_a
        line.fiscal_operation_line_id = self.fo_venda_venda
        line.price_unit = price_unit
        line.quantity = quantity

    def _assert_value_tracks_rate(self, line, domain, percent, msg=""):
        """Assert ``<domain>_value == round(<domain>_base * percent / 100)`` and
        that ``<domain>_percent`` equals ``percent`` (non-reduced taxes)."""
        base = getattr(line, f"{domain}_base")
        value = getattr(line, f"{domain}_value")
        self.assertAlmostEqual(
            getattr(line, f"{domain}_percent"),
            percent,
            places=2,
            msg=f"{domain} percent mismatch {msg}",
        )
        expected = self.currency.round(base * percent / 100.0)
        self.assertAlmostEqual(
            value,
            expected,
            places=2,
            msg=f"{domain} value {value} != base {base} * {percent}% {msg}",
        )

    # ------------------------------------------------------------------- (a) tax

    def test_draft_icms_tax_id_override(self):
        """Overriding icms_tax_id in draft recomputes icms_value with the new
        rate (the exact #4721 scenario, in the full view payload)."""
        move_form = self._invoice_form()
        with move_form.invoice_line_ids.new() as line:
            self._init_line(line)
            initial_percent = line.icms_percent
            # sanity: the mapped ICMS is computed and self-consistent
            self._assert_value_tracks_rate(line, "icms", initial_percent, "(mapped)")

            line.icms_tax_id = self.tax_icms_18
            self._assert_value_tracks_rate(line, "icms", 18.0, "(after ->18%)")

            line.icms_tax_id = self.tax_icms_7
            self._assert_value_tracks_rate(line, "icms", 7.0, "(after ->7%)")

    def test_draft_ipi_tax_id_override(self):
        move_form = self._invoice_form()
        with move_form.invoice_line_ids.new() as line:
            self._init_line(line)
            line.ipi_tax_id = self.tax_ipi_10
            self._assert_value_tracks_rate(line, "ipi", 10.0, "(after ->10%)")

    def test_draft_pis_tax_id_override(self):
        move_form = self._invoice_form()
        with move_form.invoice_line_ids.new() as line:
            self._init_line(line)
            line.pis_tax_id = self.tax_pis_1_65
            self._assert_value_tracks_rate(line, "pis", 1.65, "(after ->1.65%)")

    def test_draft_cofins_tax_id_override(self):
        move_form = self._invoice_form()
        with move_form.invoice_line_ids.new() as line:
            self._init_line(line)
            line.cofins_tax_id = self.tax_cofins_7_6
            self._assert_value_tracks_rate(line, "cofins", 7.6, "(after ->7.6%)")

    def test_draft_icms_override_survives_save(self):
        """The overridden rate must persist through save() to the posted-ready
        fiscal line (draft correctness must not depend on the view round-trip)."""
        move_form = self._invoice_form()
        with move_form.invoice_line_ids.new() as line:
            self._init_line(line)
            line.icms_tax_id = self.tax_icms_18
        move = move_form.save()
        fisc_line = move.fiscal_line_ids[0]
        self.assertEqual(fisc_line.icms_tax_id, self.tax_icms_18)
        self.assertAlmostEqual(fisc_line.icms_percent, 18.0, places=2)
        self.assertAlmostEqual(
            fisc_line.icms_value,
            self.currency.round(fisc_line.icms_base * 0.18),
            places=2,
        )

    # ---------------------------------------------------------- (b) qty / price

    def test_draft_quantity_edition(self):
        move_form = self._invoice_form()
        with move_form.invoice_line_ids.new() as line:
            self._init_line(line, price_unit=1000.0, quantity=1.0)
            percent = line.icms_percent
            self._assert_value_tracks_rate(line, "icms", percent, "(qty=1)")
            base_1 = line.icms_base

            line.quantity = 3.0
            self._assert_value_tracks_rate(line, "icms", percent, "(qty=3)")
            self.assertAlmostEqual(line.icms_base, base_1 * 3.0, places=2)

    def test_draft_price_unit_edition(self):
        move_form = self._invoice_form()
        with move_form.invoice_line_ids.new() as line:
            self._init_line(line, price_unit=1000.0, quantity=1.0)
            percent = line.icms_percent
            base_1000 = line.icms_base

            line.price_unit = 2500.0
            self._assert_value_tracks_rate(line, "icms", percent, "(price=2500)")
            self.assertAlmostEqual(line.icms_base, base_1000 * 2.5, places=2)

    # -------------------------------------------------- (c) operation line remap

    def test_draft_fiscal_operation_line_remap(self):
        """Changing fiscal_operation_line_id in draft remaps CFOP and taxes."""
        move_form = self._invoice_form()
        with move_form.invoice_line_ids.new() as line:
            self._init_line(line)
            cfop_before = line.cfop_id
            self.assertTrue(cfop_before, "mapped CFOP expected for venda_venda")

            line.fiscal_operation_line_id = self.fo_venda_revenda
            cfop_after = line.cfop_id
            self.assertTrue(cfop_after, "mapped CFOP expected for venda_revenda")
            # produção (5101) vs revenda (5102): the CFOP must be remapped
            self.assertNotEqual(
                cfop_before,
                cfop_after,
                "CFOP must be remapped when the fiscal operation line changes",
            )
            # taxes remain consistent with the new mapping
            self.assertTrue(line.fiscal_tax_ids, "taxes must be remapped")
            self._assert_value_tracks_rate(
                line, "icms", line.icms_percent, "(after op-line remap)"
            )
