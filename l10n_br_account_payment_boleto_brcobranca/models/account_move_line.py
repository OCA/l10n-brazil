# -*- coding: utf-8 -*-
# Copyright 2017 Akretion
# @author Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime

from openerp import models, api, _
from openerp.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)


class BoletoWrapper(object):
    def __init__(self, obj, boleto_cnab_api_data):
        # wrap the object
        self._wrapped_obj = obj
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
    '748': 'sicredi',
    # banks implemented in brcobranca but not in Python:
    # '004': 'banco_nordeste',
    # '021': 'banestes',
    # '756': 'sicoob',
}

dict_brcobranca_currency = {
    'R$': '9',
}


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    # see the list of brcobranca boleto fields:
    # https://github.com/kivanio/brcobranca/blob/master/lib/brcobranca/boleto/base.rb
    # and test a here:
    # https://github.com/kivanio/brcobranca/blob/master/spec/brcobranca/boleto/itau_spec.rb

    @api.multi
    def send_payment(self):
        wrapped_boleto_list = []

        for move_line in self:
            if move_line.payment_mode_id.bank_id.bank.bic in \
                    dict_brcobranca_bank:
                bank_name_brcobranca = dict_brcobranca_bank[
                               move_line.payment_mode_id.bank_id.bank.bic],
            else:
                raise UserError(
                    _('The Bank %s is not implemented in BRCobranca.') %
                    move_line.payment_mode_id.bank_id.bank.name)
            boleto_list = super(AccountMoveLine, move_line).send_payment()

            precision = self.env['decimal.precision']
            precision_account = precision.precision_get('Account')
            instrucao_juros = ''
            if move_line.payment_mode_id.cnab_percent_interest:
                valor_juros = round(
                    move_line.debit *
                    ((move_line.payment_mode_id.cnab_percent_interest / 100)
                     / 30), precision_account)
                instrucao_juros = (
                    "APÓS VENCIMENTO COBRAR PERCENTUAL"
                    " DE %s %% AO MÊS ( R$ %s AO DIA )"
                    % (('%.2f' %
                        move_line.payment_mode_id.cnab_percent_interest
                        ).replace('.', ','),
                       ('%.2f' % valor_juros).replace('.', ',')))

            instrucao_multa = ''
            if move_line.payment_mode_id.boleto_perc_mora:
                valor_multa = round(move_line.debit * (
                    (move_line.payment_mode_id.boleto_perc_mora / 100)
                ), precision_account)
                instrucao_multa = (
                    "APÓS VENCIMENTO COBRAR MULTA "
                    "PERCENTUAL DE %s %% ( R$ %s )" %
                    (('%.2f' % move_line.payment_mode_id.boleto_perc_mora
                      ).replace('.', ','),
                     ('%.2f' % valor_multa).replace('.', ',')))

            instrucao_desconto_vencimento = ''
            if move_line.payment_term_id.discount_perc:
                valor_desconto = round(
                    move_line.debit * (
                        move_line.payment_term_id.discount_perc / 100),
                    precision_account)
                instrucao_desconto_vencimento = (
                    'CONCEDER ABATIMENTO PERCENTUAL DE %s %% '
                    'ATÉ O VENCIMENTO EM %s ( R$ %s )'
                    % (('%.2f' % move_line.payment_term_id.discount_perc
                        ).replace('.', ','),
                       datetime.strptime(
                           move_line.date_maturity,
                           '%Y-%m-%d').strftime('%d/%m/%Y'),
                       ('%.2f' % valor_desconto).replace('.', ',')
                       ))

            for boleto in boleto_list:
                boleto_cnab_api_data = {
                      'bank': bank_name_brcobranca[0],
                      'valor': str("%.2f" % move_line.debit),
                      'cedente': move_line.company_id.partner_id.legal_name,
                      'cedente_endereco':
                          move_line.company_id.partner_id.street + ', ' +
                          move_line.company_id.partner_id.number + ' - ' +
                          move_line.company_id.partner_id.district + ' - ' +
                          move_line.company_id.partner_id.l10n_br_city_id.name + ' - ' +
                          'CEP:' + move_line.company_id.partner_id.zip + ' - ' +
                          move_line.company_id.partner_id.state_id.code,
                      'documento_cedente': move_line.company_id.cnpj_cpf,
                      'sacado': move_line.partner_id.legal_name,
                      'sacado_documento': move_line.partner_id.cnpj_cpf,
                      'agencia': move_line.payment_mode_id.bank_id.bra_number,
                      'conta_corrente':
                          move_line.payment_mode_id.bank_id.acc_number,
                      'convenio': move_line.payment_mode_id.boleto_convenio,
                      'carteira': str(move_line.payment_mode_id.boleto_carteira),
                      'nosso_numero': int(''.join(
                          i for i in move_line.boleto_own_number if i.isdigit())),
                      'documento_numero': str(move_line.name).encode('utf-8'),
                      'data_vencimento': datetime.strptime(
                          move_line.date_maturity,
                          '%Y-%m-%d').strftime('%Y/%m/%d'),
                      'data_documento': datetime.strptime(
                          move_line.invoice.date_invoice, '%Y-%m-%d').strftime(
                          '%Y/%m/%d'),
                      'especie': move_line.payment_mode_id.boleto_especie,
                      'moeda': dict_brcobranca_currency[boleto.especie],
                      'aceite': move_line.payment_mode_id.boleto_aceite,
                      'sacado_endereco':
                          move_line.partner_id.street + ', ' +
                          move_line.partner_id.number + ' ' +
                          move_line.partner_id.l10n_br_city_id.name + ' - ' +
                          move_line.partner_id.state_id.name,
                      'data_processamento': datetime.strptime(
                          move_line.invoice.date_invoice, '%Y-%m-%d').strftime(
                          '%Y/%m/%d'),
                      'instrucao1': move_line.payment_mode_id.instrucoes or '',
                      'instrucao3': instrucao_juros,
                      'instrucao4': instrucao_multa,
                      'instrucao5': instrucao_desconto_vencimento,
                }
                wrapped_boleto_list.append(
                    BoletoWrapper(boleto, boleto_cnab_api_data))
        return wrapped_boleto_list
