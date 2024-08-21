# Copyright (C) 2024-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPaymentOrder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.instruction_unicred_01 = cls.env.ref(
            "l10n_br_account_payment_order.unicred_240_400_instruction_01"
        )

    def test_cnab_code_abstract(self):
        """Test CNAB Code Abstract Model"""
        # Testa o name_get do objeto
        self.instruction_unicred_01.name_get()

    def test_cnab_instruction_move_code(self):
        """Test CNAB Instruction Move Code"""
        instruction_code_form = Form(self.instruction_unicred_01)

        # Testa os campos compute
        # TODO: Ver a questão do Group By a aprtir da v15 ou v16
        instruction_code_form.bank_ids.add(self.env.ref("l10n_br_base.res_bank_237"))
        instruction_code_form.payment_method_ids.add(
            self.env.ref("l10n_br_account_payment_order.payment_mode_type_cnab500")
        )
        instruction_code_form.save()

        # Testa o caso do tamanho do campo 2
        instruction_code_form.code = "123"
        with self.assertRaises(ValidationError):
            instruction_code_form.save()

        # Testa o caso do Codigo Duplicado
        instruction_code_new_form = Form(
            self.env["l10n_br_cnab.mov.instruction.code"],
            "l10n_br_account_payment_order.l10n_br_cnab_mov_instruction_code_form_view",
        )

        instruction_code_new_form.code = "01"
        instruction_code_new_form.name = "Remessa*"
        instruction_code_new_form.bank_ids.add(
            self.env.ref("l10n_br_base.res_bank_136")
        )
        instruction_code_new_form.payment_method_ids.add(
            self.env.ref("l10n_br_account_payment_order.payment_mode_type_cnab400")
        )
        with self.assertRaises(ValidationError):
            instruction_code_new_form.save()

    def test_cnab_return_move_code(self):
        """Test CNAB Return Move Code"""
        # Caso campo deve ter o tamanho 2
        return_unicred_01 = self.env.ref(
            "l10n_br_account_payment_order.unicred_240_400_return_01"
        )
        return_code_form = Form(return_unicred_01)

        # Testa o caso dos campos compute
        # TODO: Ver a questão do Group By a partir da v15 ou v16
        return_code_form.bank_ids.add(self.env.ref("l10n_br_base.res_bank_237"))
        return_code_form.payment_method_ids.add(
            self.env.ref("l10n_br_account_payment_order.payment_mode_type_cnab500")
        )
        return_code_form.save()

        # Testa caso do tamanho ser 2
        return_code_form.code = "123"
        with self.assertRaises(ValidationError):
            return_code_form.save()

        # Caso Codigo Duplicado
        return_move_code_new_form = Form(
            self.env["l10n_br_cnab.return.move.code"],
            "l10n_br_account_payment_order.l10n_br_cnab_return_move_code_form_view",
        )

        return_move_code_new_form.code = "01"
        return_move_code_new_form.name = "Pago (Título protestado pago em cartório)"
        return_move_code_new_form.bank_ids.add(
            self.env.ref("l10n_br_base.res_bank_136")
        )
        return_move_code_new_form.payment_method_ids.add(
            self.env.ref("l10n_br_account_payment_order.payment_mode_type_cnab400")
        )
        with self.assertRaises(ValidationError):
            return_move_code_new_form.save()

    def test_cnab_boleto_wallet_code(self):
        """Test CNAB Boleto Wallet Code"""
        boleto_wallet_code_1 = self.env.ref(
            "l10n_br_account_payment_order.santander_240_boleto_wallet_code_1"
        )
        boleto_wallet_code_form = Form(boleto_wallet_code_1)

        # Testa o caso dos campos compute
        # TODO: Ver a questão do Group By a partir da v15 ou v16
        boleto_wallet_code_form.bank_ids.add(self.env.ref("l10n_br_base.res_bank_136"))
        boleto_wallet_code_form.payment_method_ids.add(
            self.env.ref("l10n_br_account_payment_order.payment_mode_type_cnab500")
        )
        boleto_wallet_code_form.save()

        # Caso Codigo Duplicado
        boleto_wallet_code_new_form = Form(
            self.env["l10n_br_cnab.boleto.wallet.code"],
            "l10n_br_account_payment_order.l10n_br_cnab_boleto_wallet_code_form_view",
        )

        boleto_wallet_code_new_form.code = "1"
        boleto_wallet_code_new_form.name = (
            "Cobrança Simples (Sem Registro e Eletrônica com Registro)"
        )
        boleto_wallet_code_new_form.bank_ids.add(
            self.env.ref("l10n_br_base.res_bank_033")
        )
        boleto_wallet_code_new_form.payment_method_ids.add(
            self.env.ref("l10n_br_account_payment_order.payment_mode_type_cnab400")
        )
        with self.assertRaises(ValidationError):
            boleto_wallet_code_new_form.save()
