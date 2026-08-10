# Copyright (C) 2022 - Engenere (<https://engenere.one>).
# Copyright (C) 2025 Escodoo (https://www.escodoo.com.br)
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from pathlib import Path
from tempfile import TemporaryDirectory

from unidecode import unidecode

from odoo import fields
from odoo.tests import Form
from odoo.tests.common import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

CNAB_240 = "240"
CNAB_400 = "400"
CNAB_500 = "500"

POS_BANK_START = 1
POS_BANK_END = 3
POS_REC_TYPE = 8
POS_BATCH_START = 4
POS_BATCH_END = 7
POS_WAY_START = 12
POS_WAY_END = 13
POS_DETAIL_START = 9
POS_DETAIL_END = 13
POS_SEGMENT_START = 14
POS_SEGMENT_END = 14

REC_FILE_HEADER = 0
REC_BATCH_HEADER = 1
REC_DETAIL = 3
REC_BATCH_TRAILER = 5
REC_FILE_TRAILER = 9

PAY_WAY_SAME_BANK = "01"
PAY_WAY_OTHER_BANK = "41"

SVC_SUPPLIER = "20"
SVC_SALARY = "30"

TEST_CNPJ = "82688625000152"
TEST_PARTNER_CNPJ = "45823449000198"
TEST_INVOICE_AMOUNT = 300.0


def replace_chars(string: str, index: int, replacement: str) -> str:
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
        cls.company.update({"cnpj_cpf": TEST_CNPJ})
        cls.env.user.company_id = cls.company.id

        cls.res_partner_bank_model = cls.env["res.partner.bank"]
        cls.payment_mode_model = cls.env["account.payment.mode"]
        cls.payment_order_model = cls.env["account.payment.order"]
        cls.payment_line_model = cls.env["account.payment.line"]
        cls.attachment_model = cls.env["ir.attachment"]
        cls.res_partner_pix_model = cls.env["res.partner.pix"]

        cls.bank_341 = cls.env.ref("l10n_br_base.res_bank_341")
        cls.bank_001 = cls.env.ref("l10n_br_base.res_bank_001")
        cls.outbound_payment_method = cls.env.ref(
            "l10n_br_account_payment_order.payment_mode_type_cnab240_out"
        )

        cls.cnab_structure_itau_240 = cls.env.ref(
            "l10n_br_cnab_structure.cnab_itau_240"
        )
        cls.cnab_structure_bb_240 = cls.env.ref("l10n_br_cnab_structure.cnab_bb_240")

        cls._setup_partner_data()
        cls._setup_bank_accounts()
        cls._setup_payment_modes()
        cls._setup_pix_data()

    @classmethod
    def _setup_partner_data(cls):
        cls.partner_a.update({"cnpj_cpf": TEST_PARTNER_CNPJ})

        cls.partner_a_itau_bank = cls.res_partner_bank_model.create(
            {
                "acc_number": "123456",
                "bra_number": "0001",
                "bank_id": cls.bank_341.id,
                "partner_id": cls.partner_a.id,
            }
        )
        cls.partner_a_bb_bank = cls.res_partner_bank_model.create(
            {
                "acc_number": "789012",
                "bra_number": "0002",
                "bank_id": cls.bank_001.id,
                "partner_id": cls.partner_a.id,
            }
        )

    @classmethod
    def _setup_bank_accounts(cls):
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
                "acc_number": "12345",
                "bra_number": "1234",
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

    @classmethod
    def _setup_payment_modes(cls):
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

    @classmethod
    def _setup_pix_data(cls):
        cls.res_partner_pix_model.create(
            {
                "partner_id": cls.partner_a.id,
                "key_type": "phone",
                "key": "+50372424737",
            }
        )

    @classmethod
    def _create_test_invoice(cls, payment_mode=None, amount=TEST_INVOICE_AMOUNT):
        return cls.env["account.move"].create(
            {
                "partner_id": cls.partner_a.id,
                "move_type": "in_invoice",
                "ref": "Test Invoice",
                "invoice_date": fields.Date.today(),
                "company_id": cls.company.id,
                "payment_mode_id": (payment_mode or cls.pix_mode).id,
                "journal_id": cls.company_data["default_journal_purchase"].id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_a.id,
                            "quantity": 1.0,
                            "price_unit": amount,
                        },
                    )
                ],
            }
        )

    @classmethod
    def _create_payment_order(cls, invoice):
        invoice.action_post()
        cls.env["account.invoice.payment.line.multi"].with_context(
            active_model="account.move", active_ids=invoice.ids
        ).create({}).run()

        domain = [
            ("state", "=", "draft"),
            ("payment_type", "=", "outbound"),
            ("company_id", "=", cls.company.id),
        ]
        return cls.payment_order_model.search(domain)

    def _create_cnab_structure(self, name="Test CNAB", bank=None, payment_method=None):
        bank = bank or self.bank_341
        payment_method = payment_method or self.env.ref(
            "l10n_br_account_payment_order.payment_mode_type_cnab240_out"
        )

        cnab_structure_form = Form(self.env["l10n_br_cnab.structure"])
        cnab_structure_form.name = name
        cnab_structure_form.bank_id = bank
        cnab_structure_form.payment_method_id = payment_method
        return cnab_structure_form.save()

    def _create_batch(self, cnab_structure, batch_name="Test Batch"):
        with Form(cnab_structure) as form:
            with form.batch_ids.new() as batch_form:
                batch_form.name = batch_name
        return cnab_structure.batch_ids[-1]

    def _create_line_with_field(
        self, cnab_structure, batch=None, line_type="header", **kwargs
    ):
        defaults = {
            "type": line_type,
            "communication_flow": "both",
            "start_pos": 1,
            "end_pos": 240,
        }
        defaults.update(kwargs)

        line_form = Form(
            self.env["l10n_br_cnab.line"],
            view="l10n_br_cnab_structure.cnab_line_form_view",
        )
        line_form.cnab_structure_id = cnab_structure

        line_form.batch_id = batch or line_form.batch_id

        line_form.communication_flow = defaults["communication_flow"]
        line_form.type = defaults["type"]

        extra_fields = {
            "segment": lambda form: setattr(
                form, "segment_code", kwargs.get("segment_code", "A")
            ),
        }
        extra_fields.get(line_type, lambda form: None)(line_form)

        with line_form.field_ids.new() as field_form:
            field_form.start_pos = defaults["start_pos"]
            field_form.end_pos = defaults["end_pos"]

        return line_form.save()

    def _create_valid_cnab_structure_complete(self):
        cnab_structure = self._create_cnab_structure()

        batch = self._create_batch(cnab_structure, "Batch 1")

        self._create_line_with_field(cnab_structure, line_type="header")
        self._create_line_with_field(cnab_structure, batch, line_type="header")
        self._create_line_with_field(
            cnab_structure, batch, line_type="segment", segment_code="X"
        )
        self._create_line_with_field(cnab_structure, batch, line_type="trailer")
        self._create_line_with_field(cnab_structure, line_type="trailer")

        return cnab_structure

    def _assert_cnab_240_defaults(self, cnab_structure):
        self.assertTrue(cnab_structure)
        self.assertRecordValues(
            cnab_structure,
            [
                {
                    "conf_bank_start_pos": POS_BANK_START,
                    "conf_bank_end_pos": POS_BANK_END,
                    "conf_record_type_start_pos": POS_REC_TYPE,
                    "conf_record_type_end_pos": POS_REC_TYPE,
                    "conf_batch_start_pos": POS_BATCH_START,
                    "conf_batch_end_pos": POS_BATCH_END,
                    "conf_detail_start_pos": POS_DETAIL_START,
                    "conf_detail_end_pos": POS_DETAIL_END,
                    "conf_segment_start_pos": POS_SEGMENT_START,
                    "conf_segment_end_pos": POS_SEGMENT_END,
                    "record_type_file_header_id": REC_FILE_HEADER,
                    "record_type_file_trailer_id": REC_FILE_TRAILER,
                    "record_type_batch_header_id": REC_BATCH_HEADER,
                    "record_type_batch_trailer_id": REC_BATCH_TRAILER,
                    "record_type_detail_id": REC_DETAIL,
                }
            ],
        )
        for outbound in cnab_structure.filtered(lambda s: s.payment_type == "outbound"):
            self.assertRecordValues(
                outbound,
                [
                    {
                        "conf_payment_way_start_pos": POS_WAY_START,
                        "conf_payment_way_end_pos": POS_WAY_END,
                    }
                ],
            )

    def test_file_generete_and_return(self):
        invoice = self._create_test_invoice()
        payment_order = self._create_payment_order(invoice)
        self.assertEqual(len(payment_order), 1)

        payment_order.draft2open()
        action = payment_order.open2generated()
        delivery_cnab_file = self.attachment_model.browse(action["res_id"])
        self.assertIsNotNone(delivery_cnab_file)

        cnab_data = base64.b64decode(delivery_cnab_file.datas).decode()
        lines = cnab_data.splitlines()

        lines[2] = replace_chars(lines[2], 154, "10112022")
        lines[2] = replace_chars(lines[2], 172, "300")
        lines[2] = replace_chars(lines[2], 230, "00")

        return_data = "\r\n".join(lines).encode()

        import_wizard = self.env["cnab.import.wizard"].create(
            {
                "journal_id": self.bank_journal_itau.id,
                "return_file": base64.b64encode(return_data),
                "filename": "TEST.RET",
                "type": "outbound",
                "cnab_structure_id": self.cnab_structure_itau_240.id,
            }
        )
        action = import_wizard.with_context(default_type="outbound").import_cnab()
        cnab_log = self.env["l10n_br_cnab.return.log"].browse(action["res_id"])

        self.assertIsNotNone(cnab_log)
        self.assertFalse(cnab_log.event_ids.mapped("generated_move_id"))

        cnab_log.action_confirm_return_log()
        self.assertTrue(cnab_log.event_ids.mapped("generated_move_id"))

    def test_cnab_yaml_output(self):
        invoice = self._create_test_invoice()
        payment_order = self._create_payment_order(invoice)

        preview_wizard = self.env["cnab.preview.wizard"].create(
            {
                "payment_order_id": payment_order.id,
                "cnab_structure_id": self.cnab_structure_itau_240.id,
            }
        )

        self.assertIsNotNone(preview_wizard.output_yaml)
        self.assertIn(
            "    103_132_nome_do_banco: 'BANCO ITAU                    '\n",
            preview_wizard.output_yaml,
        )

    def test_file_generate_bb_seq_detail_with_temp_files(self):
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            invoice_bb = self._create_test_invoice(
                payment_mode=self.pix_mode_bb, amount=150.0
            )
            payment_order = self._create_payment_order(invoice_bb)
            self.assertEqual(len(payment_order), 1)

            cnab_structure = self.cnab_structure_bb_240

            cnab_structure.unique_seq_per_segment = False
            payment_order.draft2open()
            action_false = payment_order.open2generated()
            cnab_data_false = base64.b64decode(
                self.attachment_model.browse(action_false["res_id"]).datas
            ).decode()

            tmp_file_false = tmp_path / "bb_seq_false.rem"
            tmp_file_false.write_text(cnab_data_false)

            lines_false = cnab_data_false.splitlines()
            seqs_false = [line[8:13] for line in lines_false if line[7] == "3"]
            self.assertTrue(
                all(seq == seqs_false[0] for seq in seqs_false),
            )

            cnab_structure.unique_seq_per_segment = True
            action_true = payment_order.open2generated()
            cnab_data_true = base64.b64decode(
                self.attachment_model.browse(action_true["res_id"]).datas
            ).decode()

            tmp_file_true = tmp_path / "bb_seq_true.rem"
            tmp_file_true.write_text(cnab_data_true)

            lines_true = cnab_data_true.splitlines()
            seqs_true = [line[8:13] for line in lines_true if line[7] == "3"]
            self.assertEqual(seqs_true, sorted(seqs_true))
            self.assertEqual(len(seqs_true), len(set(seqs_true)))

    def test_cnab_structure_240_outbound(self):
        cnab_structure = self._create_cnab_structure(
            payment_method=self.env.ref(
                "l10n_br_account_payment_order.payment_mode_type_cnab240_out"
            )
        )
        self._assert_cnab_240_defaults(cnab_structure)

    def test_cnab_structure_240_inbound(self):
        cnab_structure = self._create_cnab_structure(
            payment_method=self.env.ref(
                "l10n_br_account_payment_order.payment_mode_type_cnab240"
            )
        )
        self.assertTrue(cnab_structure)
        self._assert_cnab_240_defaults(cnab_structure)

    def test_cnab_structure_400_inbound(self):
        cnab_structure = self._create_cnab_structure(
            payment_method=self.env.ref(
                "l10n_br_account_payment_order.payment_mode_type_cnab400"
            )
        )
        self.assertTrue(cnab_structure)
        self.assertEqual(cnab_structure.conf_record_type_start_pos, POS_REC_TYPE)
        self.assertEqual(cnab_structure.conf_record_type_end_pos, POS_REC_TYPE)
        self.assertEqual(cnab_structure.record_type_file_trailer_id, REC_FILE_TRAILER)
        self.assertEqual(cnab_structure.record_type_detail_id, 1)

    def test_cnab_structure_500_inbound(self):
        cnab_structure = self._create_cnab_structure(
            payment_method=self.env.ref(
                "l10n_br_account_payment_order.payment_mode_type_cnab500"
            )
        )
        self.assertEqual(cnab_structure.conf_record_type_start_pos, 0)

    def test_cnab_structure_states(self):
        cnab_structure = self._create_valid_cnab_structure_complete()

        self.assertEqual(cnab_structure.state, "draft")

        cnab_structure.action_review()
        self.assertEqual(cnab_structure.state, "review")

        cnab_structure.action_approve()
        self.assertEqual(cnab_structure.state, "approved")

        cnab_structure.action_draft()
        self.assertEqual(cnab_structure.state, "draft")

    def test_multiple_batch_headers(self):
        cnab_structure = self._create_cnab_structure(
            name="Test Multiple Headers", bank=self.bank_001
        )
        batch = self._create_batch(cnab_structure, "Batch 1")

        cnab_structure.line_ids.unlink()

        self._create_line_with_field(
            cnab_structure, line_type="header", name="File Header", sequence=1
        )
        self._create_line_with_field(
            cnab_structure, batch, line_type="header", name="Batch Header 1", sequence=2
        )
        self._create_line_with_field(
            cnab_structure, batch, line_type="header", name="Batch Header 2", sequence=3
        )
        self._create_line_with_field(
            cnab_structure, batch, line_type="segment", name="Segment A", sequence=4
        )
        self._create_line_with_field(
            cnab_structure, batch, line_type="trailer", name="Batch Trailer", sequence=5
        )
        self._create_line_with_field(
            cnab_structure, line_type="trailer", name="File Trailer", sequence=6
        )

        batch.check_batch()

        header_lines = batch.line_ids.filtered(lambda line: line.type == "header")
        self.assertEqual(len(header_lines), 2)

    def test_payment_rules(self):
        cnab_structure = self.cnab_structure_itau_240

        if not cnab_structure.batch_ids:
            self._create_batch(cnab_structure, "Batch 1")
        batch = cnab_structure.batch_ids[0]

        way_same_bank = self.env["cnab.payment.way"].create(
            {
                "code": PAY_WAY_SAME_BANK,
                "description": "Credit Same Bank",
                "cnab_structure_id": cnab_structure.id,
                "batch_id": batch.id,
            }
        )
        way_other_bank = self.env["cnab.payment.way"].create(
            {
                "code": PAY_WAY_OTHER_BANK,
                "description": "TED Other Bank",
                "cnab_structure_id": cnab_structure.id,
                "batch_id": batch.id,
            }
        )

        self.env["l10n_br_cnab.payment.rule"].create(
            {
                "cnab_structure_id": cnab_structure.id,
                "sequence": 10,
                "match_bank_type": "same",
                "match_partner_type": "any",
                "payment_way_id": way_same_bank.id,
                "service_type": SVC_SUPPLIER,
            }
        )
        self.env["l10n_br_cnab.payment.rule"].create(
            {
                "cnab_structure_id": cnab_structure.id,
                "sequence": 20,
                "match_bank_type": "other",
                "match_partner_type": "any",
                "payment_way_id": way_other_bank.id,
                "service_type": SVC_SALARY,
            }
        )

        invoice = self._create_test_invoice()
        payment_order = self._create_payment_order(invoice)

        line_same = self.env["account.payment.line"].create(
            {
                "order_id": payment_order.id,
                "partner_id": self.partner_a.id,
                "partner_bank_id": self.partner_a_itau_bank.id,
                "amount_currency": 100.0,
            }
        )
        line_same._compute_cnab_payment_way_id()
        self.assertEqual(line_same.cnab_payment_way_id, way_same_bank)
        self.assertEqual(line_same.service_type, SVC_SUPPLIER)

        invoice_2 = self._create_test_invoice()
        payment_order_2 = self._create_payment_order(invoice_2)

        line_other = self.env["account.payment.line"].create(
            {
                "order_id": payment_order_2.id,
                "partner_id": self.partner_a.id,
                "partner_bank_id": self.partner_a_bb_bank.id,
                "amount_currency": 200.0,
            }
        )
        line_other._compute_cnab_payment_way_id()
        self.assertEqual(line_other.cnab_payment_way_id, way_other_bank)
        self.assertEqual(line_other.service_type, SVC_SALARY)

        with self.subTest("_compute_cnab_beneficiary_name"):
            self.partner_a_itau_bank.acc_holder_name = "São Paulo"
            line_same._compute_cnab_beneficiary_name()
            self.assertEqual(
                line_same.cnab_beneficiary_name,
                unidecode("São Paulo").strip(),
            )
            self.partner_a_itau_bank.acc_holder_name = False
            line_other._compute_cnab_beneficiary_name()
            self.assertEqual(
                line_other.cnab_beneficiary_name,
                unidecode(self.partner_a.name).strip(),
            )

    def test_unique_sequence_per_segment_behavior(self):
        cnab_structure = self.cnab_structure_bb_240

        invoice_1 = self._create_test_invoice()
        payment_order = self._create_payment_order(invoice_1)

        invoice_2 = self._create_test_invoice(amount=200.0)
        invoice_2.action_post()
        self.env["account.invoice.payment.line.multi"].with_context(
            active_model="account.move", active_ids=invoice_2.ids
        ).create({}).run()

        payment_order.draft2open()

        cnab_structure.unique_seq_per_segment = False
        action_false = payment_order.open2generated()
        data_false = (
            base64.b64decode(self.attachment_model.browse(action_false["res_id"]).datas)
            .decode()
            .splitlines()
        )
        details_false = [line[8:13] for line in data_false if line[7] == "3"]

        self.assertEqual(details_false[0], details_false[1])
        self.assertNotEqual(details_false[0], details_false[2])

        cnab_structure.unique_seq_per_segment = True
        payment_order.state = "open"
        action_true = payment_order.open2generated()
        data_true = (
            base64.b64decode(self.attachment_model.browse(action_true["res_id"]).datas)
            .decode()
            .splitlines()
        )
        details_true = [line[8:13] for line in data_true if line[7] == "3"]

        self.assertEqual(details_true[0], details_true[1])
        self.assertNotEqual(details_true[0], details_true[2])
        self.assertEqual(int(details_true[2]), int(details_true[0]) + 1)

    def test_batch_grouping_by_service_type(self):
        cnab_structure = self.cnab_structure_itau_240

        batch = cnab_structure.batch_ids[:1] or self._create_batch(
            cnab_structure, "Default Batch"
        )

        way_ted = self.env["cnab.payment.way"].create(
            {
                "code": PAY_WAY_OTHER_BANK,
                "description": "TED",
                "cnab_structure_id": cnab_structure.id,
                "batch_id": batch.id,
            }
        )
        way_cc = self.env["cnab.payment.way"].create(
            {
                "code": PAY_WAY_SAME_BANK,
                "description": "Current Account",
                "cnab_structure_id": cnab_structure.id,
                "batch_id": batch.id,
            }
        )

        test_mode = self.env["account.payment.mode"].create(
            {
                "name": "Test Grouping Mode",
                "bank_account_link": "fixed",
                "company_id": self.company.id,
                "payment_method_id": self.outbound_payment_method.id,
                "fixed_journal_id": self.bank_journal_itau.id,
                "cnab_structure_id": cnab_structure.id,
                "cnab_payment_way_ids": [(6, 0, [way_ted.id, way_cc.id])],
                "cnab_processor": "oca_processor",
            }
        )

        payment_order = self.env["account.payment.order"].create(
            {
                "payment_mode_id": test_mode.id,
                "state": "draft",
                "company_id": self.company.id,
                "journal_id": self.bank_journal_itau.id,
            }
        )

        self.env["account.payment.line"].create(
            {
                "order_id": payment_order.id,
                "partner_id": self.partner_a.id,
                "partner_bank_id": self.partner_a_itau_bank.id,
                "amount_currency": 100.0,
                "service_type": SVC_SUPPLIER,
                "cnab_payment_way_id": way_ted.id,
                "communication": "TEST BATCH 1",
            }
        )

        self.env["account.payment.line"].create(
            {
                "order_id": payment_order.id,
                "partner_id": self.partner_a.id,
                "partner_bank_id": self.partner_a_itau_bank.id,
                "amount_currency": 200.0,
                "service_type": SVC_SALARY,
                "cnab_payment_way_id": way_cc.id,
                "communication": "TEST BATCH 2",
            }
        )

        payment_order._compute_cnab_processor()
        payment_order._compute_cnab_structure_id()

        payment_order.draft2open()
        action = payment_order.open2generated()

        cnab_file = self.attachment_model.browse(action["res_id"])
        cnab_content = base64.b64decode(cnab_file.datas).decode()
        lines = cnab_content.splitlines()

        batch_headers = [line for line in lines if len(line) > 8 and line[7] == "1"]

        self.assertEqual(
            len(batch_headers),
            2,
        )

        found_types = [h[9:11] for h in batch_headers]
        self.assertIn(SVC_SUPPLIER, found_types)
        self.assertIn(SVC_SALARY, found_types)

    def test_field_select_wizard(self):
        cnab_structure = self._create_valid_cnab_structure_complete()
        cnab_field_id = cnab_structure.line_ids[0].field_ids[0]

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

        self.assertFalse(field_select_wizard.notation_field)
        field_select_wizard.new_field_id = find_field("company_partner_bank_id")
        field_select_wizard._update_dot_notation()
        self.assertEqual(field_select_wizard.notation_field, "company_partner_bank_id")

        field_select_wizard.new_field_id = find_field("bank_id")
        field_select_wizard._update_dot_notation()
        self.assertEqual(
            field_select_wizard.notation_field, "company_partner_bank_id.bank_id"
        )

        field_select_wizard.action_remove_last_field()
        self.assertEqual(field_select_wizard.notation_field, "company_partner_bank_id")

        self.assertFalse(cnab_field_id.content_source_field)
        field_select_wizard.action_confirm()
        self.assertEqual(cnab_field_id.content_source_field, "company_partner_bank_id")
