# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# Copyright 2020 KMEE
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging
import tempfile
from collections import namedtuple

import requests
from odoo import models, api, fields, _
from odoo.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base import misc
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")

dict_brcobranca_cnab_type = {
    '240': 'cnab240',
    '400': 'cnab400',
}

BankRecord = namedtuple('Bank', 'name, retorno, remessa')

dict_brcobranca_bank = {
    '001': BankRecord('banco_brasil', retorno=['400'], remessa=['240', '400']),
    '004': BankRecord('banco_nordeste', retorno=['400'], remessa=['400']),
    '021': BankRecord('banestes', retorno=[], remessa=[]),
    '033': BankRecord('santander', retorno=['240'], remessa=['400']),
    '041': BankRecord('banrisul', retorno=['400'], remessa=['400']),
    '070': BankRecord('banco_brasilia', retorno=[], remessa=['400']),
    '097': BankRecord('credisis', retorno=['400'], remessa=['400']),
    '104': BankRecord('caixa', retorno=['240'], remessa=['240']),
    '136': BankRecord('unicred', retorno=['400'], remessa=['240', '400']),
    '237': BankRecord('bradesco', retorno=['400'], remessa=['400']),
    '341': BankRecord('itau', retorno=['400'], remessa=['400']),
    '399': BankRecord('hsbc', retorno=[], remessa=[]),
    '745': BankRecord('citibank', retorno=[], remessa=['400']),
    '748': BankRecord('sicred', retorno=['240'], remessa=['240']),
    '756': BankRecord('sicoob', retorno=['240'], remessa=['240', '400']),
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

        cnab_type = self.payment_mode_id.payment_method_code
        bank_account = self.journal_id.bank_account_id
        bank_name_brcobranca = dict_brcobranca_bank.get(bank_account.bank_id.code_bc)

        if self.payment_mode_id.group_lines:
            raise UserError(
                _('The Payment mode can not be used with the group lines active, \n '
                  'please uncheck it on payment mode configuration to c')
            )
        if not bank_name_brcobranca:
            # Lista de bancos não implentados no BRCobranca
            raise UserError(
                _('The Bank %s is not implemented in BRCobranca.')
                % bank_account.bank_id.name)
        if cnab_type not in bank_name_brcobranca.remessa:
            # Informa se o CNAB especifico de um Banco não está implementado
            # no BRCobranca, evitando a mensagem de erro mais extensa da lib
            raise UserError(
                _('The CNAB %s for Bank %s are not implemented in BRCobranca.')
                % (cnab_type, bank_account.bank_id.name,))

        pagamentos = []
        for line in self.bank_line_ids:
            pagamentos.append(line.prepare_bank_payment_line(bank_name_brcobranca))

        remessa_values = {
            'carteira': str(self.payment_mode_id.boleto_wallet),
            'agencia': int(bank_account.bra_number),
            'conta_corrente': int(misc.punctuation_rm(bank_account.acc_number)),
            'digito_conta': bank_account.acc_number_dig[0],
            'empresa_mae': bank_account.partner_id.legal_name[:30],
            'documento_cedente': misc.punctuation_rm(
                bank_account.partner_id.cnpj_cpf),
            'pagamentos': pagamentos,
            'sequencial_remessa': self.payment_mode_id.cnab_sequence_id.next_by_id(),
        }

        # Campos especificos de cada Banco
        if bank_name_brcobranca[0] == 'bradesco':
            remessa_values[
                'codigo_empresa'] = int(self.payment_mode_id.code_convetion)

        # Field used in Sicoob Banks
        if bank_account.bank_id.code_bc == '756':
            remessa_values.update({
                'codigo_transmissao': int(self.payment_mode_id.code_convetion),
            })

        # Field used in Sicredi Banks
        if bank_account.bank_id.code_bc == '748':
            remessa_values.update({
                'codigo_transmissao': int(self.payment_mode_id.code_convetion),
                'posto': self.payment_mode_id.boleto_post,
                'byte_idt': self.payment_mode_id.boleto_byte_idt,
            })

        # Field used in Unicred Bank
        if bank_account.bank_id.code_bc == '136':
            remessa_values[
                'codigo_beneficiario'] = int(self.payment_mode_id.code_convetion)

        # Field used in Caixa Economica Federal
        if bank_account.bank_id.code_bc == '104':
            remessa_values.update({
                'convenio': int(self.payment_mode_id.code_convetion),
                'digito_agencia': bank_account.bra_number_dig,
            })

        # Field used in Banco do Brasil
        if bank_account.bank_id.code_bc == '001':
            # TODO - BRCobranca retornando erro de agencia deve ter 4 digitos,
            #  mesmo o valor estando correto, é preciso verificar melhor
            remessa_values.update({
                'convenio': int(self.payment_mode_id.code_convetion),
                'variacao_carteira': self.payment_mode_id.boleto_variation,
                # TODO - Mapear e se necessário criar os campos abaixo devido
                #  ao erro comentado acima não está sendo possível validar
                'tipo_cobranca': '04DSC',
                'convenio_lider': '7654321',
            })

        content = json.dumps(remessa_values)
        f = open(tempfile.mktemp(), 'w')
        f.write(content)
        f.close()
        files = {'data': open(f.name, 'rb')}

        api_address = self.env[
            'ir.config_parameter'].sudo().get_param(
            'l10n_br_account_payment_brcobranca.boleto_cnab_api')

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
                    cnab_type],
                'bank': bank_name_brcobranca[0],
            }, files=files)

        if cnab_type == '240' and 'R01' in res.text[242:254]:
            #  Todos os header de lote cnab 240 tem conteúdo: R01,
            #  verificar observações G025 e G028 do manual cnab 240 febraban.
            remessa = res.content
        elif cnab_type == '400' and res.text[:3] in ('01R', 'DCB'):
            # A remessa 400 não tem um layout padronizado,
            # entretanto a maiorias dos arquivos começa com 01REMESSA,
            # o banco de brasilia começa com DCB...
            # Dúvidas verificar exemplos:
            # https://github.com/kivanio/brcobranca/tree/master/spec/fixtures/remessa
            remessa = res.content
        else:
            raise UserError(res.text)

        context_today = fields.Date.context_today(self)

        if cnab_type == '240':
            file_name = 'CB%s%s.REM' % (
                context_today.strftime('%d%m'), str(self.file_number))
        elif cnab_type == '400':
            file_name = 'CB%s%02d.REM' % (
                context_today.strftime('%d%m'), self.file_number or 1)
        elif cnab_type == '500':
            file_name = 'PG%s%s.REM' % (
                context_today.strftime('%d%m'), str(self.file_number))

        return remessa, file_name

    def generated2uploaded(self):
        super().generated2uploaded()
        self.action_done()
