# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from brazilfiscalreport.danfe import (
    DanfeEtiqueta,
    DanfeEtiquetaConfig,
    FontType,
    Margins,
)

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase

ETIQUETA_CLASS = "odoo.addons.l10n_br_nfe.report.ir_actions_report.DanfeEtiqueta"


class TestDanfeEtiqueta(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.nfe = cls.env.ref("l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11")
        cls.report = cls.env["ir.actions.report"].search(
            [("report_name", "=", "main_template_danfe_etiqueta")]
        )

    def _print_etiqueta(self):
        """Print the label, returning the config handed to brazilfiscalreport."""
        with patch(ETIQUETA_CLASS, wraps=DanfeEtiqueta) as etiqueta_class:
            pdf, report_type = self.report._render_qweb_pdf(
                "main_template_danfe_etiqueta", [self.nfe.id]
            )
        self.assertEqual(report_type, "pdf")
        self.assertTrue(pdf.startswith(b"%PDF"))
        return etiqueta_class.call_args.kwargs["config"]

    def test_generate_etiqueta(self):
        self.nfe.action_document_confirm()
        self._print_etiqueta()

    def test_generate_etiqueta_document_type_error(self):
        self.nfe.document_type_id = self.env.ref("l10n_br_fiscal.document_01")
        self.nfe.action_document_confirm()
        with self.assertRaises(UserError) as captured_exception:
            self.report._render_qweb_pdf("main_template_danfe_etiqueta", [self.nfe.id])
        self.assertEqual(
            captured_exception.exception.args[0],
            "You can only print a DANFE Simplificado - Etiqueta of a NFe(55).",
        )

    def test_generate_etiqueta_without_xml_error(self):
        with self.assertRaises(UserError) as captured_exception:
            self.report._render_qweb_pdf("main_template_danfe_etiqueta", [self.nfe.id])
        self.assertEqual(captured_exception.exception.args[0], "No xml file was found.")

    def test_etiqueta_default_options(self):
        """The default profile, or no profile at all, keeps the library defaults."""
        self.nfe.action_document_confirm()
        default_profile = self.env.ref("l10n_br_nfe.danfe_profile_default")
        for profile in (default_profile, default_profile.browse()):
            self.nfe.company_id.danfe_profile_id = profile
            self.assertEqual(self._print_etiqueta(), DanfeEtiquetaConfig())

    def test_etiqueta_profile_options(self):
        self.nfe.company_id.danfe_profile_id = self.env[
            "l10n_br_nfe.danfe.profile"
        ].create(
            {
                "name": "Full Label",
                "font_type": "courier",
                "etiqueta_paper_width": 80,
                "etiqueta_paper_height": 120,
                "etiqueta_margin_top": 1,
                "etiqueta_margin_right": 2,
                "etiqueta_margin_bottom": 3,
                "etiqueta_margin_left": 4,
                "etiqueta_display_total": False,
                "etiqueta_display_delivery_address": False,
                "etiqueta_display_items": True,
            }
        )
        self.nfe.action_document_confirm()

        config = self._print_etiqueta()

        self.assertEqual(config.paper_width, 80)
        self.assertEqual(config.paper_height, 120)
        self.assertEqual(config.margins, Margins(top=1, right=2, bottom=3, left=4))
        self.assertEqual(config.font_type, FontType.COURIER)
        self.assertFalse(config.display_total)
        self.assertFalse(config.display_delivery_address)
        self.assertTrue(config.display_items)

    def test_etiqueta_min_paper_width(self):
        with self.assertRaises(ValidationError):
            self.env["l10n_br_nfe.danfe.profile"].create(
                {"name": "Too Narrow", "etiqueta_paper_width": 54}
            )

    def test_etiqueta_cancelled_watermark(self):
        self.nfe.action_document_confirm()
        self.nfe._trigger_fsm("action_authorize")
        self.assertFalse(self._print_etiqueta().watermark_cancelled)

        self.nfe.state_edoc = "cancelada"
        self.assertTrue(self._print_etiqueta().watermark_cancelled)
