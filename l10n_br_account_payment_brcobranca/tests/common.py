# Copyright (C) 2023-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
import os

from odoo.modules import get_resource_path
from odoo.tests import tagged

from odoo.addons.l10n_br_account_payment_order.tests.common import (
    CNABTestCommon,
)
from odoo.addons.l10n_br_account_payment_order.tests.tools import (
    create_with_form_account_journal,
    create_with_form_account_move,
    create_with_form_account_payment_mode,
    create_with_form_ir_sequence,
    create_with_form_l10n_br_cnab_config,
    create_with_form_res_partner_bank,
)

_module_ns = "odoo.addons.l10n_br_account_payment_brcobranca"
_provider_class_pay_order = (
    _module_ns + ".models.account_payment_order" + ".PaymentOrder"
)
_provider_class_cnab_parser = (
    _module_ns + ".parser.cnab_file_parser" + ".CNABFileParser"
)
_provider_class_acc_invoice = _module_ns + ".models.account_move" + ".AccountMove"
_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class TestBRCobrancaCommon(CNABTestCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Dados necessários da Empresa/res.company para Gerar os arquivos CNAB

        # l10n_br_account_payment_brcobranca/models/account_payment_order.py",
        # line 150, in generate_payment_file
        cls.env.company.partner_id.legal_name = "Company A LTDA"
        cls.env.company.cnpj_cpf = "47.906.085/0001-35"
        # l10n_br_account_payment_brcobranca/models/account_move_line.py",
        # line 62, in send_payment
        cls.env.company.partner_id.zip = "01234-123"

        # Dados do Cliente/res.partner que devem ser informados

        # l10n_br_account_payment_brcobranca/models/account_move_line.py",
        # line 92, in send_payment
        cls.partner_a.zip = "01234-321"
        # l10n_br_account_payment_order/models/account_payment_line.py",
        # line 265, in _prepare_boleto_line_vals
        cls.partner_a.legal_name = "Partner A LTDA"
        # l10n_br_account_payment_order/models/account_payment_line.py",
        # line 270, in _prepare_boleto_line_vals
        cls.partner_a.district = "Bairro A"
        # l10n_br_account_payment_brcobranca/models/account_move.py",
        # line 84, in _get_brcobranca_boleto
        # raise UserError(res.text.encode("utf-8"))
        # odoo.exceptions.UserError: b'{"error":
        # [{"sacado_documento":["Sacado documento n\xc3\xa3o pode estar em branco."]},
        cls.partner_a.cnpj_cpf = "66.793.591/0001-00"
        # l10n_br_account_payment_brcobranca/models/account_payment_order.py",
        # line 209, in _get_brcobranca_remessa
        # raise ValidationError(res.text)
        # odoo.exceptions.Warning:
        # {"error":[{"cidade_sacado":["Cidade sacado não pode estar em branco."],
        # "uf_sacado":["Uf sacado não pode estar em branco.",
        # "Uf sacado deve ter 2 dígitos."]},
        cls.partner_a.city_id = cls.env.ref("l10n_br_base.city_3550308")
        cls.partner_a.state_id = cls.env.ref("base.state_br_sp")
        cls.partner_a.country_id = cls.env.ref("base.br")

        # Conta Bancaria
        cls.bank_account_unicred = create_with_form_res_partner_bank(
            cls.env,
            {
                "acc_number": "372",
                "acc_number_dig": "0",
                "bra_number": "1234",
                "bra_number_dig": "0",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_136"),
                "partner_id": cls.env.company.partner_id,
            },
        )

        cls.bank_account_brasil = create_with_form_res_partner_bank(
            cls.env,
            {
                "acc_number": "5385",
                "acc_number_dig": "8",
                "bra_number": "7030",
                "bra_number_dig": "8",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_001"),
                "partner_id": cls.env.company.partner_id,
            },
        )

        cls.bank_account_bradesco = create_with_form_res_partner_bank(
            cls.env,
            {
                "acc_number": "396",
                "acc_number_dig": "0",
                "bra_number": "1611",
                "bra_number_dig": "0",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_237"),
                "partner_id": cls.env.company.partner_id,
            },
        )

        cls.bank_account_sicredi = create_with_form_res_partner_bank(
            cls.env,
            {
                "acc_number": "332",
                "acc_number_dig": "0",
                "bra_number": "1234",
                "bra_number_dig": "0",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_748"),
                "partner_id": cls.env.company.partner_id,
            },
        )

        cls.bank_account_santander = create_with_form_res_partner_bank(
            cls.env,
            {
                "acc_number": "1333",
                "acc_number_dig": "3",
                "bra_number": "0707",
                "bra_number_dig": "1",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_033"),
                "partner_id": cls.env.company.partner_id,
            },
        )

        cls.bank_account_ailos = create_with_form_res_partner_bank(
            cls.env,
            {
                "acc_number": "374",
                "acc_number_dig": "0",
                "bra_number": "1236",
                "bra_number_dig": "1",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_085"),
                "partner_id": cls.env.company.partner_id,
            },
        )

        cls.bank_account_nordeste = create_with_form_res_partner_bank(
            cls.env,
            {
                "acc_number": "123",
                "acc_number_dig": "0",
                "bra_number": "1234",
                "bra_number_dig": "0",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_004"),
                "partner_id": cls.env.company.partner_id,
            },
        )

        # Sequencias

        # Arquivo CNAB
        cls.cnab_seq_unicred = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Sequencia Arquivo CNAB - UNICRED 400",
                "code": "Sequencia Arquivo CNAB - UNICRED 400",
            },
        )
        # Nosso Número
        cls.own_number_seq_unicred = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Nosso número UNICRED",
                "code": "nosso.numero",
            },
        )

        cls.cnab_seq_brasil = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Sequencia Arquivo CNAB - Banco do Brasil 400",
                "code": "Sequencia Arquivo CNAB - Banco do BRasil 400",
            },
        )

        cls.own_number_seq_brasil = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Nosso número Banco do Brasil",
                "code": "nosso.numero",
            },
        )

        cls.cnab_seq_bradesco = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Sequencia Arquivo CNAB - Bradesco 400",
                "code": "Sequencia Arquivo CNAB - Bradesco 400",
            },
        )

        cls.own_number_seq_bradesco = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Nosso número Bradesco",
                "code": "nosso.numero",
            },
        )

        cls.cnab_seq_sicredi = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Sequencia Arquivo CNAB - SICREDI 240",
                "code": "Sequencia Arquivo CNAB - SICREDI 240",
            },
        )

        cls.own_number_seq_sicredi = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Nosso número SICREDI",
                "code": "nosso.numero",
            },
        )

        cls.cnab_seq_santander_400 = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Sequencia Arquivo CNAB - Santander 400",
                "code": "Sequencia Arquivo CNAB - Santander 400",
            },
        )

        cls.own_number_seq_santander_400 = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Nosso número Santander",
                "code": "nosso.numero",
            },
        )

        cls.cnab_seq_santander_240 = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Sequencia Arquivo CNAB - Santander 240",
                "code": "Sequencia Arquivo CNAB - Santander 240",
            },
        )

        cls.own_number_seq_santander_240 = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Nosso número Santander",
                "code": "nosso.numero",
            },
        )

        cls.cnab_seq_ailos = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Sequencia Arquivo CNAB - AILOS 240",
                "code": "Sequencia Arquivo CNAB - AILOS 240",
            },
        )

        cls.own_number_seq_ailos = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Nosso número AILOS",
                "code": "nosso.numero",
            },
        )

        cls.cnab_seq_nordeste = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Sequencia Arquivo CNAB - Nordeste 400",
                "code": "Sequencia Arquivo CNAB - Nordeste 400",
            },
        )

        cls.own_number_seq_nordeste = create_with_form_ir_sequence(
            cls.env,
            cls.common_sequence_values
            | {
                "name": "Nosso número Nordeste",
                "code": "nosso.numero",
            },
        )

        # Configurção do CNAB
        cls.cnab_config_cef.cnab_processor = "brcobranca"
        cls.cnab_config_itau_400.cnab_processor = "brcobranca"
        cls.cnab_config_itau_240.cnab_processor = "brcobranca"

        cls.common_cnab_config_values.update({"cnab_processor": "brcobranca"})

        cls.cnab_config_unicred = create_with_form_l10n_br_cnab_config(
            cls.env,
            cls.common_cnab_config_values
            | {
                "name": "Banco Unicred - CNAB 400 (inbound)",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_136"),
                "payment_method_id": cls.pay_method_type_400,
                "boleto_wallet": "21",
                "boleto_variation": "19",
                "boleto_discount_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.unicred_240_400_boleto_discount_code_1"
                ),
                "boleto_protest_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.unicred_240_400_boleto_protest_code_2"
                ),
                "boleto_interest_code": "2",
                "cnab_sequence_id": cls.cnab_seq_unicred,
                "own_number_sequence_id": cls.own_number_seq_unicred,
                "cnab_company_bank_code": "92035760",
                "sending_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.unicred_240_400_instruction_01"
                ),
                "write_off_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.unicred_240_400_instruction_02"
                ),
                "change_maturity_date_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.unicred_240_400_instruction_06"
                ),
                "protest_title_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.unicred_240_400_instruction_09"
                ),
                "suspend_protest_keep_wallet_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.unicred_240_400_instruction_11"
                ),
                "suspend_protest_write_off_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.unicred_240_400_instruction_25"
                ),
                "grant_rebate_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.unicred_240_400_instruction_04"
                ),
                "cancel_rebate_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.unicred_240_400_instruction_04"
                ),
            },
        )
        cls.cnab_config_unicred.write(
            {
                "liq_return_move_code_ids": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref(
                                "l10n_br_account_payment_order.unicred_240_400_return_01"
                            ).id,
                            cls.env.ref(
                                "l10n_br_account_payment_order.unicred_240_400_return_06"
                            ).id,
                            cls.env.ref(
                                "l10n_br_account_payment_order.unicred_240_400_return_07"
                            ).id,
                            cls.env.ref(
                                "l10n_br_account_payment_order.unicred_240_400_return_09"
                            ).id,
                        ],
                    )
                ],
            }
        )

        cls.cnab_config_brasil = create_with_form_l10n_br_cnab_config(
            cls.env,
            cls.common_cnab_config_values
            | {
                "name": "Banco do Brasil - CNAB 400 (inbound)",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_001"),
                "payment_method_id": cls.pay_method_type_400,
                "boleto_wallet": "18",
                "boleto_variation": "19",
                "boleto_interest_code": "1",
                "cnab_sequence_id": cls.cnab_seq_brasil,
                "own_number_sequence_id": cls.own_number_seq_brasil,
                "cnab_company_bank_code": "1234",
                "convention_code": "7654321",
                "sending_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.brasil_400_instruction_01"
                ),
                "write_off_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.brasil_400_instruction_02"
                ),
            },
        )

        cls.cnab_config_bradesco = create_with_form_l10n_br_cnab_config(
            cls.env,
            cls.common_cnab_config_values
            | {
                "name": "Banco do Bradesco - CNAB 400 (inbound)",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_237"),
                "payment_method_id": cls.pay_method_type_400,
                "boleto_wallet": "03",
                "boleto_variation": "19",
                "boleto_interest_code": "2",
                "cnab_sequence_id": cls.cnab_seq_bradesco,
                "own_number_sequence_id": cls.own_number_seq_bradesco,
                "cnab_company_bank_code": "0001222130126",
                "sending_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.bradesco_400_instruction_01"
                ),
                "write_off_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.bradesco_400_instruction_02"
                ),
            },
        )

        cls.cnab_config_sicredi = create_with_form_l10n_br_cnab_config(
            cls.env,
            cls.common_cnab_config_values
            | {
                "name": "Banco do SICREDI - CNAB 240 (inbound)",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_748"),
                "payment_method_id": cls.pay_method_type_240,
                "boleto_wallet": "3",
                "boleto_variation": "19",
                "boleto_interest_code": "2",
                "cnab_sequence_id": cls.cnab_seq_sicredi,
                "own_number_sequence_id": cls.own_number_seq_sicredi,
                "cnab_company_bank_code": "12345",
                "boleto_byte_idt": "2",
                "boleto_post": "1",
                "sending_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.sicredi_240_instruction_01"
                ),
                "write_off_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.sicredi_240_instruction_02"
                ),
            },
        )

        cls.cnab_config_santander_400 = create_with_form_l10n_br_cnab_config(
            cls.env,
            cls.common_cnab_config_values
            | {
                "name": "Banco Santander - CNAB 400 (inbound)",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_033"),
                "payment_method_id": cls.pay_method_type_400,
                "boleto_wallet": "101",
                "wallet_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.santander_400_boleto_wallet_code_5"
                ),
                "boleto_variation": "35",
                "boleto_interest_code": "2",
                "cnab_sequence_id": cls.cnab_seq_santander_400,
                "own_number_sequence_id": cls.own_number_seq_santander_400,
                "cnab_company_bank_code": "12345678901234567890",
                "convention_code": "1234567",
                "sending_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.santander_400_instruction_01"
                ),
                "write_off_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.santander_400_instruction_02"
                ),
            },
        )

        cls.cnab_config_santander_240 = create_with_form_l10n_br_cnab_config(
            cls.env,
            cls.common_cnab_config_values
            | {
                "name": "Banco Santander - CNAB 240 (inbound)",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_033"),
                "payment_method_id": cls.pay_method_type_240,
                "boleto_wallet": "101",
                "boleto_variation": "35",
                "boleto_discount_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.santander_240_boleto_discount_code_4"
                ),
                "boleto_interest_code": "2",
                "cnab_sequence_id": cls.cnab_seq_santander_240,
                "own_number_sequence_id": cls.own_number_seq_santander_240,
                "cnab_company_bank_code": "123456789012345",
                "convention_code": "1234567",
                "wallet_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.santander_240_boleto_wallet_code_5"
                ),
                "write_off_devolution_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.santander_240_boleto_write_off_devolution_3"
                ),
                "write_off_devolution_number_of_days": 0,
                "sending_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.santander_240_instruction_01"
                ),
                "write_off_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.santander_240_instruction_02"
                ),
            },
        )

        cls.cnab_config_ailos = create_with_form_l10n_br_cnab_config(
            cls.env,
            cls.common_cnab_config_values
            | {
                "name": "Banco AILOS - CNAB 240 (inbound)",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_085"),
                "payment_method_id": cls.pay_method_type_240,
                "boleto_wallet": "01",
                "boleto_variation": "35",
                "boleto_discount_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.ailos_240_boleto_discount_code_1"
                ),
                "boleto_interest_code": "2",
                "cnab_sequence_id": cls.cnab_seq_ailos,
                "own_number_sequence_id": cls.own_number_seq_ailos,
                "cnab_company_bank_code": "101004",
                "sending_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.ailos_instruction_01"
                ),
                "write_off_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.ailos_instruction_02"
                ),
            },
        )
        cls.cnab_config_ailos.write(
            {
                "liq_return_move_code_ids": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref(
                                "l10n_br_account_payment_order.ailos_240_return_06"
                            ).id,
                            cls.env.ref(
                                "l10n_br_account_payment_order.ailos_240_return_76"
                            ).id,
                            cls.env.ref(
                                "l10n_br_account_payment_order.ailos_240_return_77"
                            ).id,
                        ],
                    )
                ],
            }
        )

        cls.cnab_config_nordeste = create_with_form_l10n_br_cnab_config(
            cls.env,
            cls.common_cnab_config_values
            | {
                "name": "Banco do Nordeste - CNAB 400 (inbound)",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_004"),
                "payment_method_id": cls.pay_method_type_400,
                "boleto_wallet": "21",
                "boleto_variation": "1",
                "boleto_interest_code": "2",
                "cnab_sequence_id": cls.cnab_seq_nordeste,
                "own_number_sequence_id": cls.own_number_seq_nordeste,
                "cnab_company_bank_code": "0001222130126",
                "sending_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.nordeste_400_instruction_01"
                ),
                "write_off_code_id": cls.env.ref(
                    "l10n_br_account_payment_order.nordeste_400_instruction_02"
                ),
            },
        )

        # Diário

        # Dados necessários para a Importação do Arquivo de Retorno
        cls.journal_cef.update(
            {
                "used_for_import": True,
                "import_type": "cnab240",
                "return_auto_reconcile": True,
            }
        )

        cls.journal_unicred = create_with_form_account_journal(
            cls.env,
            {
                "name": "Banco UNICRED",
                "type": "bank",
                "code": "BNC3",
                "bank_account_id": cls.bank_account_unicred,
                "edi_format_ids": False,
            },
            [
                {
                    "name": "UNICRED CNAB 400",
                    "payment_method_id": cls.pay_method_type_400,
                }
            ],
        )
        # Método que cria com Form não tem esses campos
        cls.journal_unicred.write(
            {
                "used_for_import": True,
                "import_type": "cnab400",
                "return_auto_reconcile": True,
            }
        )

        cls.journal_brasil = create_with_form_account_journal(
            cls.env,
            {
                "name": "Banco do Brasil",
                "type": "bank",
                "code": "BNC11",
                "bank_account_id": cls.bank_account_brasil,
                "edi_format_ids": False,
            },
            [
                {
                    "name": "BB CNAB 400",
                    "payment_method_id": cls.pay_method_type_400,
                }
            ],
        )
        cls.journal_brasil.write(
            {
                "used_for_import": True,
                "import_type": "cnab400",
                "return_auto_reconcile": True,
            }
        )

        cls.journal_bradesco = create_with_form_account_journal(
            cls.env,
            {
                "name": "Banco Bradesco",
                "type": "bank",
                "code": "BNC12",
                "bank_account_id": cls.bank_account_bradesco,
                "edi_format_ids": False,
            },
            [
                {
                    "name": "Bradesco CNAB 400",
                    "payment_method_id": cls.pay_method_type_400,
                }
            ],
        )
        cls.journal_bradesco.write(
            {
                "used_for_import": True,
                "import_type": "cnab400",
                "return_auto_reconcile": True,
            }
        )

        cls.journal_sicredi = create_with_form_account_journal(
            cls.env,
            {
                "name": "Banco SICREDI",
                "type": "bank",
                "code": "BNC13",
                "bank_account_id": cls.bank_account_sicredi,
                "edi_format_ids": False,
            },
            [
                {
                    "name": "SICREDI CNAB 240",
                    "payment_method_id": cls.pay_method_type_240,
                }
            ],
        )
        cls.journal_sicredi.write(
            {
                "used_for_import": True,
                "import_type": "cnab400",
                "return_auto_reconcile": True,
            }
        )

        cls.journal_santander_400 = create_with_form_account_journal(
            cls.env,
            {
                "name": "Banco Santander CNAB 400",
                "type": "bank",
                "code": "BNC14",
                "bank_account_id": cls.bank_account_santander,
                "edi_format_ids": False,
            },
            [
                {
                    "name": "Santander CNAB 400",
                    "payment_method_id": cls.pay_method_type_400,
                },
            ],
        )
        cls.journal_santander_400.write(
            {
                "used_for_import": True,
                "import_type": "cnab400",
                "return_auto_reconcile": True,
            }
        )

        cls.journal_santander_240 = create_with_form_account_journal(
            cls.env,
            {
                "name": "Banco Santander",
                "type": "bank",
                "code": "BNC15",
                "bank_account_id": cls.bank_account_santander,
                "edi_format_ids": False,
            },
            [
                {
                    "name": "Santander CNAB 240",
                    "payment_method_id": cls.pay_method_type_240,
                },
            ],
        )
        cls.journal_santander_240.write(
            {
                "used_for_import": True,
                "import_type": "cnab240",
                "return_auto_reconcile": True,
            }
        )

        cls.journal_ailos = create_with_form_account_journal(
            cls.env,
            {
                "name": "Banco AILOS",
                "type": "bank",
                "code": "BNC16",
                "bank_account_id": cls.bank_account_ailos,
                "edi_format_ids": False,
                "used_for_import": True,
                "import_type": "cnab240",
                "return_auto_reconcile": True,
            },
            [
                {
                    "name": "AILOS CNAB 240",
                    "payment_method_id": cls.pay_method_type_240,
                }
            ],
        )
        cls.journal_ailos.write(
            {
                "used_for_import": True,
                "import_type": "cnab240",
                "return_auto_reconcile": True,
            }
        )

        cls.journal_nordeste = create_with_form_account_journal(
            cls.env,
            {
                "name": "Banco Nordeste",
                "type": "bank",
                "code": "BNC17",
                "bank_account_id": cls.bank_account_nordeste,
                "edi_format_ids": False,
                "used_for_import": True,
                "import_type": "cnab400",
                "return_auto_reconcile": True,
            },
            [
                {
                    "name": "Nordeste CNAB 400",
                    "payment_method_id": cls.pay_method_type_400,
                }
            ],
        )
        cls.journal_nordeste.write(
            {
                "used_for_import": True,
                "import_type": "cnab400",
                "return_auto_reconcile": True,
            }
        )

        # Modo de Pagamento
        cls.pay_mode_unicred = create_with_form_account_payment_mode(
            cls.env,
            cls.common_pay_mode_values
            | {
                "name": "Cobrança UNICRED 400",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_136"),
                "fixed_journal_id": cls.journal_unicred,
                "payment_method_id": cls.pay_method_type_400,
                "cnab_config_id": cls.cnab_config_unicred,
            },
        )

        cls.pay_mode_brasil = create_with_form_account_payment_mode(
            cls.env,
            cls.common_pay_mode_values
            | {
                "name": "Cobrança Banco do Brasil 400",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_001"),
                "fixed_journal_id": cls.journal_brasil,
                "payment_method_id": cls.pay_method_type_400,
                "cnab_config_id": cls.cnab_config_brasil,
            },
        )

        cls.pay_mode_bradesco = create_with_form_account_payment_mode(
            cls.env,
            cls.common_pay_mode_values
            | {
                "name": "Cobrança Bradesco 400",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_237"),
                "fixed_journal_id": cls.journal_bradesco,
                "payment_method_id": cls.pay_method_type_400,
                "cnab_config_id": cls.cnab_config_bradesco,
            },
        )

        cls.pay_mode_sicredi = create_with_form_account_payment_mode(
            cls.env,
            cls.common_pay_mode_values
            | {
                "name": "Cobrança SICREDI 240",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_748"),
                "fixed_journal_id": cls.journal_sicredi,
                "payment_method_id": cls.pay_method_type_240,
                "cnab_config_id": cls.cnab_config_sicredi,
            },
        )

        cls.pay_mode_santander_400 = create_with_form_account_payment_mode(
            cls.env,
            cls.common_pay_mode_values
            | {
                "name": "Cobrança Santander 400",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_033"),
                "fixed_journal_id": cls.journal_santander_400,
                "payment_method_id": cls.pay_method_type_400,
                "cnab_config_id": cls.cnab_config_santander_400,
            },
        )

        cls.pay_mode_santander_240 = create_with_form_account_payment_mode(
            cls.env,
            cls.common_pay_mode_values
            | {
                "name": "Cobrança Santander 240",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_033"),
                "fixed_journal_id": cls.journal_santander_240,
                "payment_method_id": cls.pay_method_type_240,
                "cnab_config_id": cls.cnab_config_santander_240,
            },
        )

        cls.pay_mode_ailos = create_with_form_account_payment_mode(
            cls.env,
            cls.common_pay_mode_values
            | {
                "name": "Cobrança AILOS 240",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_085"),
                "fixed_journal_id": cls.journal_ailos,
                "payment_method_id": cls.pay_method_type_240,
                "cnab_config_id": cls.cnab_config_ailos,
            },
        )

        cls.pay_mode_nordeste = create_with_form_account_payment_mode(
            cls.env,
            cls.common_pay_mode_values
            | {
                "name": "Cobrança Nordeste 400",
                "bank_id": cls.env.ref("l10n_br_base.res_bank_004"),
                "fixed_journal_id": cls.journal_nordeste,
                "payment_method_id": cls.pay_method_type_400,
                "cnab_config_id": cls.cnab_config_nordeste,
            },
        )

        # Faturas/Invoice/account.move
        cls.invoice_unicred_400_1 = create_with_form_account_move(
            cls.env,
            cls.inv_common_values
            | {
                "name": "UNICRED 400 - Valor Menor",
                "payment_mode_id": cls.pay_mode_unicred,
            },
            cls.inv_line_common_values,
        )
        # Altera o valor total para 1000
        for line in cls.invoice_unicred_400_1.invoice_line_ids:
            line.tax_ids = False

        cls.invoice_unicred_400_2 = create_with_form_account_move(
            cls.env,
            cls.inv_common_values
            | {
                "name": "UNICRED 400 - Valor Maior",
                "payment_mode_id": cls.pay_mode_unicred,
            },
            cls.inv_line_common_values,
        )
        # Altera o valor total para 1000
        for line in cls.invoice_unicred_400_2.invoice_line_ids:
            line.tax_ids = False

        cls.invoice_itau_400 = create_with_form_account_move(
            cls.env,
            cls.inv_common_values
            | {
                "name": "Itau CNAB 400",
                "payment_mode_id": cls.pay_mode_itau_400,
            },
            cls.inv_line_common_values,
        )

        cls.invoice_brasil_400 = create_with_form_account_move(
            cls.env,
            cls.inv_common_values
            | {
                "name": "Banco do Brasil CNAB 400",
                "payment_mode_id": cls.pay_mode_brasil,
            },
            cls.inv_line_common_values,
        )

        cls.invoice_bradesco_400 = create_with_form_account_move(
            cls.env,
            cls.inv_common_values
            | {
                "name": "Banco Bradesco CNAB 400",
                "payment_mode_id": cls.pay_mode_bradesco,
            },
            cls.inv_line_common_values,
        )

        cls.invoice_sicredi_240 = create_with_form_account_move(
            cls.env,
            cls.inv_common_values
            | {
                "name": "Banco SICREDI 240",
                "payment_mode_id": cls.pay_mode_sicredi,
            },
            cls.inv_line_common_values,
        )

        cls.invoice_santander_400 = create_with_form_account_move(
            cls.env,
            cls.inv_common_values
            | {
                "name": "Santander CNAB 400",
                "payment_mode_id": cls.pay_mode_santander_400,
            },
            cls.inv_line_common_values,
        )

        cls.invoice_santander_240 = create_with_form_account_move(
            cls.env,
            cls.inv_common_values
            | {
                "name": "Santander CNAB 240",
                "payment_mode_id": cls.pay_mode_santander_240,
            },
            cls.inv_line_common_values,
        )

        cls.invoice_ailos_240 = create_with_form_account_move(
            cls.env,
            cls.inv_common_values
            | {
                "name": "AILOS CNAB 240",
                "payment_mode_id": cls.pay_mode_ailos,
            },
            cls.inv_line_common_values,
        )
        # Altera o valor total para 1000
        for line in cls.invoice_ailos_240.invoice_line_ids:
            line.tax_ids = False

        cls.invoice_nordeste_400 = create_with_form_account_move(
            cls.env,
            cls.inv_common_values
            | {
                "name": "Nordeste CNAB 400",
                "payment_mode_id": cls.pay_mode_nordeste,
            },
            cls.inv_line_common_values,
        )

    def _run_invoice_and_order_brcobranca(self, invoice):
        if not self._check_ci_no_brcobranca():
            self._invoice_confirm_workflow(invoice)
            payment_order = self._get_draft_payment_order(invoice)
            self._run_payment_order_workflow(payment_order, test_not_create_file=False)

    def _run_import_return_file(self, test_file, journal):
        file_name = get_resource_path(
            "l10n_br_account_payment_brcobranca",
            "tests",
            "data",
            test_file,
        )

        with open(file_name, "rb") as f:
            content = f.read()
            self.wizard = self.env["credit.statement.import"].create(
                {
                    "journal_id": journal.id,
                    "input_statement": base64.b64encode(content),
                    "file_name": os.path.basename(file_name),
                }
            )
            action = self.wizard.import_statement()
            log_view_ref = self.ref(
                "l10n_br_account_payment_order.l10n_br_cnab_return_log_form_view"
            )
            if action["views"] == [(log_view_ref, "form")]:
                # Se não for um codigo cnab de liquidação retorna
                # apenas o LOG criado.
                return self.env["l10n_br_cnab.return.log"].browse(action["res_id"])
            else:
                # Se for um codigo cnab de liquidação retorna
                # as account.move criadas.
                return self.env["account.move"].browse(action["res_id"])

    def _check_ci_no_brcobranca(self):
        if os.environ.get("CI_NO_BRCOBRANCA"):
            _logger.warning(
                "Test skipped because Enviroment are setting for CI_NO_BRCOBRANCA."
            )
            return True
