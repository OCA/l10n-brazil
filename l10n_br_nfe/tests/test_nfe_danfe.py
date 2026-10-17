# Copyright 2024 Engenere.one
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from brazilfiscalreport.danfe import (
    Danfe,
    DanfeConfig,
    DecimalConfig,
    FontSize,
    FontType,
    InvoiceDisplay,
    Margins,
    ProductDescriptionConfig,
    ReceiptPosition,
)

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

DANFE_CLASS = "odoo.addons.l10n_br_nfe.report.ir_actions_report.Danfe"

# 1x1 PNG
FOOTER_STAMP_LOGO = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAA"
    "AABJRU5ErkJggg=="
)


class TestDanfeGeneration(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.nfe = cls.env.ref("l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11")
        cls.default_profile = cls.env.ref("l10n_br_nfe.danfe_profile_default")

    def _print_danfe(self):
        """Print the DANFE, returning the config handed to brazilfiscalreport."""
        with patch(DANFE_CLASS, wraps=Danfe) as danfe_class:
            self.nfe.make_pdf()
        self.assertTrue(self.nfe.file_report_id)
        return danfe_class.call_args.kwargs["config"]

    def test_generate_danfe_brazil_fiscal_report(self):
        nfe = self.env.ref("l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11")
        nfe.action_document_confirm()
        nfe.view_pdf()
        self.assertTrue(nfe.file_report_id)

    def test_generate_danfe_document_type_error(self):
        danfe_report = self.env["ir.actions.report"].search(
            [("report_name", "=", "main_template_danfe")]
        )
        nfe = self.env.ref("l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11")
        nfe.document_type_id = self.env.ref("l10n_br_fiscal.document_01")
        nfe.action_document_confirm()
        with self.assertRaises(UserError) as captured_exception:
            danfe_report._render_qweb_pdf("main_template_danfe", [nfe.id])
        self.assertEqual(
            captured_exception.exception.args[0],
            "You can only print a DANFE of a NFe(55).",
        )

    def test_generate_danfe_brazil_fiscal_report_partner(self):
        nfe = self.env.ref("l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11")
        nfe.action_document_confirm()
        nfe.with_context(skip_edoc_lock=True).issuer = "partner"
        nfe.view_pdf()
        self.assertTrue(nfe.file_report_id)

    def test_generate_danfe_after_authorization(self):
        """The DANFE must be generated automatically upon authorization.

        Regression test: the legacy _exec_after_SITUACAO_EDOC_AUTORIZADA
        hook that generated it became dead code with the FSM refactor.
        """
        nfe = self.env.ref("l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11")
        nfe.action_document_confirm()
        self.assertFalse(nfe.file_report_id)
        nfe._trigger_fsm("action_authorize")
        self.assertTrue(nfe.file_report_id)

    def test_danfe_default_options(self):
        """The default profile, or no profile at all, keeps the library defaults."""
        self.nfe.action_document_confirm()
        for profile in (self.default_profile, self.default_profile.browse()):
            self.nfe.company_id.danfe_profile_id = profile
            config = self._print_danfe()
            self.assertEqual(config, DanfeConfig(logo=config.logo))

    def test_danfe_profile_options(self):
        self.nfe.company_id.danfe_profile_id = self.env[
            "l10n_br_nfe.danfe.profile"
        ].create(
            {
                "name": "Carrier Receipt",
                "invoice_display": "duplicates_only",
                "display_pis_cofins": True,
                "margin_top": 1,
                "margin_right": 2,
                "margin_bottom": 3,
                "margin_left": 4,
                "receipt_position": "bottom",
                "carrier_receipt": True,
                "font_type": "courier",
                "font_size": "big",
                "price_precision": 2,
                "quantity_precision": 3,
                "infcpl_semicolon_newline": True,
                "display_product_additional_info": False,
                "display_lot": True,
                "lot_prefix": "Rastro",
                "display_anp": True,
                "display_anvisa": True,
                "footer_stamp_logo": FOOTER_STAMP_LOGO,
                "footer_stamp_text": "Printed by Odoo",
            }
        )
        self.nfe.action_document_confirm()

        config = self._print_danfe()

        self.assertEqual(config.invoice_display, InvoiceDisplay.DUPLICATES_ONLY)
        self.assertTrue(config.display_pis_cofins)
        self.assertEqual(config.margins, Margins(top=1, right=2, bottom=3, left=4))
        self.assertEqual(config.receipt_pos, ReceiptPosition.BOTTOM)
        self.assertTrue(config.carrier_receipt)
        self.assertEqual(config.font_type, FontType.COURIER)
        self.assertEqual(config.font_size, FontSize.BIG)
        self.assertEqual(
            config.decimal_config,
            DecimalConfig(price_precision=2, quantity_precision=3),
        )
        self.assertTrue(config.infcpl_semicolon_newline)
        self.assertEqual(
            config.product_description_config,
            ProductDescriptionConfig(
                display_branch=True,
                display_anp=True,
                display_anvisa=True,
                branch_info_prefix="Rastro",
                display_additional_info=False,
            ),
        )
        self.assertTrue(config.footer_stamp.logo)
        self.assertEqual(config.footer_stamp.text, "Printed by Odoo")

    def test_danfe_profile_companies(self):
        """A company is in a single profile: adding it to one removes it from the
        other, and removing it falls back to the default profile."""
        company = self.nfe.company_id
        company.danfe_profile_id = self.default_profile
        profile = self.env["l10n_br_nfe.danfe.profile"].create({"name": "Other"})
        self.assertIn(company, self.default_profile.company_ids)

        profile.company_ids = company
        self.assertEqual(company.danfe_profile_id, profile)
        self.default_profile.invalidate_recordset(["company_ids"])
        self.assertNotIn(company, self.default_profile.company_ids)

        profile.company_ids = False
        self.assertEqual(company.danfe_profile_id, self.default_profile)

    def test_danfe_new_company_default_profile(self):
        company = self.env["res.company"].create({"name": "DANFE Company"})
        self.assertEqual(company.danfe_profile_id, self.default_profile)

    def test_danfe_cancelled_watermark(self):
        self.nfe.action_document_confirm()
        self.nfe._trigger_fsm("action_authorize")
        self.assertFalse(self._print_danfe().watermark_cancelled)

        self.nfe.state_edoc = "cancelada"
        self.assertTrue(self._print_danfe().watermark_cancelled)

    def test_danfe_printed_again_on_cancel(self):
        """The DANFE printed at the authorization gets the cancellation watermark."""
        self.nfe.action_document_confirm()
        self.nfe._trigger_fsm("action_authorize")
        authorized_danfe = self.nfe.file_report_id

        # Skip the SEFAZ cancellation event
        with patch.object(type(self.nfe), "_nfe_cancel"), patch(
            DANFE_CLASS, wraps=Danfe
        ) as danfe_class:
            self.nfe._document_cancel("Cancellation for the DANFE test")

        self.assertEqual(self.nfe.state_edoc, "cancelada")
        self.assertNotEqual(self.nfe.file_report_id, authorized_danfe)
        self.assertTrue(danfe_class.call_args.kwargs["config"].watermark_cancelled)
