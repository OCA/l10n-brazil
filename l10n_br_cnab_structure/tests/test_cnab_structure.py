# Copyright (C) 2022 - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestCNABStructure(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.company_data["company"]
        cls.env.user.company_id = cls.company.id
        cls.res_partner_bank_model = cls.env["res.partner.bank"]
        cls.payment_mode_model = cls.env["account.payment.mode"]
        cls.payment_order_model = cls.env["account.payment.order"]
        cls.payment_line_model = cls.env["account.payment.line"]
        cls.attachment_model = cls.env["ir.attachment"]
        cls.res_partner_pix_model = cls.env["res.partner.pix"]
        cls.bank_341 = cls.env.ref("l10n_br_base.res_bank_341")
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
        cls.outbound_payment_method = cls.env.ref(
            "l10n_br_cnab_structure.payment_mode_type_cnab240_out"
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
                "cnab_structure_id": cls.env.ref(
                    "l10n_br_cnab_structure.cnab_itau_240"
                ).id,
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

    def test_file_generete(self):
        # Open invoice
        self.invoice.action_post()
        # Add to payment order using the wizard
        self.env["account.invoice.payment.line.multi"].with_context(
            active_model="account.move", active_ids=self.invoice.ids
        ).create({}).run()
        payment_order = self.env["account.payment.order"].search(self.domain)
        self.assertEqual(len(payment_order), 1)
        # Open payment order
        payment_order.draft2open()
        action = payment_order.open2generated()
        attachment = self.attachment_model.browse(action["res_id"])
        self.assertIsNotNone(attachment)
