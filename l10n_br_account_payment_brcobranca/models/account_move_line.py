# -*- coding: utf-8 -*-
# Copyright 2017 Akretion
# @author Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime

from odoo import models, api, _
from odoo.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)


class BoletoWrapper(object):
    def __init__(self, boleto_cnab_api_data):
        # wrap the object
        # self._wrapped_obj = obj
        self.boleto_cnab_api_data = boleto_cnab_api_data

    def __getattr__(self, attr):
        # see if this object has attr
        # NOTE do not use hasattr, it goes into
        # infinite recurrsion
        if attr in self.__dict__:
            # this object has it
            return getattr(self, attr)
        # proxy to the wrapped object
        return getattr(self._wrapped_obj, attr)


dict_brcobranca_bank = {
    '001': 'banco_brasil',
    '041': 'banrisul',
    '237': 'bradesco',
    '104': 'caixa',
    '399': 'hsbc',
    '341': 'itau',
    '033': 'santander',
    '748': 'sicred',
    '004': 'banco_nordeste',
    '021': 'banestes',
    '756': 'sicoob',
    '136': 'unicred',
}

dict_brcobranca_currency = {
    'R$': '9',
}


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    # see the list of brcobranca boleto fields:
    # https://github.com/kivanio/brcobranca/blob/master/lib/
    # brcobranca/boleto/base.rb
    # and test a here:
    # https://github.com/kivanio/brcobranca/blob/master/spec/
    # brcobranca/boleto/itau_spec.rb

    @api.multi
    def send_payment(self):

        # super(AccountMoveLine, self).send_payment()
        wrapped_boleto_list = []

        for move_line in self:
            bank_account = \
                move_line.payment_mode_id.fixed_journal_id.bank_account_id
            if bank_account.bank_id.code_bc in dict_brcobranca_bank:
                bank_name_brcobranca = dict_brcobranca_bank[
                                           bank_account.bank_id.code_bc],
            else:
                raise UserError(
                    _('The Bank %s is not implemented in BRCobranca.') %
                    bank_account.bank_id.name)

            precision = self.env['decimal.precision']
            precision_account = precision.precision_get('Account')

            boleto_cnab_api_data = {
                  'bank': bank_name_brcobranca[0],
                  'valor': str("%.2f" % move_line.debit),
                  'cedente': move_line.company_id.partner_id.legal_name,
                  'cedente_endereco':
                      move_line.company_id.partner_id.street or '' + ', ' +
                      move_line.company_id.partner_id.street_number or '' + ' - ' +
                      move_line.company_id.partner_id.district or '' + ' - ' +
                      move_line.company_id.partner_id.city_id.name or ''
                      + ' - ' + 'CEP:' + move_line.company_id.partner_id.zip or ''
                      + ' - ' + move_line.company_id.partner_id.state_id.code or '',
                  'documento_cedente': move_line.company_id.cnpj_cpf,
                  'sacado': move_line.partner_id.legal_name,
                  'sacado_documento': move_line.partner_id.cnpj_cpf,
                  'agencia': bank_account.bra_number,
                  'conta_corrente': bank_account.acc_number,
                  'convenio': move_line.payment_mode_id.boleto_convenio,
                  'carteira': str(move_line.payment_mode_id.boleto_carteira),
                  'nosso_numero': int(''.join(
                      i for i in move_line.nosso_numero if i.isdigit())),
                  'documento_numero': move_line.numero_documento,
                  'data_vencimento':
                      move_line.date_maturity.strftime('%Y/%m/%d'),
                  'data_documento':
                      move_line.invoice_id.date_invoice.strftime('%Y/%m/%d'),
                  'especie': move_line.payment_mode_id.boleto_especie,
                  'moeda': dict_brcobranca_currency['R$'],
                  'aceite': move_line.payment_mode_id.boleto_aceite,
                  'sacado_endereco':
                      move_line.partner_id.street or '' + ', ' +
                      move_line.partner_id.street_number or '' + ' ' +
                      move_line.partner_id.city_id.name or '' + ' - ' +
                      move_line.partner_id.state_id.name or '',
                  'data_processamento':
                      move_line.invoice_id.date_invoice.strftime('%Y/%m/%d'),
                  'instrucao1': move_line.payment_mode_id.instrucoes or '',
            }

            # Instrução de Juros
            if move_line.payment_mode_id.boleto_perc_mora > 0.0:
                instrucao_juros_tmp = "APÓS VENCIMENTO COBRAR PERCENTUAL"
                if move_line.payment_mode_id.instrucao_boleto_perc_mora:
                    instrucao_juros_tmp = \
                        move_line.payment_mode_id.instrucao_boleto_perc_mora

                valor_juros = round(
                    move_line.debit *
                    ((move_line.payment_mode_id.boleto_perc_mora / 100)
                     / 30), precision_account)
                instrucao_juros = (
                    instrucao_juros_tmp +
                    " DE %s %% AO MÊS ( R$ %s AO DIA )"
                    % (('%.2f' %
                        move_line.payment_mode_id.boleto_perc_mora
                        ).replace('.', ','),
                       ('%.2f' % valor_juros).replace('.', ',')))
                boleto_cnab_api_data.update({
                    'instrucao3': instrucao_juros,
                })

            # Instrução Multa
            if move_line.payment_mode_id.boleto_perc_multa > 0.0:
                instrucao_multa_tmp = "APÓS VENCIMENTO COBRAR MULTA"
                if move_line.payment_mode_id.instrucao_boleto_perc_multa:
                    instrucao_multa_tmp = \
                        move_line.payment_mode_id.instrucao_boleto_perc_multa

                valor_multa = round(move_line.debit * (
                    (move_line.payment_mode_id.boleto_perc_multa / 100)
                ), precision_account)
                instrucao_multa = (
                    instrucao_multa_tmp +
                    " DE %s %% ( R$ %s )" %
                    (('%.2f' % move_line.payment_mode_id.boleto_perc_multa
                      ).replace('.', ','),
                     ('%.2f' % valor_multa).replace('.', ',')))
                boleto_cnab_api_data.update({
                    'instrucao4': instrucao_multa,
                })

            # Instrução Desconto
            if move_line.payment_term_id.discount_perc > 0.0:
                instrucao_desconto_vencimento_tmp = \
                    'CONCEDER ABATIMENTO PERCENTUAL DE'
                if move_line.payment_term_id.instrucao_discount_perc:
                    instrucao_desconto_vencimento_tmp = \
                        move_line.payment_term_id.instrucao_discount_perc
                valor_desconto = round(
                    move_line.debit * (
                        move_line.payment_term_id.discount_perc / 100),
                    precision_account)
                instrucao_desconto_vencimento = (
                    instrucao_desconto_vencimento_tmp + ' %s %% '
                    'ATÉ O VENCIMENTO EM %s ( R$ %s )'
                    % (('%.2f' % move_line.payment_term_id.discount_perc
                        ).replace('.', ','),
                       move_line.date_maturity.strftime('%d/%m/%Y'),
                       ('%.2f' % valor_desconto).replace('.', ',')
                       ))
                boleto_cnab_api_data.update({
                    'instrucao5': instrucao_desconto_vencimento,
                })

            if bank_account.bank_id.code_bc in ('021', '004'):
                boleto_cnab_api_data.update({
                    'digito_conta_corrente':
                        move_line.payment_mode_id.bank_id.acc_number_dig,
                })

            # Fields used in Sicredi/Unicred and Sicoob Banks
            if bank_account.bank_id.code_bc == '748':
                boleto_cnab_api_data.update({
                    'byte_idt': move_line.payment_mode_id.boleto_byte_idt,
                    'posto': move_line.payment_mode_id.boleto_posto,
                })

            wrapped_boleto_list.append(BoletoWrapper(boleto_cnab_api_data))
        return wrapped_boleto_list
