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
from openerp.exceptions import Warning as UserError
from contextlib import contextmanager

try:
    import cnab240
    from cnab240.tipos import ArquivoCobranca400 as cnab_parser
    from cnab240.bancos import bradesco_cobranca_retorno_400 as bradesco
    from cnab240.ocorrencias import retorna_ocorrencia, \
        retorna_motivios_ocorrencia
    import codecs
except:
    raise Exception(_('Please install python lib PyCNAB'))


_logger = logging.getLogger(__name__)


@contextmanager
def commit(cr):
    """
    Commit the cursor after the ``yield``, or rollback it if an
    exception occurs.

    Warning: using this method, the exceptions are logged then discarded.
    """
    try:
        yield
    except Exception:
        cr.rollback()
        _logger.exception('Error during an automatic workflow action.')
    else:
        cr.commit()


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

    @api.multi
    def _parse_file(self, data_file):
        """Parse a CNAB file."""
        cnab = self._check_cnab(data_file)
        try:
            if cnab.header.literal_servico == 'COBRANCA':
                event_list = []

                try:
                    for lote in cnab.lotes:

                        data_criacao = str(cnab.header.arquivo_data_de_geracao)
                        if len(data_criacao) < 6:
                            data_criacao = '0' + data_criacao
                        dia_criacao = data_criacao[:2]
                        mes_criacao = data_criacao[2:4]
                        ano_criacao = data_criacao[4:6]
                        name = cnab.header.literal_retorno + " "
                        name += cnab.header.literal_servico + " "
                        name += cnab.header.nome_banco + " - "
                        name += dia_criacao + "/"
                        name += mes_criacao + "/" + ano_criacao

                        vals_bank_statement = {
                            'name': name,
                            'transactions': {},
                            'balance_end_real': float(
                                cnab.trailer
                                    .valor_registros_ocorrencia_06_liquidacao
                            )/100,
                            'date':
                                dia_criacao + "-" + mes_criacao + "-" +
                                ano_criacao,
                        }

                        for evento in lote.eventos:
                            with commit(self.env.cr):
                                is_created = self.create_cnab_move(evento)
                            if is_created:
                                if evento.identificacao_ocorrencia == 6 or \
                                                evento.identificacao_ocorrencia\
                                                == 15:
                                    data = str(evento.data_ocorrencia_banco)
                                    if len(data) < 6:
                                        data = '0' + data
                                    dia = data[:2]
                                    mes = data[2:4]
                                    ano = data[4:6]
                                    move_line_item, partner = \
                                        self.buscar_account_move_line(
                                            evento.numero_documento
                                        )

                                    bank_account = \
                                        self.env['res.partner.bank'].search([
                                            (
                                                'acc_number', '=', str(
                                                    cnab.header.codigo_empresa)
                                            )
                                        ])
                                    vals_line = {
                                        'date': dia + "-" + mes + "-" + ano,
                                        'name': str(evento.identificacao_titulo_banco),
                                        'ref': evento.numero_documento,
                                        'amount': float(
                                            evento.valor_pago)/100,
                                        'unique_import_id':
                                            evento.identificacao_titulo_banco,

                                        'bank_account_id': bank_account.id,
                                    }
                                    event_list.append(vals_line)
                        vals_bank_statement['transactions'] = event_list
                except Exception, e:
                    raise UserError(_(
                        "Erro!\n "
                        "Mensagem:\n\n %s" % e.message
                    ))

                return False, str(
                            cnab.header.codigo_empresa
                       ), [vals_bank_statement]
        except:
            return super(AccountBankStatementImport, self)._parse_file(
                data_file)

    @api.model
    def create_cnab_move(self, evento):
        data = str(evento.data_ocorrencia_banco)
        if len(data) < 6:
            data = '0' + data
        dia = data[:2]
        mes = data[2:4]
        ano = data[4:6]

        identificacao_ocorrencia = evento.identificacao_ocorrencia
        id_motivos = evento.motivo_rejeicao_ocorrencia_109_110

        motivos = retorna_motivios_ocorrencia(
            identificacao_ocorrencia, id_motivos
        )

        move_line_item, partner = self.buscar_account_move_line(
            evento.numero_documento
        )

        if move_line_item:
            move_line_item.transaction_ref = evento.identificacao_titulo_banco
            move_line_item.ml_identificacao_titulo_no_banco = \
                evento.identificacao_titulo_banco

        try:
            referencia = evento.numero_documento.split("/")
            num_sequencia_parcela = referencia[1]
        except:
            num_sequencia_parcela = evento.numero_documento[-4:-2]

        vals = {
            'move_line_id': move_line_item and move_line_item.id or False,
            'bank_title_name': evento.identificacao_titulo_banco,
            'title_name_at_company': evento.numero_documento[:-2],
            'sequencia_no_titulo': num_sequencia_parcela,
            'data_ocorrencia': dia + '/' + mes + '/' + ano,
            'str_ocorrencia': retorna_ocorrencia(identificacao_ocorrencia),
            'cod_ocorrencia': evento.identificacao_ocorrencia,
            'str_motiv_a': motivos[0],
            'str_motiv_b': motivos[1],
            'str_motiv_c': motivos[2],
            'str_motiv_d': motivos[3],
            'str_motiv_e': motivos[4],
            'valor': float(evento.valor_titulo)/100,
        }
        cnab_move = self.env['l10n_br_cnab.move']

        return cnab_move.create(vals)

    @api.multi
    def buscar_account_move_line(self, referencia_invoice, partner=False):
        move_line_name = referencia_invoice
        move_line_model = self.env['account.move.line']
        move_line_item = move_line_model.search(
            [('name', '=', move_line_name),
             ('debit', '>', 0),
             ('account_id.type', '=', 'receivable')
             ], limit=1)

        if move_line_item:
            partner = move_line_item.partner_id

        return move_line_item, partner
