# Copyright (C) 2022 - Engenere (<https://engenere.one>).
# Copyright (C) 2025 Escodoo (https://www.escodoo.com.br)
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import base64
import tempfile
from pathlib import Path

from odoo import fields
from odoo.tests import Form
from odoo.tests.common import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


# Help function
def replace_chars(string, index, replacement):
    return string[:index] + replacement + string[index + len(replacement) :]


@tagged("post_install", "-at_install")
class TestCNABStructure(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(
        cls, chart_template_ref="l10n_br_coa_generic.l10n_br_coa_generic_template"
    ):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.company_data["company"]
        cls.company.update({"cnpj_cpf": "82688625000152"})
        cls.env.user.company_id = cls.company.id
        cls.res_partner_bank_model = cls.env["res.partner.bank"]
        cls.payment_mode_model = cls.env["account.payment.mode"]
        cls.payment_order_model = cls.env["account.payment.order"]
        cls.payment_line_model = cls.env["account.payment.line"]
        cls.attachment_model = cls.env["ir.attachment"]
        cls.account_payment_method_model = cls.env["account.payment.method"]
        cls.res_partner_pix_model = cls.env["res.partner.pix"]
        cls.bank_341 = cls.env.ref("l10n_br_base.res_bank_341")
        cls.bank_001 = cls.env.ref("l10n_br_base.res_bank_001")
        cls.import_wizard_obj = cls.env["cnab.import.wizard"]
        cls.cnab_log_obj = cls.env["l10n_br_cnab.return.log"]
        cls.partner_a.update({"cnpj_cpf": "45823449000198"})
        cls.cnab_structure_itau_240 = cls.env.ref(
            "l10n_br_cnab_structure.cnab_itau_240"
        )
        cls.cnab_structure_bb_240 = cls.env.ref("l10n_br_cnab_structure.cnab_bb_240")
        cls.res_partner_pix_model.create(
            {
                "partner_id": cls.partner_a.id,
                "key_type": "phone",
                "key": "+50372424737",
            }
        )
        cls.itau_bank_account = cls.res_partner_bank_model.create(
            {
                "acc_number": "205040",
                "bra_number": "1030",
                "bank_id": cls.bank_341.id,
                "company_id": cls.company.id,
                "partner_id": cls.company.partner_id.id,
            }
        )
        cls.bank_journal_itau = cls.env["account.journal"].create(
            {
                "name": "Itau Bank",
                "type": "bank",
                "code": "BNK_ITAU",
                "bank_account_id": cls.itau_bank_account.id,
                "bank_id": cls.bank_341.id,
            }
        )
        cls.bb_bank_account = cls.res_partner_bank_model.create(
            {
                "acc_number": "12345",  # Example BB account number
                "bra_number": "1234",  # Example BB branch number
                "bank_id": cls.bank_001.id,
                "company_id": cls.company.id,
                "partner_id": cls.company.partner_id.id,
            }
        )
        cls.bank_journal_bb = cls.env["account.journal"].create(
            {
                "name": "BB Bank",
                "type": "bank",
                "code": "BNK_BB",
                "bank_account_id": cls.bb_bank_account.id,
                "bank_id": cls.bank_001.id,
            }
        )
        cls.outbound_payment_method = cls.env.ref(
            "l10n_br_account_payment_order.payment_mode_type_cnab240_out"
        )
        cls.pix_mode = cls.payment_mode_model.create(
            {
                "bank_account_link": "fixed",
                "name": "Pix Transfer",
                "company_id": cls.company.id,
                "payment_method_id": cls.outbound_payment_method.id,
                "payment_mode_domain": "pix_transfer",
                "payment_order_ok": True,
                "fixed_journal_id": cls.bank_journal_itau.id,
                "cnab_processor": "oca_processor",
                "cnab_structure_id": cls.cnab_structure_itau_240.id,
                "cnab_payment_way_ids": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref(
                                "l10n_br_cnab_structure.cnab_itau_240_pay_way_45"
                            ).id
                        ],
                    )
                ],
            }
        )
        cls.pix_mode_bb = cls.payment_mode_model.create(
            {
                "bank_account_link": "fixed",
                "name": "Pix Transfer BB",
                "company_id": cls.company.id,
                "payment_method_id": cls.outbound_payment_method.id,
                "payment_mode_domain": "pix_transfer",
                "payment_order_ok": True,
                "fixed_journal_id": cls.bank_journal_bb.id,
                "cnab_processor": "oca_processor",
                "cnab_structure_id": cls.cnab_structure_bb_240.id,
                "cnab_payment_way_ids": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref(
                                "l10n_br_cnab_structure.cnab_bb_240_pay_way_45"
                            ).id
                        ],
                    )
                ],
            }
        )
        cls.invoice = cls.env["account.move"].create(
            {
                "partner_id": cls.partner_a.id,
                "move_type": "in_invoice",
                "ref": "Test Bill Invoice 1",
                "invoice_date": fields.Date.today(),
                "company_id": cls.company.id,
                "payment_mode_id": cls.pix_mode.id,
                "journal_id": cls.company_data["default_journal_purchase"].id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_a.id,
                            "quantity": 1.0,
                            "price_unit": 300.0,
                        },
                    )
                ],
            }
        )
        # Make sure no other payment orders are in the DB
        cls.domain = [
            ("state", "=", "draft"),
            ("payment_type", "=", "outbound"),
            ("company_id", "=", cls.company.id),
        ]
        cls.payment_order_model.search(cls.domain).unlink()

    def test_file_generete_and_return(self):
        payment_order_id = self._create_and_get_payment_order()
        self.assertEqual(len(payment_order_id), 1)
        # Open payment order
        payment_order_id.draft2open()
        action = payment_order_id.open2generated()
        delivery_cnab_file = self.attachment_model.browse(action["res_id"])
        self.assertIsNotNone(delivery_cnab_file)

        # Transform the send file (remessa) into a return file (retorno)
        cnab_data = base64.b64decode(delivery_cnab_file.datas).decode()
        lines = cnab_data.splitlines()
        # payment effective date
        lines[2] = replace_chars(lines[2], 154, "10112022")
        # actual payment amount
        lines[2] = replace_chars(lines[2], 172, "300")
        # occurrence
        lines[2] = replace_chars(lines[2], 230, "00")

        return_data = "\r\n".join(lines).encode()

        import_wizard = self.import_wizard_obj.create(
            {
                "journal_id": self.bank_journal_itau.id,
                "return_file": base64.b64encode(return_data),
                "filename": "TEST.RET",
                "type": "outbound",
                "cnab_structure_id": self.cnab_structure_itau_240.id,
            }
        )
        action = import_wizard.with_context(default_type="outbound").import_cnab()
        cnab_log = self.cnab_log_obj.browse(action["res_id"])

        self.assertIsNotNone(cnab_log)
        self.assertFalse(cnab_log.event_ids.mapped("generated_move_id"))

        cnab_log.action_confirm_return_log()

        self.assertTrue(cnab_log.event_ids.mapped("generated_move_id"))

    def test_cnab_yaml_output(self):
        payment_order_id = self._create_and_get_payment_order()
        preview_wizard_obj = self.env["cnab.preview.wizard"]
        preview_wizard = preview_wizard_obj.create(
            {
                "payment_order_id": payment_order_id.id,
                "cnab_structure_id": self.cnab_structure_itau_240.id,
            }
        )
        self.assertIsNotNone(preview_wizard.output_yaml)
        self.assertIn(
            "    103_132_nome_do_banco: 'BANCO ITAU                    '\n",
            preview_wizard.output_yaml,
        )

    def _create_and_get_payment_order(self):
        # Open invoice
        self.invoice.action_post()
        # Add to payment order using the wizard
        self.env["account.invoice.payment.line.multi"].with_context(
            active_model="account.move", active_ids=self.invoice.ids
        ).create({}).run()
        payment_order_id = self.env["account.payment.order"].search(self.domain)
        return payment_order_id

    def _create_valid_cnab_structure(self):
        cnab_structure_form = Form(self.env["l10n_br_cnab.structure"])
        cnab_structure_form.payment_method_id = self.env.ref(
            "l10n_br_account_payment_order.payment_mode_type_cnab240_out"
        )
        cnab_structure_form.name = "Test CNAB Structure"
        cnab_structure_form.bank_id = self.bank_341
        # BATCH
        with cnab_structure_form.batch_ids.new() as batch_form:
            batch_form.name = "Test Batch 1"
        cnab_structure = cnab_structure_form.save()

        # FILE HEADER
        line_form = Form(
            self.env["l10n_br_cnab.line"],
            view="l10n_br_cnab_structure.cnab_line_form_view",
        )
        line_form.cnab_structure_id = cnab_structure
        line_form.type = "header"
        line_form.communication_flow = "both"
        with line_form.field_ids.new() as field_form:
            field_form.start_pos = 1
            field_form.end_pos = 240
        line_form.save()

        # BATCH HEADER
        line_form = Form(
            self.env["l10n_br_cnab.line"],
            view="l10n_br_cnab_structure.cnab_line_form_view",
        )
        line_form.cnab_structure_id = cnab_structure
        line_form.batch_id = cnab_structure.batch_ids[0]
        line_form.type = "header"
        line_form.communication_flow = "both"
        with line_form.field_ids.new() as field_form:
            field_form.start_pos = 1
            field_form.end_pos = 240
        line_form.save()

        # BATCH SEGMENT
        line_form = Form(
            self.env["l10n_br_cnab.line"],
            view="l10n_br_cnab_structure.cnab_line_form_view",
        )
        line_form.cnab_structure_id = cnab_structure
        line_form.batch_id = cnab_structure.batch_ids[0]
        line_form.type = "segment"
        line_form.segment_code = "X"
        line_form.communication_flow = "both"
        with line_form.field_ids.new() as field_form:
            field_form.start_pos = 1
            field_form.end_pos = 240
        line_form.save()

        # BATCH TRAILER
        line_form = Form(
            self.env["l10n_br_cnab.line"],
            view="l10n_br_cnab_structure.cnab_line_form_view",
        )
        line_form.cnab_structure_id = cnab_structure
        line_form.batch_id = cnab_structure.batch_ids[0]
        line_form.type = "trailer"
        line_form.communication_flow = "both"
        with line_form.field_ids.new() as field_form:
            field_form.start_pos = 1
            field_form.end_pos = 240
        line_form.save()

        # FILE TRAILER
        line_form = Form(
            self.env["l10n_br_cnab.line"],
            view="l10n_br_cnab_structure.cnab_line_form_view",
        )
        line_form.cnab_structure_id = cnab_structure
        line_form.type = "trailer"
        line_form.communication_flow = "both"
        with line_form.field_ids.new() as field_form:
            field_form.start_pos = 1
            field_form.end_pos = 240
        line_form.save()
        return cnab_structure

    def test_cnab_structure_240_outbound(self):
        cnab_structure_form = Form(self.env["l10n_br_cnab.structure"])
        cnab_structure_form.payment_method_id = self.env.ref(
            "l10n_br_account_payment_order.payment_mode_type_cnab240_out"
        )
        cnab_structure = cnab_structure_form.save()
        self.assertTrue(cnab_structure)
        self.assertEqual(cnab_structure.conf_bank_start_pos, 1)
        self.assertEqual(cnab_structure.conf_bank_end_pos, 3)
        self.assertEqual(cnab_structure.conf_record_type_start_pos, 8)
        self.assertEqual(cnab_structure.conf_record_type_end_pos, 8)
        self.assertEqual(cnab_structure.conf_batch_start_pos, 4)
        self.assertEqual(cnab_structure.conf_bank_start_pos, 1)
        self.assertEqual(cnab_structure.conf_batch_end_pos, 7)
        self.assertEqual(cnab_structure.conf_payment_way_start_pos, 12)
        self.assertEqual(cnab_structure.conf_payment_way_end_pos, 13)
        self.assertEqual(cnab_structure.record_type_file_header_id, 0)
        self.assertEqual(cnab_structure.record_type_file_trailer_id, 9)
        self.assertEqual(cnab_structure.record_type_batch_header_id, 1)
        self.assertEqual(cnab_structure.record_type_batch_trailer_id, 5)
        self.assertEqual(cnab_structure.record_type_detail_id, 3)

    def test_cnab_structure_240_inbound(self):
        # Please note: support for CNAB 240 inbound is not fully implemented.
        cnab_structure_form = Form(self.env["l10n_br_cnab.structure"])
        cnab_structure_form.payment_method_id = self.env.ref(
            "l10n_br_account_payment_order.payment_mode_type_cnab240"
        )
        cnab_structure = cnab_structure_form.save()
        self.assertTrue(cnab_structure)
        self.assertEqual(cnab_structure.conf_bank_start_pos, 1)
        self.assertEqual(cnab_structure.conf_bank_end_pos, 3)
        self.assertEqual(cnab_structure.conf_record_type_start_pos, 8)
        self.assertEqual(cnab_structure.conf_record_type_end_pos, 8)
        self.assertEqual(cnab_structure.conf_batch_start_pos, 4)
        self.assertEqual(cnab_structure.conf_bank_start_pos, 1)
        self.assertEqual(cnab_structure.conf_batch_end_pos, 7)
        self.assertEqual(cnab_structure.conf_payment_way_start_pos, 0)
        self.assertEqual(cnab_structure.conf_payment_way_end_pos, 0)
        self.assertEqual(cnab_structure.record_type_file_header_id, 0)
        self.assertEqual(cnab_structure.record_type_file_trailer_id, 9)
        self.assertEqual(cnab_structure.record_type_batch_header_id, 1)
        self.assertEqual(cnab_structure.record_type_batch_trailer_id, 5)
        self.assertEqual(cnab_structure.record_type_detail_id, 3)

    def test_cnab_structure_400_inbound(self):
        # Please note: support for CNAB 400 is not fully implemented.
        cnab_structure_form = Form(self.env["l10n_br_cnab.structure"])
        cnab_structure_form.payment_method_id = self.env.ref(
            "l10n_br_account_payment_order.payment_mode_type_cnab400"
        )
        cnab_structure = cnab_structure_form.save()
        self.assertTrue(cnab_structure)
        self.assertEqual(cnab_structure.conf_record_type_start_pos, 8)
        self.assertEqual(cnab_structure.conf_record_type_end_pos, 8)
        self.assertEqual(cnab_structure.record_type_file_trailer_id, 9)
        self.assertEqual(cnab_structure.record_type_detail_id, 1)

    def test_cnab_structure_500_inbound(self):
        # Please note: support for CNAB 500 is not fully implemented.
        cnab_structure_form = Form(self.env["l10n_br_cnab.structure"])
        cnab_structure_form.payment_method_id = self.env.ref(
            "l10n_br_account_payment_order.payment_mode_type_cnab500"
        )
        cnab_structure = cnab_structure_form.save()
        self.assertEqual(cnab_structure.conf_record_type_start_pos, 0)

    def test_cnab_structure_states(self):
        cnab_structure = self._create_valid_cnab_structure()
        self.assertEqual(cnab_structure.state, "draft")
        cnab_structure.action_review()
        self.assertEqual(cnab_structure.state, "review")
        cnab_structure.action_approve()
        self.assertEqual(cnab_structure.state, "approved")
        cnab_structure.action_draft()
        self.assertEqual(cnab_structure.state, "draft")

    def test_field_select_wizard(self):
        cnab_field_id = self._create_valid_cnab_structure().line_ids[0].field_ids[0]
        wiz_action = cnab_field_id.action_change_field_sending()

        self.assertEqual(wiz_action["res_model"], "field.select.wizard")
        self.assertEqual(wiz_action["target"], "new")
        self.assertEqual(wiz_action["type"], "ir.actions.act_window")
        self.assertEqual(wiz_action["view_mode"], "form")
        self.assertEqual(wiz_action["view_type"], "form")

        field_select_wizard = (
            self.env[wiz_action["res_model"]]
            .with_context(**wiz_action["context"])
            .create({})
        )

        def find_field(name):
            model = field_select_wizard.parent_model_id
            field = self.env["ir.model.fields"].search(
                [("model_id", "=", model.id), ("name", "=", name)]
            )
            return field

        # select and confirm new field in wizard
        self.assertFalse(field_select_wizard.notation_field)
        field_select_wizard.new_field_id = find_field("company_partner_bank_id")
        field_select_wizard._update_dot_notation()
        self.assertEqual(field_select_wizard.notation_field, "company_partner_bank_id")

        # select and confirm new sub-field in wizard
        field_select_wizard.new_field_id = find_field("bank_id")
        field_select_wizard._update_dot_notation()
        self.assertEqual(
            field_select_wizard.notation_field, "company_partner_bank_id.bank_id"
        )

        # remove sub-field in wizard
        field_select_wizard.action_remove_last_field()
        self.assertEqual(field_select_wizard.notation_field, "company_partner_bank_id")

        # confirm wizard
        self.assertFalse(cnab_field_id.content_source_field)
        field_select_wizard.action_confirm()
        self.assertEqual(cnab_field_id.content_source_field, "company_partner_bank_id")

    def test_file_generate_bb_seq_detail_with_temp_files(self):
        """Test BB 240 detail sequence with unique_seq_per_segment both False and True
        using temporary files to compare generated CNAB output.
        """
        # Create an invoice for Banco do Brasil (BB)
        invoice_bb = self.env["account.move"].create(
            {
                "partner_id": self.partner_a.id,
                "move_type": "in_invoice",
                "ref": "Test BB Invoice",
                "invoice_date": fields.Date.today(),
                "company_id": self.company.id,
                "payment_mode_id": self.pix_mode_bb.id,
                "journal_id": self.company_data["default_journal_purchase"].id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_a.id,
                            "quantity": 1.0,
                            "price_unit": 150.0,
                        },
                    )
                ],
            }
        )
        invoice_bb.action_post()

        # Add invoice to payment order
        self.env["account.invoice.payment.line.multi"].with_context(
            active_model="account.move", active_ids=invoice_bb.ids
        ).create({}).run()

        payment_order = self.env["account.payment.order"].search(
            [
                ("state", "=", "draft"),
                ("payment_type", "=", "outbound"),
                ("company_id", "=", self.company.id),
            ]
        )
        self.assertEqual(len(payment_order), 1)

        cnab_structure = self.cnab_structure_bb_240

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # --- Case 1: unique_seq_per_segment = False ---
            cnab_structure.unique_seq_per_segment = False
            payment_order.draft2open()
            action_false = payment_order.open2generated()
            cnab_file_false = self.attachment_model.browse(action_false["res_id"])
            cnab_data_false = base64.b64decode(cnab_file_false.datas).decode()

            tmp_file_false = tmp_path / "bb_seq_false.rem"
            tmp_file_false.write_text(cnab_data_false)

            # Check that all detail segment sequences are the same
            lines_false = cnab_data_false.splitlines()
            seqs_false = [line[8:13] for line in lines_false if line[7] == "3"]
            self.assertTrue(
                all(seq == seqs_false[0] for seq in seqs_false),
                "Sequences should be identical when unique_seq_per_segment = False",
            )

            # --- Case 2: unique_seq_per_segment = True ---
            cnab_structure.unique_seq_per_segment = True
            action_true = payment_order.open2generated()
            cnab_file_true = self.attachment_model.browse(action_true["res_id"])
            cnab_data_true = base64.b64decode(cnab_file_true.datas).decode()

            tmp_file_true = tmp_path / "bb_seq_true.rem"
            tmp_file_true.write_text(cnab_data_true)

            # Check that all detail segment sequences are unique and sorted
            lines_true = cnab_data_true.splitlines()
            seqs_true = [line[8:13] for line in lines_true if line[7] == "3"]
            self.assertEqual(seqs_true, sorted(seqs_true))
            self.assertEqual(len(seqs_true), len(set(seqs_true)))
