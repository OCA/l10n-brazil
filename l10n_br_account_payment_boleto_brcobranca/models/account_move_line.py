# -*- coding: utf-8 -*-
# Copyright 2017 Akretion
# @author Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import date

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
            for boleto in boleto_list:
                boleto_cnab_api_data = {
                      'bank': bank_name_brcobranca[0],
                      'valor': boleto.valor,
                      'cedente': boleto.cedente,
                      'documento_cedente': boleto.cedente_documento,
                      'sacado': boleto.sacado_nome,
                      'sacado_documento': boleto.sacado_documento,
                      'agencia': move_line.payment_mode_id.bank_id.bra_number,
                      'conta_corrente': move_line.payment_mode_id.bank_id.acc_number,
                      'convenio': boleto.convenio,
                      'numero_documento': move_line.id,
                      'data_vencimento': boleto.data_vencimento.strftime(
                          '%Y/%m/%d'),
                      'data_documento': boleto.data_documento.strftime(
                          '%Y/%m/%d'),
                      'especie': boleto.especie,
                      'moeda': dict_brcobranca_currency[boleto.especie],
                      'aceite': boleto.aceite,
                      'sacado_endereco': boleto.sacado_endereco,
                }
                wrapped_boleto_list.append(
                    BoletoWrapper(boleto, boleto_cnab_api_data))
        return wrapped_boleto_list
