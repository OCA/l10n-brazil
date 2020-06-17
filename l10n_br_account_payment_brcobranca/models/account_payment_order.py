# -*- coding: utf-8 -*-
# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
import logging

from odoo import models, api, fields, _

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base import misc
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")

import logging

import requests
import json
import tempfile
from odoo.exceptions import Warning as UserError


_logger = logging.getLogger(__name__)
try:
    from cnab240.errors import (Cnab240Error)
except ImportError as err:
    _logger.debug = err

dict_brcobranca_bank = {
    '001': 'banco_brasil',
    '041': 'banrisul',
    '237': 'bradesco',
    '104': 'caixa',
    '399': 'hsbc',
    '341': 'itau',
    '033': 'santander',
    '748': 'sicredi',
    '004': 'banco_nordeste',
    '021': 'banestes',
    '756': 'sicoob',
}

dict_brcobranca_cnab_type = {
    '240': 'cnab240',
    '400': 'cnab400',
}


class PaymentOrder(models.Model):
    _inherit = "account.payment.order"

    @api.multi
    def generate_payment_file(self):
        """Returns (payment file as string, filename)"""
        self.ensure_one()

        # see remessa fields here:
        # https://github.com/kivanio/brcobranca/blob/master/lib/brcobranca/remessa/base.rb
        # https://github.com/kivanio/brcobranca/tree/master/lib/brcobranca/remessa/cnab240
        # https://github.com/kivanio/brcobranca/tree/master/lib/brcobranca/remessa/cnab400
        # and a test here:
        # https://github.com/kivanio/brcobranca/blob/master/spec/brcobranca/remessa/cnab400/itau_spec.rb

        if self.payment_mode_id.fixed_journal_id.\
                bank_account_id.bank_id.code_bc in \
                dict_brcobranca_bank:
            bank_name_brcobranca = \
                dict_brcobranca_bank[
                    self.payment_mode_id.fixed_journal_id
                        .bank_account_id.bank_id.code_bc],
        else:
            raise UserError(
                _('The Bank %s is not implemented in BRCobranca.')
                % self.payment_mode_id.fixed_journal_id.bank_account_id.bank_id.name)

        if (bank_name_brcobranca[0] not in ('bradesco', 'itau')
                or self.payment_mode_id.payment_method_id.code != '400'):
            raise UserError(
                _('The Bank %s and CNAB %s are not implemented.')
                % (self.payment_mode_id.fixed_journal_id.bank_account_id.bank_id.name,
                   self.payment_mode_id.payment_method_id.code))

        pagamentos = []
        for line in self.payment_line_ids:
            linhas_pagamentos = {
                'valor': line.amount_currency,
                'data_vencimento': line.move_line_id.date_maturity.strftime('%Y/%m/%d'),
                'nosso_numero': line.move_line_id.nosso_numero,
                'documento_sacado': misc.punctuation_rm(line.partner_id.cnpj_cpf),
                'nome_sacado':
                    line.partner_id.legal_name.strip()[:40],
                'numero': str(line.move_line_id.name)[:10],
                'endereco_sacado': str(
                    line.partner_id.street + ', ' + str(
                        line.partner_id.street_number))[:40],
                'bairro_sacado':
                    line.partner_id.district.strip(),
                'cep_sacado': misc.punctuation_rm(line.partner_id.zip),
                'cidade_sacado':
                    line.partner_id.city_id.name,
                'uf_sacado': line.partner_id.state_id.code,
                'identificacao_ocorrencia': self.codigo_instrucao_movimento
            }
            if line.move_line_id.payment_mode_id.boleto_perc_mora:
                linhas_pagamentos['codigo_multa'] = '2'
                linhas_pagamentos['percentual_multa'] = \
                    line.move_line_id.payment_mode_id.boleto_perc_mora
            precision = self.env['decimal.precision']
            precision_account = precision.precision_get('Account')
            if line.move_line_id.payment_mode_id.cnab_percent_interest:
                linhas_pagamentos['valor_mora'] = round(
                    line.move_line_id.debit *
                    ((line.move_line_id.payment_mode_id.cnab_percent_interest / 100)
                     / 30), precision_account)
            if line.move_line_id.payment_term_id.discount_perc:
                linhas_pagamentos['data_desconto'] =\
                    line.move_line_id.date_maturity.strftime('%Y/%m/%d')
                linhas_pagamentos['valor_desconto'] = round(
                    line.move_line_id.debit * (
                            line.move_line_id.payment_term_id.discount_perc / 100),
                    precision_account)

            pagamentos.append(linhas_pagamentos)

        remessa_values = {
            'carteira': str(self.payment_mode_id.boleto_carteira),
            'agencia': int(self.payment_mode_id.fixed_journal_id.bank_account_id.bra_number),
            # 'digito_agencia': order.mode.bank_id.bra_number_dig,
            'conta_corrente': int(misc.punctuation_rm(self.payment_mode_id.fixed_journal_id.bank_account_id.acc_number)),
            'digito_conta': self.payment_mode_id.fixed_journal_id.bank_account_id.acc_number_dig[0],
            'empresa_mae':
                self.payment_mode_id.fixed_journal_id.bank_account_id.partner_id.legal_name[:30],
            'documento_cedente': misc.punctuation_rm(
                self.payment_mode_id.fixed_journal_id.bank_account_id.partner_id.cnpj_cpf),
            'pagamentos': pagamentos,
            'sequencial_remessa': self.payment_mode_id.cnab_sequence_id.next_by_id(),
        }

        if (bank_name_brcobranca[0] == 'bradesco'
                and self.payment_mode_id.payment_method_id.code == '400'):
            remessa_values[
                'codigo_empresa'] = int(self.payment_mode_id.codigo_convenio)

        content = json.dumps(remessa_values)
        f = open(tempfile.mktemp(), 'w')
        f.write(content)
        f.close()
        files = {'data': open(f.name, 'rb')}

        # TODO - Name of service should be a parameter ?
        #  For docky users check the name of service
        #  defined in dev.docker-compose.yml

        res = requests.post(
            "http://brcobranca:9292/api/remessa",
            data={
                'type': dict_brcobranca_cnab_type[
                    self.payment_mode_id.payment_method_id.code],
                'bank': bank_name_brcobranca[0],
            }, files=files)
        # print "AAAAAAAA", res.status_code, str(res.status_code)[0]
        #print('RES.CONTENT', res.content[0])

        # TODO - Check If will be necessary keep code
        #  Test made in CNAB 400 Bradesco
        #if res.content[0] == '0':
        #    remessa = res.content
        #else:
        #    raise UserError(res.text)

        remessa = res.content

        #self.state = 'done'
        #self.cnab_file = base64.b64encode(remessa)

        # Criando instancia do CNAB a partir do código do banco
        #            cnab = Cnab.get_cnab(
        #                order.mode.bank_id.bank_bic, order.mode.type.code)()

        #                remessa = cnab.remessa(order)

        file_name = ''
        if self.payment_mode_id.payment_method_id.code == '240':
            file_name = 'CB%s%s.REM' % (
                time.strftime('%d%m'), str(self.file_number))
        elif self.payment_mode_id.payment_method_id.code == '400':
            file_name = 'CB%s%02d.REM' % (
                time.strftime('%d%m'), self.file_number or 1)
        elif self.payment_mode_id.payment_method_id.code == '500':
            file_name = 'PG%s%s.REM' % (
                time.strftime('%d%m'), str(self.file_number))
        # self.state = 'done'
        # self.cnab_file = base64.b64encode(remessa)
        # self.cnab_file = base64.b64encode(remessa)
        # self.cnab_filename = self.name

        return remessa, file_name
