# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# Copyright 2020 KMEE
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging
import tempfile

import requests
from odoo import models, api, fields, _
from odoo.exceptions import Warning as UserError
from ..constants.br_cobranca import (
    DICT_BRCOBRANCA_CNAB_TYPE,
    get_brcobranca_bank,
)


_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base import misc
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")


class PaymentOrder(models.Model):
    _inherit = "account.payment.order"

    def _prepare_remessa_banco_brasil_400(self, remessa_values):
        # TODO - BRCobranca retornando erro de agencia deve ter 4 digitos,
        #  mesmo o valor estando correto, é preciso verificar melhor
        remessa_values.update({
            'convenio': int(self.payment_mode_id.code_convetion),
            'variacao_carteira': self.payment_mode_id.boleto_variation.zfill(3),
            # TODO - Mapear e se necessário criar os campos abaixo devido
            #  ao erro comentado acima não está sendo possível validar
            'tipo_cobranca': '04DSC',
            'convenio_lider': '7654321',
            'carteira': str(self.payment_mode_id.boleto_wallet).zfill(2),
        })

    def _prepare_remessa_caixa_240(self, remessa_values):
        remessa_values.update({
            'convenio': int(self.payment_mode_id.code_convetion),
            'digito_agencia': self.journal_id.bank_account_id.bra_number_dig,
        })

    def _prepare_remessa_unicred_400(self, remessa_values):
        remessa_values[
            'codigo_beneficiario'] = int(self.payment_mode_id.code_convetion)

    def _prepare_remessa_sicred_240(self, remessa_values):
        remessa_values.update({
            'codigo_transmissao': int(self.payment_mode_id.code_convetion),
            'posto': self.payment_mode_id.boleto_post,
            'byte_idt': self.payment_mode_id.boleto_byte_idt,
        })

    def _prepare_remessa_bradesco_400(self, remessa_values):
        remessa_values['codigo_empresa'] = int(self.payment_mode_id.code_convetion)

    def get_file_name(self, cnab_type):
        context_today = fields.Date.context_today(self)
        if cnab_type == '240':
            return 'CB%s%s.REM' % (
                context_today.strftime('%d%m'), str(self.file_number))
        elif cnab_type == '400':
            return 'CB%s%02d.REM' % (
                context_today.strftime('%d%m'), self.file_number or 1)
        elif cnab_type == '500':
            return 'PG%s%s.REM' % (
                context_today.strftime('%d%m'), str(self.file_number))

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
        bank_account_id = self.journal_id.bank_account_id
        bank_brcobranca = get_brcobranca_bank(bank_account_id)

        if self.payment_mode_id.group_lines:
            raise UserError(
                _('The Payment mode can not be used with the group lines active, \n '
                  'please uncheck it on payment mode configuration to continue')
            )
        if self.payment_mode_id.generate_move or self.payment_mode_id.post_move:
            raise UserError(
                _('The Payment mode can not be used with the generated moves or'
                  ' post moves active \n Please uncheck it on payment mode'
                  ' configuration to continue')
            )
        if cnab_type not in bank_brcobranca.remessa:
            # Informa se o CNAB especifico de um Banco não está implementado
            # no BRCobranca, evitando a mensagem de erro mais extensa da lib
            raise UserError(
                _('The CNAB %s for Bank %s are not implemented in BRCobranca.')
                % (cnab_type, bank_account_id.bank_id.name,))

        pagamentos = []
        for line in self.bank_line_ids:
            pagamentos.append(line.prepare_bank_payment_line(
                bank_brcobranca
            ))

        remessa_values = {
            'carteira': str(self.payment_mode_id.boleto_wallet),
            'agencia': bank_account_id.bra_number,
            'conta_corrente': int(misc.punctuation_rm(bank_account_id.acc_number)),
            'digito_conta': bank_account_id.acc_number_dig[0],
            'empresa_mae': bank_account_id.partner_id.legal_name[:30],
            'documento_cedente': misc.punctuation_rm(
                bank_account_id.partner_id.cnpj_cpf),
            'pagamentos': pagamentos,
            'sequencial_remessa': self.payment_mode_id.cnab_sequence_id.next_by_id(),
        }

        try:
            bank_method = getattr(
                self, '_prepare_remessa_{}_{}'.format(
                    bank_brcobranca.name,
                    cnab_type
                )
            )
            if bank_method:
                bank_method(remessa_values)
        except Exception:
            pass

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
                'type': DICT_BRCOBRANCA_CNAB_TYPE[
                    cnab_type],
                'bank': bank_brcobranca.name,
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

        return remessa, self.get_file_name(cnab_type)

    @api.multi
    def generated2uploaded(self):
        super().generated2uploaded()
        for payment_line in self.payment_line_ids:
            # No caso de Cancelamento da Invoice a AML é apagada
            if payment_line.move_line_id:
                # Importante para saber a situação do CNAB no caso
                # de um pagto feito por fora ( dinheiro, deposito, etc)
                payment_line.move_line_id.cnab_state = 'exported'
        self.action_done()
