# © 2012 KMEE INFORMATICA LTDA
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
#   @author  Hendrix Costa <hendrix.costa@kmee.com.br>
# Copyright (C) 2020 - KMEE (<http://kmee.com.br>).
#  author Daniel Sadamo <daniel.sadamo@kmee.com.br>
# Copyright (C) 2020 - Akretion (<http://akretion.com.br>).
#  author Magno Costa <magno.costa@akretion.com.br>
#  author Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

from ..constants import (
    FORMA_LANCAMENTO,
    INDICATIVO_FORMA_PAGAMENTO,
    TIPO_SERVICO,
)

_logger = logging.getLogger(__name__)


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    file_number = fields.Integer(
        string='Número sequencial do arquivo',
    )

    cnab_file = fields.Binary(
        string='CNAB File',
        readonly=True,
    )

    cnab_filename = fields.Char(
        string='CNAB Filename',
    )

    service_type = fields.Selection(
        selection=TIPO_SERVICO,
        string='Tipo de Serviço',
        help='Campo G025 do CNAB',
        default='30',
    )

    release_form = fields.Selection(
        selection=FORMA_LANCAMENTO,
        string='Forma Lançamento',
        help='Campo G029 do CNAB',
    )

    code_convetion = fields.Char(
        related='payment_mode_id.code_convetion',
        help='Campo G007 do CNAB',
    )

    indicative_form_payment = fields.Selection(
        selection=INDICATIVO_FORMA_PAGAMENTO,
        string='Indicativo de Forma de Pagamento',
        help='Campo P014 do CNAB',
        default='01',
    )

    bank_line_error_ids = fields.One2many(
        comodel_name='bank.payment.line',
        inverse_name='order_id',
        string='Bank Payment Error Lines',
        readonly=True,
        domain=[('is_export_error', '=', True)],
    )

    # Usados para deixar invisiveis/somente leitura
    # os campos relacionados ao CNAB
    payment_method_code = fields.Char(
        related='payment_method_id.code',
        readonly=True,
        store=True,
        string='Payment Method Code'
    )

    @api.model
    def _prepare_bank_payment_line(self, paylines):
        result = super()._prepare_bank_payment_line(paylines)
        result['own_number'] = paylines[0].own_number
        result['document_number'] = paylines[0].document_number
        result['company_title_identification'] =\
            paylines[0].company_title_identification
        result['last_cnab_state'] = paylines[0].move_line_id.cnab_state
        result['mov_instruction_code_id'] = \
            paylines[0].move_line_id.mov_instruction_code_id.id
        return result

    @api.multi
    def open2generated(self):
        result = super().open2generated()

        for record in self:
            # TODO - exemplos de caso de uso ? Qdo isso ocorre ?
            #  Já não gera erro ao tentar criar o arquivo ?
            if record.bank_line_error_ids:
                record.message_post(
                    body=('Erro ao gerar o arquivo, '
                          'verifique a aba Linhas com problemas.')
                )
                for payment_line in record.payment_line_ids:
                    payment_line.move_line_id.cnab_state = 'exporting_error'
                continue
            else:
                for line in self.payment_line_ids:
                    if line.move_line_id:
                        line.move_line_id.bank_payment_line_id = \
                            line.bank_line_id
                record.message_post(body='Arquivo gerado com sucesso.')

        return result
