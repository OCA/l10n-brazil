# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo.tests import tagged

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestOtherDocumentTypes(AccountMoveBRCommon):
    """With the NF-e installed, the invoice of another type of document (here an
    NFS-e) must neither read nor write the tags of the NF-e."""

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.configure_normal_company_taxes()
        document_type = cls.env.ref("l10n_br_fiscal.document_SE")
        cls.serie = cls.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "001",
                "name": "Series 1",
                "document_type_id": document_type.id,
                "company_id": cls.company_data["company"].id,
            }
        )
        cls.service = cls.env["product.product"].create(
            {
                "name": "Service",
                "type": "service",
                "tax_icms_or_issqn": "issqn",
            }
        )
        cls.move = cls.init_invoice(
            "out_invoice",
            products=[cls.service],
            document_type=document_type,
            document_serie_id=cls.serie,
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[cls.env.ref("l10n_br_fiscal.fo_venda_servico")],
        )
        cls.move.invoice_payment_term_id = cls.env["account.payment.term"].create(
            {"name": "30 days", "line_ids": [(0, 0, {"value": "balance", "days": 30})]}
        )

    def _tags_cannot_be_read(self):
        """The tags of the NF-e are not a thing of this document: reading one fails
        as it does when the spec model is not a concrete one (nothing to read)."""
        model = type(self.move.fiscal_document_id)
        return [
            mock.patch.object(
                model, name, new_callable=mock.PropertyMock, side_effect=ValueError
            )
            for name in ("nfe40_dup", "nfe40_detPag")
        ]

    def test_the_invoice_of_an_nfse_is_posted_and_cancelled(self):
        self.assertEqual(self.move.document_type_id.code, "SE")
        patches = self._tags_cannot_be_read()
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

        self.move.action_post()

        self.assertEqual(self.move.state, "posted")
        document = self.move.fiscal_document_id
        self.assertEqual(document._edi_get_installments(), [])
        self.assertEqual(document._edi_get_payments(), [])
        self.assertFalse(document.edi_payment_summary)
        self.move.button_cancel()
        self.assertEqual(self.move.state, "cancel")
