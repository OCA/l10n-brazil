# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Fernando Marcato Rodrigues
#    Copyright (C) 2015 KMEE - www.kmee.com.br
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
import tempfile
import StringIO
from openerp import api, models, fields
from openerp.tools.translate import _
from openerp.exceptions import Warning

try:
    import cnab240
    from cnab240.tipos import ArquivoCobranca400 as cnab_parser
    from cnab240.bancos import bradesco_cobranca_retorno_400 as bradesco
    import codecs
except:
    raise Exception(_('Please install python lib PyCNAB'))


_logger = logging.getLogger(__name__)


MODOS_IMPORTACAO_CNAB = [
    ('bradesco_cobranca_400', u'Bradesco Cobrança 400'),
]


class AccountBankStatementImport(models.TransientModel):
    """  """
    _inherit = 'account.bank.statement.import'

    @api.model
    def _check_cnab(self, data_file):
        if cnab_parser is None:
            return False
        try:
            cnab400_file = tempfile.NamedTemporaryFile()
            cnab400_file.seek(0)
            cnab400_file.write(data_file)
            cnab400_file.flush()
            ret_file = codecs.open(cnab400_file.name, encoding='ascii')
            cnab = cnab_parser(bradesco, arquivo=ret_file)
        except:
            return False
        if len(cnab.lotes) == 0:
            cnab240_file = tempfile.NamedTemporaryFile()
            cnab240_file.seek(0)
            cnab240_file.write(data_file)
            cnab240_file.flush()
            ret_file = codecs.open(cnab240_file.name, encoding='ascii')
            cnab2 = cnab240.tipos.Arquivo(
                cnab240.bancos.bradesco, arquivo=ret_file
            )
            return cnab2
        return cnab

    # @api.model
    # def _find_bank_account_id(self, account_number):
    #     """ Get res.partner.bank ID """
    #     bank_account_id = None
    #     if account_number:
    #         bank_account_ids = self.env['res.partner.bank'].search(
    #             [('acc_number', '=', str(account_number))], limit=1)
    #         if bank_account_ids:
    #             bank_account_id = bank_account_ids[0].id
    #     return bank_account_id

    # @api.model
    # def _complete_statement(self, stmt_vals, journal_id, account_number):
    #     """Complete statement from information passed.
    #         unique_import_id can be imported more than 1 time."""
    #     stmt_vals['journal_id'] = journal_id
    #
    #     #TODO pesquisar cnpj do parceiro para a reconciliação
    #     for line_vals in stmt_vals['transactions_cnab_return']:
    #         # write on move_line
    #         self.write_data_on_move_line(line_vals)
    #         pass
    #
    #     for line_vals in stmt_vals['transactions']:
    #         self.write_data_on_paid_move_line(line_vals)
    #         unique_import_id = line_vals.get('unique_import_id', False)
    #         if unique_import_id:
    #             line_vals['unique_import_id'] = unique_import_id
    #         if not line_vals.get('bank_account_id'):
    #             # Find the partner and his bank account or create the bank
    #             # account. The partner selected during the reconciliation
    #             # process will be linked to the bank when the statement is
    #             # closed.
    #             partner_id = False
    #             bank_account_id = False
    #             partner_account_number = line_vals.get('account_number')
    #             if partner_account_number:
    #                 bank_model = self.env['res.partner.bank']
    #                 banks = bank_model.search(
    #                     [('acc_number', '=', partner_account_number)], limit=1)
    #                 if banks:
    #                     bank_account_id = banks[0].id
    #                     partner_id = banks[0].partner_id.id
    #                 else:
    #                     bank_obj = self._create_bank_account(
    #                         partner_account_number)
    #                     bank_account_id = bank_obj and bank_obj.id or False
    #             line_vals['partner_id'] = partner_id
    #             line_vals['bank_account_id'] = bank_account_id
    #     return stmt_vals

    @api.multi
    def _parse_file(self, data_file):
        """Parse a CNAB file."""
        cnab = self._check_cnab(data_file)
        try:
            if cnab.header.literal_servico == 'COBRANCA':
                event_list = []
                transactions = []
                total_amt = 0.00
                try:
                    for lote in cnab.lotes:

                        data_criacao = str(cnab.header.arquivo_data_de_geracao)
                        if len(data_criacao) < 6:
                            data_criacao = '0' + data_criacao
                        dia_criacao = data_criacao[:2]
                        mes_criacao = data_criacao[2:4]
                        ano_criacao = data_criacao[4:6]
                        name = cnab.header.literal_retorno + " " + cnab.header.literal_servico + " " + cnab.header.nome_banco + " - " + dia_criacao + "/" + mes_criacao + "/" + ano_criacao
                        vals_bank_statement = {
                            'name': name,
                            'transactions': {},
                            'balance_end_real': cnab.trailer.valor_registros_ocorrencia_02_confirmacao,
                            'date': dia_criacao + "-" + mes_criacao + "-" + ano_criacao,
                        }

                        for evento in lote.eventos:
                            if evento.identificacao_ocorrencia == 2:
                                data = str(evento.data_ocorrencia_banco)
                                if len(data) < 6:
                                    data = '0' + data
                                dia = data[:2]
                                mes = data[2:4]
                                ano = data[4:6]
                                partner_id = False
                                cnpj_cpf = str(evento.numero_documento)[-14:]
                                invoice_number = 'SAJ/2016/005'
                                invoices = self.env['account.invoice']
                                invoice = invoices.search([
                                    ('number', '=', invoice_number)
                                ])
                                partner = invoice.partner_id
                                # if fiscal.validate_cnpj(cnpj_cpf):
                                #     cnpj_cpf = "%s.%s.%s/%s-%s"\
                                #     % (cnpj_cpf[0:2], cnpj_cpf[2:5], cnpj_cpf[5:8],
                                #        cnpj_cpf[8:12], cnpj_cpf[12:14])
                                #     partner_id = self.env['res.partner'].search(
                                #         [('cnpj_cpf', '=', cnpj_cpf)], limit=1)
                                bank_account = self.env['res.partner.bank'].search([
                                    ('acc_number', '=', evento.identificacao_empresa_cedente_banco[11:16])
                                ])
                                vals_line = {
                                    'date': dia + "-" + mes + "-" + ano,
                                    'name': evento.identificacao_titulo_banco,
                                    'ref': evento.numero_documento,
                                    #'ref': partner_id and partner_id.name or False,
                                    'amount': evento.valor_titulo,
                                    'unique_import_id': evento.identificacao_titulo_banco,
                                    'partner_id': partner and partner.id or False,
                                    'partner_name': (partner and partner.legal_name
                                                     or False),
                                    'bank_account_id': bank_account.id,
                                }
                                event_list.append(vals_line)
                        vals_bank_statement['transactions'] = event_list
                except Exception, e:
                    raise UserError(_(
                        "Erro!\n "
                        "Mensagem:\n\n %s" % e.message
                    ))

                return False, str(cnab.lotes[0].eventos[0].identificacao_empresa_cedente_banco[11:16]), [vals_bank_statement]
        except:
            return super(AccountBankStatementImport, self)._parse_file(
                data_file)

    # @api.model
    # def _check_parsed_data(self, statements):
    #     """ Basic and structural verifications """
    #     if len(statements) == 0:
    #         raise Warning(_('This file doesn\'t contain any statement.'))
    #     for stmt_vals in statements:
    #         if 'transactions' in stmt_vals and stmt_vals['transactions']:
    #             return
    #     # Due to actual CNAB implementation, stmt_vals can have zero
    #     # transactions.
    #     # raise Warning(_('This file doesn\'t contain any transaction.'))
    #
    # @api.multi
    # def write_data_on_move_line(self, data):
    #     self.ensure_one()
    #
    #     move_line_name = data['ref']
    #     move_line_model = self.env['account.move.line']
    #     move_line_item = move_line_model.search(
    #         [('name', '=', move_line_name)], limit=1)
    #
    #     if move_line_item:
    #         move_line_item.transaction_ref = data['ref']
    #         move_line_item.ml_identificacao_titulo_no_banco = data[
    #         'identificacao_titulo_no_banco']
    #
    #
    #     cnab_move = self.env['l10n_br_cnab.move']
    #     cnab_move.create({
    #         'move_line_id': move_line_item and move_line_item.id or False,
    #         'str_ocorrencia': data['str_ocorrencia'],
    #         'str_motiv_a': data['str_motiv_a'],
    #         'str_motiv_b': data['str_motiv_b'],
    #         'str_motiv_c': data['str_motiv_c'],
    #         'str_motiv_d': data['str_motiv_d'],
    #         'str_motiv_e': data['str_motiv_e'],
    #         'data_ocorrencia': data['data_ocorrencia'],
    #         'bank_title_name': data['bank_title_name'],
    #         'title_name_at_company': data['title_name_at_company']
    #     })
    #
    # @api.multi
    # def write_data_on_paid_move_line(self, data):
    #     self.ensure_one()
    #
    #     move_line_name = data['ref']
    #     move_line_model = self.env['account.move.line']
    #     move_line_item = move_line_model.search(
    #         [('name', '=', move_line_name)], limit=1)
    #
    #
    #     cnab_move = self.env['l10n_br_cnab.move']
    #     cnab_move.create({
    #         'move_line_id':  move_line_item and move_line_item.id or False,
    #         'str_ocorrencia': data['str_ocorrencia'],
    #         'str_motiv_a': data['str_motiv_a'],
    #         'str_motiv_b': data['str_motiv_b'],
    #         'str_motiv_c': data['str_motiv_c'],
    #         'str_motiv_d': data['str_motiv_d'],
    #         'str_motiv_e': data['str_motiv_e'],
    #         'data_ocorrencia': data['data_ocorrencia'],
    #         'bank_title_name': data['bank_title_name'],
    #         'title_name_at_company': data['title_name_at_company']
    #     })
    #
    # # Overrides temporarily
    # @api.model
    # def _import_file(self, data_file):
    #     """ Create bank statement(s) from file."""
    #     # The appropriate implementation module returns the required data
    #     statement_ids = []
    #     notifications = []
    #     parse_result = self._parse_file(data_file)
    #     # Check for old version result, with separate currency and account
    #     if isinstance(parse_result, tuple) and len(parse_result) == 3:
    #         (currency_code, account_number, statements) = parse_result
    #         for stmt_vals in statements:
    #             stmt_vals['currency_code'] = currency_code
    #             stmt_vals['account_number'] = account_number
    #     else:
    #         statements = parse_result
    #     # Check raw data:
    #     self._check_parsed_data(statements)
    #     # Import all statements:
    #     for stmt_vals in statements:
    #         (statement_id, new_notifications) = (
    #             self._import_statement(stmt_vals))
    #         if statement_id:
    #             statement_ids.append(statement_id)
    #         notifications.append(new_notifications)
    #     if len(statement_ids) == 0:
    #         pass
    #         # raise Warning(_('You have already imported that file.'))
    #     return statement_ids, notifications