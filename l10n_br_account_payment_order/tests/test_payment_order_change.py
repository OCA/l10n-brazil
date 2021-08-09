# @ 2021 KMEE - www.kmee.com.br
#   Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from datetime import date, timedelta

from odoo.tests import Form, tagged

from .test_base_class import TestL10nBrAccountPaymentOder


@tagged("post_install", "-at_install")
class TestPaymentOrderChange(TestL10nBrAccountPaymentOder):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.invoice_auto = cls.env.ref(
            "l10n_br_account_payment_order." "demo_invoice_automatic_test"
        )
        if cls.invoice_auto.state == "draft":
            cls.invoice_auto.action_invoice_open()

        assert cls.invoice_auto.move_id, "Move not created for open invoice"

        cls.financial_move_line_ids = cls.invoice_auto.financial_move_line_ids
        cls.financial_move_line_0 = cls.financial_move_line_ids[0]
        cls.financial_move_line_1 = cls.financial_move_line_ids[1]

        assert cls.financial_move_line_0, "Move 0 not created for open invoice"
        assert cls.financial_move_line_1, "Move 1 not created for open invoice"

    def test_change_date_maturity_multiple(self):
        """ Test Creation of a Payment Order an change MULTIPLE due date """
        self._invoice_payment_order_all_workflow(self.invoice_auto)
        date_maturity = self.financial_move_line_ids.mapped("date_maturity")
        new_date = date.today() + timedelta(days=120)
        with Form(
            self._prepare_change_view(self.financial_move_line_ids),
            view=self.chance_view_id,
        ) as f:
            f.change_type = "change_date_maturity"
            f.date_maturity = new_date
        change_wizard = f.save()
        change_wizard.doit()

        self.assertEqual(
            self.financial_move_line_0.date_maturity, new_date, "Data não alterada"
        )
        self.assertNotEqual(date_maturity[0], new_date, "Data não alterada")

        change_payment_order = self.env["account.payment.order"].search(
            [
                ("state", "=", "draft"),
                ("payment_mode_id", "=", self.invoice_auto.payment_mode_id.id),
            ]
        )
        self._payment_order_all_workflow(change_payment_order)

        assert (
            self.env.ref(
                "l10n_br_account_payment_order.manual_test_mov_instruction_code_06"
            ).id
            in change_payment_order.payment_line_ids.mapped(
                "mov_instruction_code_id"
            ).ids
        ), "Payment Order with wrong mov_instruction_code_id"

    def test_change_date_maturity_one(self):
        """ Test Creation of a Payment Order an change ONE due date """
        self._invoice_payment_order_all_workflow(self.invoice_auto)
        date_maturity = self.financial_move_line_0.mapped("date_maturity")
        new_date = date.today() + timedelta(days=120)

        with Form(
            self._prepare_change_view(self.financial_move_line_0),
            view=self.chance_view_id,
        ) as f:
            f.change_type = "change_date_maturity"
            f.date_maturity = new_date
        change_wizard = f.save()
        change_wizard.doit()

        self.assertEqual(
            self.env["account.move.line"]
            .browse(self.financial_move_line_0.id)
            .date_maturity,
            new_date,
            "Data não alterada",
        )
        self.assertNotEqual(date_maturity[0], new_date, "Data não alterada")

        change_payment_order = self.env["account.payment.order"].search(
            [
                ("state", "=", "draft"),
                ("payment_mode_id", "=", self.invoice_auto.payment_mode_id.id),
            ]
        )
        self._payment_order_all_workflow(change_payment_order)

        assert (
            self.env.ref(
                "l10n_br_account_payment_order.manual_test_mov_instruction_code_06"
            ).id
            in change_payment_order.payment_line_ids.mapped(
                "mov_instruction_code_id"
            ).ids
        ), "Payment Order with wrong mov_instruction_code_id"

    # def test_change_payment_mode(self):
    #     invoice = self.invoice_auto
    #     self._invoice_payment_order_all_workflow(
    #         invoice
    #     )
    #     financial_move_line_ids = invoice.financial_move_line_ids[0]
    #     with Form(self._prepare_change_view(financial_move_line_ids),
    #               view=self.chance_view_id) as f:
    #         f.change_type = 'change_payment_mode'
    #         f.payment_mode_id = self.env.ref(
    #             'l10n_br_account_payment_order.main_payment_mode_boleto')
    #     change_wizard = f.save()
    #     self.assertRaises(
    #         change_wizard.doit(), 'Favor melhorar este teste'
    #     )

    def test_change_not_payment(self):
        """ Test Creation of a Payment Order an change not_payment """
        self._invoice_payment_order_all_workflow(self.invoice_auto)
        financial_move_line_ids = self.invoice_auto.financial_move_line_ids[0]
        with Form(
            self._prepare_change_view(financial_move_line_ids), view=self.chance_view_id
        ) as f:
            f.change_type = "not_payment"
        change_wizard = f.save()
        change_wizard.doit()

        change_payment_order = self.env["account.payment.order"].search(
            [
                ("state", "=", "draft"),
                ("payment_mode_id", "=", self.invoice_auto.payment_mode_id.id),
            ]
        )
        self._payment_order_all_workflow(change_payment_order)

        assert (
            self.env.ref(
                "l10n_br_account_payment_order.manual_test_mov_instruction_code_02"
            ).id
            in change_payment_order.payment_line_ids.mapped(
                "mov_instruction_code_id"
            ).ids
        ), "Payment Order with wrong mov_instruction_code_id"

    def test_change_protest_tittle(self):
        """ Test Creation of a Payment Order an change protest_tittle """
        self._invoice_payment_order_all_workflow(self.invoice_auto)
        financial_move_line_ids = self.invoice_auto.financial_move_line_ids[0]
        with Form(
            self._prepare_change_view(financial_move_line_ids), view=self.chance_view_id
        ) as f:
            f.change_type = "protest_tittle"
        change_wizard = f.save()
        change_wizard.doit()

        change_payment_order = self.env["account.payment.order"].search(
            [
                ("state", "=", "draft"),
                ("payment_mode_id", "=", self.invoice_auto.payment_mode_id.id),
            ]
        )
        self._payment_order_all_workflow(change_payment_order)

        assert (
            self.env.ref(
                "l10n_br_account_payment_order.manual_test_mov_instruction_code_09"
            ).id
            in change_payment_order.payment_line_ids.mapped(
                "mov_instruction_code_id"
            ).ids
        ), "Payment Order with wrong mov_instruction_code_id"

    def test_change_suspend_protest_keep_wallet(self):
        """ Test Creation of a Payment Order an change suspend_protest_keep_wallet """
        self._invoice_payment_order_all_workflow(self.invoice_auto)
        financial_move_line_ids = self.invoice_auto.financial_move_line_ids[0]
        with Form(
            self._prepare_change_view(financial_move_line_ids), view=self.chance_view_id
        ) as f:
            f.change_type = "suspend_protest_keep_wallet"
        change_wizard = f.save()
        change_wizard.doit()

        change_payment_order = self.env["account.payment.order"].search(
            [
                ("state", "=", "draft"),
                ("payment_mode_id", "=", self.invoice_auto.payment_mode_id.id),
            ]
        )
        self._payment_order_all_workflow(change_payment_order)

        assert (
            self.env.ref(
                "l10n_br_account_payment_order.manual_test_mov_instruction_code_11"
            ).id
            in change_payment_order.payment_line_ids.mapped(
                "mov_instruction_code_id"
            ).ids
        ), "Payment Order with wrong mov_instruction_code_id"

    def test_change_suspend_grant_rebate(self):
        """ Test Creation of a Payment Order an change grant_rebate """
        self._invoice_payment_order_all_workflow(self.invoice_auto)
        financial_move_line_ids = self.invoice_auto.financial_move_line_ids[0]
        with Form(
            self._prepare_change_view(financial_move_line_ids), view=self.chance_view_id
        ) as f:
            f.change_type = "grant_rebate"
            f.rebate_value = 10.00
        change_wizard = f.save()
        change_wizard.doit()

        change_payment_order = self.env["account.payment.order"].search(
            [
                ("state", "=", "draft"),
                ("payment_mode_id", "=", self.invoice_auto.payment_mode_id.id),
            ]
        )
        self._payment_order_all_workflow(change_payment_order)

        assert (
            self.env.ref(
                "l10n_br_account_payment_order.manual_test_mov_instruction_code_04"
            ).id
            in change_payment_order.payment_line_ids.mapped(
                "mov_instruction_code_id"
            ).ids
        ), "Payment Order with wrong mov_instruction_code_id"

    def test_change_suspend_grant_discount(self):
        """ Test Creation of a Payment Order an change grant_discount """
        self._invoice_payment_order_all_workflow(self.invoice_auto)
        financial_move_line_ids = self.invoice_auto.financial_move_line_ids[0]
        with Form(
            self._prepare_change_view(financial_move_line_ids), view=self.chance_view_id
        ) as f:
            f.change_type = "grant_discount"
            f.discount_value = 10.00
        change_wizard = f.save()
        change_wizard.doit()

        change_payment_order = self.env["account.payment.order"].search(
            [
                ("state", "=", "draft"),
                ("payment_mode_id", "=", self.invoice_auto.payment_mode_id.id),
            ]
        )
        self._payment_order_all_workflow(change_payment_order)

        assert (
            self.env.ref(
                "l10n_br_account_payment_order.manual_test_mov_instruction_code_07"
            ).id
            in change_payment_order.payment_line_ids.mapped(
                "mov_instruction_code_id"
            ).ids
        ), "Payment Order with wrong mov_instruction_code_id"

    def test_change_suspend_cancel_rebate(self):
        """ Test Creation of a Payment Order an change cancel_rebate """
        self._invoice_payment_order_all_workflow(self.invoice_auto)
        financial_move_line_ids = self.invoice_auto.financial_move_line_ids[0]
        with Form(
            self._prepare_change_view(financial_move_line_ids), view=self.chance_view_id
        ) as f:
            f.change_type = "cancel_rebate"
        change_wizard = f.save()
        change_wizard.doit()

        change_payment_order = self.env["account.payment.order"].search(
            [
                ("state", "=", "draft"),
                ("payment_mode_id", "=", self.invoice_auto.payment_mode_id.id),
            ]
        )
        self._payment_order_all_workflow(change_payment_order)

        assert (
            self.env.ref(
                "l10n_br_account_payment_order.manual_test_mov_instruction_code_05"
            ).id
            in change_payment_order.payment_line_ids.mapped(
                "mov_instruction_code_id"
            ).ids
        ), "Payment Order with wrong mov_instruction_code_id"

    def test_change_suspend_cancel_discount(self):
        """ Test Creation of a Payment Order an change cancel_discount """
        self._invoice_payment_order_all_workflow(self.invoice_auto)
        financial_move_line_ids = self.invoice_auto.financial_move_line_ids[0]
        with Form(
            self._prepare_change_view(financial_move_line_ids), view=self.chance_view_id
        ) as f:
            f.change_type = "cancel_discount"
        change_wizard = f.save()
        change_wizard.doit()

        change_payment_order = self.env["account.payment.order"].search(
            [
                ("state", "=", "draft"),
                ("payment_mode_id", "=", self.invoice_auto.payment_mode_id.id),
            ]
        )
        self._payment_order_all_workflow(change_payment_order)

        assert (
            self.env.ref(
                "l10n_br_account_payment_order.manual_test_mov_instruction_code_08"
            ).id
            in change_payment_order.payment_line_ids.mapped(
                "mov_instruction_code_id"
            ).ids
        ), "Payment Order with wrong mov_instruction_code_id"
