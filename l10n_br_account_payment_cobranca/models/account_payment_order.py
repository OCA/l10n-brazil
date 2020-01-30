# © 2012 KMEE INFORMATICA LTDA
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
#   @author  Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import logging

from odoo import api, fields, models

from ..constantes import (CODIGO_INSTRUCAO_MOVIMENTO, FORMA_LANCAMENTO,
                          INDICATIVO_FORMA_PAGAMENTO, TIPO_MOVIMENTO,
                          TIPO_SERVICO)

_logger = logging.getLogger(__name__)


class PaymentOrder(models.Model):
    _inherit = "account.payment.order"

    active = fields.Boolean(string="Ativo", default=True)

    file_number = fields.Integer(string="Número sequencial do arquivo")

    cnab_file = fields.Binary(string="CNAB File", readonly=True)

    cnab_filename = fields.Char("CNAB Filename")

    tipo_servico = fields.Selection(
        selection=TIPO_SERVICO,
        string="Tipo de Serviço",
        help="Campo G025 do CNAB",
        default="30",
    )
    forma_lancamento = fields.Selection(
        selection=FORMA_LANCAMENTO, string="Forma Lançamento", help="Campo G029 do CNAB"
    )
    codigo_convenio = fields.Char(
        size=20,
        string="Código do Convênio no Banco",
        help="Campo G007 do CNAB",
        default="0001222130126",
    )
    indicativo_forma_pagamento = fields.Selection(
        selection=INDICATIVO_FORMA_PAGAMENTO,
        string="Indicativo de Forma de Pagamento",
        help="Campo P014 do CNAB",
        default="01",
    )
    tipo_movimento = fields.Selection(
        selection=TIPO_MOVIMENTO,
        string="Tipo de Movimento",
        help="Campo G060 do CNAB",
        default="0",
    )
    codigo_instrucao_movimento = fields.Selection(
        selection=CODIGO_INSTRUCAO_MOVIMENTO,
        string="Código da Instrução para Movimento",
        help="Campo G061 do CNAB",
        default="0",
    )
    bank_line_error_ids = fields.One2many(
        comodel_name="bank.payment.line",
        inverse_name="order_id",
        string="Bank Payment Error Lines",
        readonly=True,
        domain=[("is_erro_exportacao", "=", True)],
    )

    def _confirm_debit_orders_api(self):
        """
        Method create to confirm all bank_api exclusive account.payment.order
        :return:
        """
        _logger.info("_confirm_debit_orders_api()")

        order_ids = self.search(
            [("active", "=", False), ("state", "=", "draft"), ("name", "ilike", "api")]
        )

        for order_id in order_ids:
            try:
                order_id.draft2open()
                order_id.active = True
            except Exception as e:
                _logger.warn(str(e))

    @api.model
    def _prepare_bank_payment_line(self, paylines):
        result = super(PaymentOrder, self)._prepare_bank_payment_line(paylines)
        result["nosso_numero"] = paylines.nosso_numero
        result["numero_documento"] = paylines.numero_documento
        result["identificacao_titulo_empresa"] = paylines.identificacao_titulo_empresa
        result["ultimo_estado_cnab"] = paylines.move_line_id.state_cnab
        return result

    @api.multi
    def open2generated(self):
        result = super(PaymentOrder, self).open2generated()

        if self.bank_line_error_ids:
            self.message_post(
                "Erro ao gerar o arquivo," ' verifique a aba "Linhas com problemas"'
            )
            return False
        self.message_post("Arquivo gerado com sucesso")
        return result
