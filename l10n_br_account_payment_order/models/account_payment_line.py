# Copyright (C) 2016-Today - KMEE (<http://kmee.com.br>).
#  Luis Felipe Miléo - mileo@kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants import (
    AVISO_FAVORECIDO,
    CODIGO_FINALIDADE_TED,
    COMPLEMENTO_TIPO_SERVICO,
    TIPO_MOVIMENTO,
    TIPO_SERVICO,
)

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base import misc
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")


class AccountPaymentLine(models.Model):
    _inherit = "account.payment.line"

    PIX_TRANSFER_TYPES = [
        ("checking", _("Checking Account (Conta Corrente)")),
        ("saving", _("Saving Account (Conta Poupança)")),
        ("payment", _("Prepaid Payment Account (Conta Pagamento)")),
        ("pix_key", _("Instant Payment Key (Chave Pix)")),
    ]

    digitable_line = fields.Char(
        string="Linha Digitável",
    )

    percent_interest = fields.Float(
        string="Percentual de Juros",
        digits="Account",
    )

    amount_interest = fields.Float(
        string="Valor Juros",
        compute="_compute_interest",
        digits="Account",
    )

    own_number = fields.Char(
        string="Nosso Numero",
    )

    document_number = fields.Char(
        string="Número documento",
    )

    barcode = fields.Char(
        string="Barcode", help="This field is used in the payment of supplier slips"
    )

    company_title_identification = fields.Char(
        string="Identificação Titulo Empresa",
    )

    doc_finality_code = fields.Selection(
        selection=COMPLEMENTO_TIPO_SERVICO,
        string="Complemento do Tipo de Serviço",
        help="Campo P005 do CNAB",
    )

    ted_finality_code = fields.Selection(
        selection=CODIGO_FINALIDADE_TED,
        string="Código Finalidade da TED",
        help="Campo P011 do CNAB",
    )

    partner_pix_id = fields.Many2one(
        string="Pix Key",
        comodel_name="res.partner.pix",
    )

    pix_transfer_type = fields.Selection(
        selection=PIX_TRANSFER_TYPES,
        help="Pix transfer type identification",
        compute="_compute_pix_transfer_type",
    )

    service_type = fields.Selection(
        selection=TIPO_SERVICO,
        string="Tipo de Serviço",
        help="Campo G025 do CNAB",
        default="30",
    )

    complementary_finality_code = fields.Char(
        string="Código de finalidade complementar",
        size=2,
        help="Campo P013 do CNAB",
    )

    favored_warning = fields.Selection(
        selection=AVISO_FAVORECIDO,
        string="Aviso ao Favorecido",
        help="Campo P006 do CNAB",
        default="0",
    )

    rebate_value = fields.Monetary(
        string="Valor do Abatimento",
        help="Campo G045 do CNAB",
    )

    discount_value = fields.Monetary(
        string="Valor do Desconto",
        help="Campo G046 do CNAB",
    )

    interest_value = fields.Monetary(
        string="Valor da Mora",
        help="Campo G047 do CNAB",
    )

    fee_value = fields.Monetary(
        string="Valor da Multa",
        help="Campo G048 do CNAB",
    )

    payment_mode_id = fields.Many2one(
        comodel_name="account.payment.mode",
        related="order_id.payment_mode_id",
    )

    payment_mode_domain = fields.Selection(
        related="payment_mode_id.payment_mode_domain",
    )

    # Campo não usado no BRCobranca
    movement_type = fields.Selection(
        selection=TIPO_MOVIMENTO,
        string="Tipo de Movimento",
        help="Campo G060 do CNAB",
        default="0",
    )

    mov_instruction_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Código da Instrução para Movimento",
        help="Campo G061 do CNAB",
    )

    # Usados para deixar invisiveis/somente leitura
    # os campos relacionados ao CNAB
    payment_method_id = fields.Many2one(
        comodel_name="account.payment.method",
        related="payment_mode_id.payment_method_id",
        string="Payment Method",
    )

    payment_method_code = fields.Char(
        related="payment_method_id.code",
        readonly=True,
        store=True,
        string="Payment Method Code",
    )

    communication_type = fields.Selection(
        selection_add=[
            ("cnab", "CNAB"),
        ],
        ondelete={"cnab": "set default"},
    )

    # No caso de Ordens de Pagto vinculadas devido o
    # ondelete=restrict no campo move_line_id do account.payment.line
    # não é possível apagar uma move que já tenha uma Ordem de
    # Pagto confirmada ( processo chamado pelo action_cancel objeto
    # account.invoice ), acontece o erro abaixo de constraint:
    # psycopg2.IntegrityError: update or delete on table
    # "account_move_line" violates foreign key constraint
    # "account_payment_line_move_line_id_fkey" on table
    # "account_payment_line"
    # TODO: Verificar a possibilidade de alteração no
    #  modulo account_payment_order na v14
    move_line_id = fields.Many2one(ondelete=None)
    ml_maturity_date = fields.Date(related=None)
    # Para manter a rastreabilidade está sendo adicionado uma relação
    # com a account.invoice referente, já que a AML pode ser apagada
    move_id = fields.Many2one(comodel_name="account.move", string="Fatura")

    @api.depends("percent_interest", "amount_currency", "currency_id")
    def _compute_interest(self):
        for record in self:
            record.amount_interest = record.currency_id.round(
                record.amount_currency * (record.percent_interest / 100)
            )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        mode = (
            self.env["account.payment.order"]
            .browse(self.env.context.get("order_id"))
            .payment_mode_id
        )
        if mode.doc_finality_code:
            res.update({"doc_finality_code": mode.doc_finality_code})
        if mode.ted_finality_code:
            res.update({"ted_finality_code": mode.ted_finality_code})
        if mode.complementary_finality_code:
            res.update(
                {"complementary_finality_code": mode.complementary_finality_code}
            )
        if mode.favored_warning:
            res.update({"favored_warning": mode.favored_warning})

        return res

    def draft2open_payment_line_check(self):
        """
        Override to add brazilian validations
        """
        res = super(AccountPaymentLine, self).draft2open_payment_line_check()
        self._check_pix_transfer_type()
        return res

    @api.onchange("partner_id")
    def partner_id_change(self):
        res = super(AccountPaymentLine, self).partner_id_change()
        partner_pix = False
        if self.partner_id.pix_key_ids:
            partner_pix = self.partner_id.pix_key_ids[0]
        self.partner_pix_id = partner_pix
        return res

    def _compute_pix_transfer_type(self):
        for line in self:
            line.pix_transfer_type = False
            if line.payment_mode_domain != "pix_transfer":
                return
            if line.partner_pix_id:
                line.pix_transfer_type = "pix_key"
            elif line.partner_bank_id:
                acc_type = line.partner_bank_id.transactional_acc_type
                line.pix_transfer_type = acc_type

    def _check_pix_transfer_type(self):
        for rec in self:
            if (
                rec.payment_mode_domain == "pix_transfer"
                and not rec.partner_pix_id
                and not rec.partner_bank_id.transactional_acc_type
            ):
                raise UserError(
                    _(
                        "When the payment method is pix transfer, a pix key must be "
                        "informed, or the bank account with the type of account.\n"
                        f"Payment Line: {rec.name}"
                    )
                )

    # TODO: Implementar métodos para outros tipos cnab.
    #   _prepare_pagamento_line_vals
    #   _prepare_debito_automatico_line_vals
    #   _prepare_[...]_line_vals

    def _prepare_boleto_line_vals(self):
        return {
            "valor": self.amount_currency,
            "data_vencimento": self.date.strftime("%Y/%m/%d"),
            "nosso_numero": self.own_number,
            "documento_sacado": misc.punctuation_rm(self.partner_id.cnpj_cpf),
            "nome_sacado": self.partner_id.legal_name.strip()[:40],
            "numero": self.document_number,
            "endereco_sacado": str(
                self.partner_id.street_name + ", " + str(self.partner_id.street_number)
            )[:40],
            "bairro_sacado": self.partner_id.district.strip(),
            "cep_sacado": misc.punctuation_rm(self.partner_id.zip),
            "cidade_sacado": self.partner_id.city_id.name,
            "uf_sacado": self.partner_id.state_id.code,
            # Codigo da Ocorrencia usado pode variar por Banco, CNAB e operação
            # ex.: UNICRED 240/400 é 01 - Remessa*, 02 - Pedido de Baixa e
            # 06 - Alteração de vencimento . Veja que está sendo informado
            # o campo Code do objeto.
            "identificacao_ocorrencia": self.mov_instruction_code_id.code,
        }


class BankPaymentLine(models.Model):
    _name = "bank.payment.line"
    _description = "Bank Payment Lines"
    # TODO: Sem isso acontece o erro abaixo, por isso é preciso incluir o objeto
    #  bank.payment.line vazio e rodar um update,
    #  Em outro PR o objeto será removido e assim em um terceiro update vai
    #  limpar o Warning. Para evitar problemas o melhor será remover o objeto
    #  na migração de versão v15 ou v16.
    #  LOG com erro.
    #  Referencia https://github.com/odoo/odoo/issues/44767
    #
    # 2023-03-10 21:15:22,323 72 INFO db odoo.addons.base.models.ir_model:
    # Deleting 1622@ir.model.fields.selection (
    # l10n_br_account_payment_order.
    # selection__bank_payment_line__last_cnab_state__done)
    # 2023-03-10 21:15:22,326 72 WARNING db odoo.modules.loading:
    # Transient module states were reset
    # 2023-03-10 21:15:22,328 72 ERROR db odoo.modules.registry:
    # Failed to load registry
    # 2023-03-10 21:15:22,328 72 CRITICAL db odoo.service.server:
    # Failed to initialize database `db`.
    # Traceback (most recent call last):
    #   File "/odoo/src/odoo/service/server.py", line 1201, in preload_registries
    #     registry = Registry.new(dbname, update_module=update_module)
    #   File "/odoo/src/odoo/modules/registry.py", line 89, in new
    #     odoo.modules.load_modules(registry._db, force_demo, status, update_module)
    #   File "/odoo/src/odoo/modules/loading.py", line 505, in load_modules
    #     env['ir.model.data']._process_end(processed_modules)
    #   File "/odoo/src/odoo/addons/base/models/ir_model.py",
    #   line 2310, in _process_end
    #     self._process_end_unlink_record(record)
    #   File "/odoo/src/odoo/addons/base/models/ir_model.py",
    #   line 2233, in _process_end_unlink_record
    #     record.unlink()
    #   File "/odoo/src/odoo/addons/base/models/ir_model.py",
    #   line 1380, in unlink
    #     self._process_ondelete()
    #   File "/odoo/src/odoo/addons/base/models/ir_model.py",
    #   line 1418, in _process_ondelete
    #     Model = self.env[selection.field_id.model]
    #   File "/odoo/src/odoo/api.py", line 476, in __getitem__
    #     return self.registry[model_name]._browse(self, (), ())
    #   File "/odoo/src/odoo/modules/registry.py",
    #   line 177, in __getitem__
    #     return self.models[model_name]
    # KeyError: 'bank.payment.line'
