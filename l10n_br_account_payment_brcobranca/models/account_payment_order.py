# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime

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
    '748': 'sicred',
    '004': 'banco_nordeste',
    '021': 'banestes',
    '756': 'sicoob',
    '136': 'unicred',
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

        bank_account = \
            self.payment_mode_id.fixed_journal_id.bank_account_id

        if bank_account.bank_id.code_bc in \
                dict_brcobranca_bank:
            bank_name_brcobranca = \
                dict_brcobranca_bank[bank_account.bank_id.code_bc],
        else:
            raise UserError(
                _('The Bank %s is not implemented in BRCobranca.')
                % bank_account.bank_id.name)

        if (bank_name_brcobranca[0] not in ('bradesco', 'itau', 'unicred')
                or self.payment_mode_id.payment_method_id.code != '400'):
            raise UserError(
                _('The Bank %s and CNAB %s are not implemented.')
                % (bank_account.bank_id.name,
                   self.payment_mode_id.payment_method_id.code))

        pagamentos = []
        for line in self.payment_line_ids:
            linhas_pagamentos = {
                'valor': line.amount_currency,
                'data_vencimento': line.move_line_id.date_maturity.strftime('%Y/%m/%d'),
                'nosso_numero': line.move_line_id.own_number,
                'documento_sacado': misc.punctuation_rm(line.partner_id.cnpj_cpf),
                'nome_sacado':
                    line.partner_id.legal_name.strip()[:40],
                'numero': str(line.document_number)[:10],
                'endereco_sacado': str(
                    line.partner_id.street + ', ' + str(
                        line.partner_id.street_number))[:40],
                'bairro_sacado':
                    line.partner_id.district.strip(),
                'cep_sacado': misc.punctuation_rm(line.partner_id.zip),
                'cidade_sacado':
                    line.partner_id.city_id.name,
                'uf_sacado': line.partner_id.state_id.code,
                'identificacao_ocorrencia': self.movement_instruction_code
            }

            payment_mode = line.move_line_id.payment_mode_id

            if bank_name_brcobranca[0] == 'unicred':
                # TODO - Verificar se é uma tabela unica por banco ou há padrão
                # Identificação da Ocorrência:
                # 01 - Remessa*
                # 02 - Pedido de Baixa
                # 04 - Concessão de Abatimento*
                # 05 - Cancelamento de Abatimento
                # 06 - Alteração de vencimento
                # 08 - Alteração de Seu Número
                # 09 - Protestar*
                # 11 - Sustar Protesto e Manter em Carteira
                # 25 - Sustar Protesto e Baixar Título
                # 26 – Protesto automático
                # 31 - Alteração de outros dados (Alteração de dados do pagador)
                # 40 - Alteração de Carteira
                linhas_pagamentos['identificacao_ocorrencia'] = '01'
                linhas_pagamentos['codigo_protesto'] = \
                    payment_mode.boleto_protest_code or '3'
                linhas_pagamentos['dias_protesto'] = \
                    payment_mode.boleto_days_protest or '0'

                # Código adotado pela FEBRABAN para identificação
                # do tipo de pagamento de multa.
                # Domínio:
                # ‘1’ = Valor Fixo (R$)
                # ‘2’ = Taxa (%)
                # ‘3’ = Isento
                # Isento de Multa caso não exista percentual
                linhas_pagamentos['codigo_multa'] = '3'

                # Isento de Mora
                linhas_pagamentos['tipo_mora'] = '5'

                # TODO
                # Código adotado pela FEBRABAN para identificação do desconto.
                # Domínio:
                # 0 = Isento
                # 1 = Valor Fixo
                linhas_pagamentos['cod_desconto'] = '0'
                # 00000005/01
                linhas_pagamentos['numero'] = str(line.document_number)[1:11]

            if payment_mode.boleto_fee_perc:
                linhas_pagamentos['codigo_multa'] = \
                    payment_mode.boleto_fee_code
                linhas_pagamentos['percentual_multa'] = \
                    payment_mode.boleto_fee_perc

            precision = self.env['decimal.precision']
            precision_account = precision.precision_get('Account')
            if payment_mode.boleto_interest_perc:
                linhas_pagamentos['tipo_mora'] = \
                    payment_mode.boleto_interest_perc
                # TODO - É padrão em todos os bancos ?
                # Código adotado pela FEBRABAN para identificação do tipo de
                # pagamento de mora de juros.
                # Domínio:
                # ‘1’ = Valor Diário (R$)
                # ‘2’ = Taxa Mensal (%)
                # ‘3’= Valor Mensal (R$) *
                # ‘4’ = Taxa diária (%)
                # ‘5’ = Isento
                # *OBSERVAÇÃO:
                # ‘3’ - Valor Mensal (R$): a CIP não acata valor mensal,
                # segundo manual. Cógido mantido
                # para Correspondentes que ainda utilizam.
                # Isento de Mora caso não exista percentual
                if payment_mode.boleto_interest_code == '1':
                    linhas_pagamentos['valor_mora'] = round(
                        line.move_line_id.debit *
                        ((payment_mode.boleto_interest_code / 100)
                         / 30), precision_account)
                if payment_mode.boleto_interest_code == '2':
                    linhas_pagamentos['valor_mora'] = \
                        payment_mode.boleto_interest_code

            if payment_mode.boleto_discount_perc:
                linhas_pagamentos['data_desconto'] =\
                    line.move_line_id.date_maturity.strftime('%Y/%m/%d')
                linhas_pagamentos['valor_desconto'] = round(
                    line.move_line_id.debit * (
                            payment_mode.boleto_discount_perc / 100),
                    precision_account)
                if bank_name_brcobranca[0] == 'unicred':
                    linhas_pagamentos['cod_desconto'] = '1'

            # Protesto
            if payment_mode.boleto_protest_code:
                linhas_pagamentos['codigo_protesto'] = \
                    payment_mode.boleto_protest_code
                if payment_mode.boleto_days_protest:
                    linhas_pagamentos['dias_protesto'] = \
                        payment_mode.boleto_days_protest

            pagamentos.append(linhas_pagamentos)

        remessa_values = {
            'carteira': str(self.payment_mode_id.boleto_wallet),
            'agencia': int(bank_account.bra_number),
            # 'digito_agencia': order.mode.bank_id.bra_number_dig,
            'conta_corrente': int(misc.punctuation_rm(bank_account.acc_number)),
            'digito_conta': bank_account.acc_number_dig[0],
            'empresa_mae': bank_account.partner_id.legal_name[:30],
            'documento_cedente': misc.punctuation_rm(
                bank_account.partner_id.cnpj_cpf),
            'pagamentos': pagamentos,
            'sequencial_remessa': self.payment_mode_id.cnab_sequence_id.next_by_id(),
        }

        if bank_name_brcobranca[0] == 'bradesco':
            remessa_values[
                'codigo_empresa'] = int(self.payment_mode_id.code_convetion)

        # Field used in Sicredi and Sicoob Banks
        if bank_account.bank_id.code_bc in ('748', '756'):
            remessa_values.update({
                'codigo_transmissao': int(self.payment_mode_id.code_convetion),
            })
        # Field used in Unicred Bank
        if bank_account.bank_id.code_bc == '136':
            remessa_values.update({
                'codigo_beneficiario': int(self.payment_mode_id.code_convetion),
            })

        content = json.dumps(remessa_values)
        f = open(tempfile.mktemp(), 'w')
        f.write(content)
        f.close()
        files = {'data': open(f.name, 'rb')}

        api_address = self.env[
            "ir.config_parameter"].sudo().get_param(
            "l10n_br_account_payment_brcobranca.boleto_cnab_api")

        if not api_address:
            raise UserError(
                ('Não é possível gerar os remessa\n'
                 'Informe o Endereço IP ou Nome do'
                 'Boleto CNAB API.'))

        # EX.: "http://boleto_cnab_api:9292/api/remessa"
        api_service_address = \
            'http://' + api_address + ':9292/api/remessa'
        res = requests.post(
            api_service_address,
            data={
                'type': dict_brcobranca_cnab_type[
                    self.payment_mode_id.payment_method_id.code],
                'bank': bank_name_brcobranca[0],
            }, files=files)
        # print("AAAAAAAA", res.status_code, str(res.status_code)[0])
        # print('RES.CONTENT', res.content[0], type(res.content[0]))

        # TODO - res.content[0] parece variar de acordo com banco, existe padrão ?
        if bank_name_brcobranca[0] == 'bradesco' and res.content[0] == '0':
            remessa = res.content
        elif bank_name_brcobranca[0] == 'unicred' and res.content[0] == 48:
            remessa = res.content
        else:
            raise UserError(res.text)

        # Get user TIME ZONE to avoid generate file in 'future'
        now_user_tz = fields.Datetime.context_timestamp(self, datetime.now())
        if self.payment_mode_id.payment_method_id.code == '240':
            file_name = 'CB%s%s.REM' % (
                datetime.strftime(now_user_tz, '%d%m'), str(self.file_number))
        elif self.payment_mode_id.payment_method_id.code == '400':
            file_name = 'CB%s%02d.REM' % (
                datetime.strftime(now_user_tz, '%d%m'), self.file_number or 1)
        elif self.payment_mode_id.payment_method_id.code == '500':
            file_name = 'PG%s%s.REM' % (
                datetime.strftime(now_user_tz, '%d%m'), str(self.file_number))

        return remessa, file_name

    def generated2uploaded(self):
        super().generated2uploaded()
        self.action_done()
