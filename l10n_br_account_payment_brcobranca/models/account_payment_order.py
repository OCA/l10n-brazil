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
                # 31 - Alteração de outros da
                linhas_pagamentos['identificacao_ocorrencia'] = '01'

            if line.move_line_id.payment_mode_id.boleto_perc_mora:
                if bank_name_brcobranca[0] == 'bradesco':
                    linhas_pagamentos['codigo_multa'] = '2'
                    linhas_pagamentos['percentual_multa'] = \
                        line.move_line_id.payment_mode_id.boleto_perc_mora
                if bank_name_brcobranca[0] == 'unicred':
                    # TODO
                    # Código adotado pela FEBRABAN para identificação
                    # do tipo de pagamento de multa.
                    # Domínio:
                    # ‘1’ = Valor Fixo (R$)
                    # ‘2’ = Taxa (%)
                    # ‘3’ = Isento
                    linhas_pagamentos['codigo_multa'] = '2'
                    linhas_pagamentos['percentual_multa'] = \
                        line.move_line_id.payment_mode_id.boleto_perc_mora
                    # TODO
                    # Código para Protesto*
                    # Código adotado pela FEBRABAN para identificar o tipo de prazo a ser considerado para o
                    # protesto.
                    # Domínio:
                    # 1 = Protestar Dias Corridos
                    # 2 = Protestar Dias Úteis
                    # 3 = Não Protestar
                    # OBS.: a) Na remessa de títulos - Identificação da Ocorrência igual a ‘01’ - Remessa:
                    # Qualquer caracter diferente de ‘1’, ‘2’ ou ‘3’ será considerado igual a ‘3’.
                    # 158 a 158
                    # b) Na instrução de Protesto Automático - Identificação da Ocorrência ‘26’ -
                    # Protesto automático:
                    # Qualquer caracter diferente de ‘1’, ‘2’ ou ‘3’, a instrução será rejeitada.
                    linhas_pagamentos['codigo_protesto'] = 3

            precision = self.env['decimal.precision']
            precision_account = precision.precision_get('Account')
            if line.move_line_id.payment_mode_id.cnab_percent_interest:
                linhas_pagamentos['valor_mora'] = round(
                    line.move_line_id.debit *
                    ((line.move_line_id.payment_mode_id.cnab_percent_interest / 100)
                     / 30), precision_account)
                if bank_name_brcobranca[0] == 'unicred':
                    # TODO
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
                    linhas_pagamentos['tipo_mora'] = '1'
            if line.move_line_id.payment_term_id.discount_perc:
                linhas_pagamentos['data_desconto'] =\
                    line.move_line_id.date_maturity.strftime('%Y/%m/%d')
                linhas_pagamentos['valor_desconto'] = round(
                    line.move_line_id.debit * (
                            line.move_line_id.payment_term_id.discount_perc / 100),
                    precision_account)
                if bank_name_brcobranca[0] == 'unicred':
                    # TODO
                    # Código adotado pela FEBRABAN para identificação do desconto.
                    # Domínio:
                    # 0 = Isento
                    # 1 = Valor Fixo
                    linhas_pagamentos['cod_desconto'] = 1

            pagamentos.append(linhas_pagamentos)

        remessa_values = {
            'carteira': str(self.payment_mode_id.boleto_carteira),
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

        if (bank_name_brcobranca[0] == 'bradesco'
                and self.payment_mode_id.payment_method_id.code == '400'):
            remessa_values[
                'codigo_empresa'] = int(self.payment_mode_id.codigo_convenio)

        # Field used in Sicredi/Unicred and Sicoob Banks
        if bank_account.bank_id.code_bc == '748':
            # TODO - Verificar no manual de onde vem o campo e tirar o hardcode
            remessa_values.update({
                'codigo_transmissao': '01234567890123456789',
            })
        # Field used in Unicred Bank
        if bank_account.bank_id.code_bc == '136':
            remessa_values.update({
                'codigo_beneficiario': int(self.payment_mode_id.codigo_convenio),
            })

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
        # print("AAAAAAAA", res.status_code, str(res.status_code)[0])
        # print('RES.CONTENT', res.content[0], type(res.content[0]))

        # TODO - res.content[0] parece variar de acordo com banco, existe padrão ?
        if bank_name_brcobranca[0] == 'bradesco' and res.content[0] == '0':
            remessa = res.content
        elif bank_name_brcobranca[0] == 'unicred' and res.content[0] == 48:
            remessa = res.content
        else:
            raise UserError(res.text)

        # self.state = 'done'
        # self.cnab_file = base64.b64encode(remessa)

        # Criando instancia do CNAB a partir do código do banco
        #            cnab = Cnab.get_cnab(
        #                order.mode.bank_id.bank_bic, order.mode.type.code)()

        #                remessa = cnab.remessa(order)

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
