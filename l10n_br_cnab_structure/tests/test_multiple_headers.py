# Copyright (C) 2025 Escodoo (https://www.escodoo.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form
from odoo.tests.common import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestCNABMultipleHeaders(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(
        cls, chart_template_ref="l10n_br_coa_generic.l10n_br_coa_generic_template"
    ):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.bank_001 = cls.env.ref("l10n_br_base.res_bank_001")

    def test_multiple_batch_headers(self):
        # Create a CNAB Structure
        cnab_structure_form = Form(self.env["l10n_br_cnab.structure"])
        cnab_structure_form.payment_method_id = self.env.ref(
            "l10n_br_account_payment_order.payment_mode_type_cnab240_out"
        )
        cnab_structure_form.name = "Test Multiple Headers"
        cnab_structure_form.bank_id = self.bank_001

        # Create Batch
        with cnab_structure_form.batch_ids.new() as batch_form:
            batch_form.name = "Batch 1"

        cnab_structure = cnab_structure_form.save()
        batch = cnab_structure.batch_ids[0]

        # Clean up any existing lines to avoid unique constraint errors
        cnab_structure.line_ids.unlink()

        # 1. File Header
        self.env["l10n_br_cnab.line"].create(
            {
                "cnab_structure_id": cnab_structure.id,
                "type": "header",
                "name": "File Header",
                "sequence": 1,
                "communication_flow": "both",
            }
        )

        # 2. Batch Header 1
        self.env["l10n_br_cnab.line"].create(
            {
                "cnab_structure_id": cnab_structure.id,
                "batch_id": batch.id,
                "type": "header",
                "name": "Batch Header 1",
                "sequence": 2,
                "communication_flow": "both",
            }
        )

        # 3. Batch Header 2
        self.env["l10n_br_cnab.line"].create(
            {
                "cnab_structure_id": cnab_structure.id,
                "batch_id": batch.id,
                "type": "header",
                "name": "Batch Header 2",
                "sequence": 3,
                "communication_flow": "both",
            }
        )

        # 4. Segment
        self.env["l10n_br_cnab.line"].create(
            {
                "cnab_structure_id": cnab_structure.id,
                "batch_id": batch.id,
                "type": "segment",
                "name": "Segment A",
                "sequence": 4,
                "communication_flow": "both",
            }
        )

        # 5. Batch Trailer
        self.env["l10n_br_cnab.line"].create(
            {
                "cnab_structure_id": cnab_structure.id,
                "batch_id": batch.id,
                "type": "trailer",
                "name": "Batch Trailer",
                "sequence": 5,
                "communication_flow": "both",
            }
        )

        # 6. File Trailer
        self.env["l10n_br_cnab.line"].create(
            {
                "cnab_structure_id": cnab_structure.id,
                "type": "trailer",
                "name": "File Trailer",
                "sequence": 6,
                "communication_flow": "both",
            }
        )

        # Validate Batch Check
        # This should pass now with multiple headers
        batch.check_batch()

        # Verify that we have 2 header lines for this batch
        header_lines = batch.line_ids.filtered(lambda line: line.type == "header")
        self.assertEqual(len(header_lines), 2)
