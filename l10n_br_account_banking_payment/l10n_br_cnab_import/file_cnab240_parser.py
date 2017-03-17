# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Luis Felipe Mileo - mileo at kmee.com.br
#            Fernando Marcato Rodrigues
#    Copyright 2015 KMEE - www.kmee.com.br
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

import datetime
import tempfile

from openerp import _

try:
    from cnab240.tipos import Arquivo
    import codecs
except:
    raise Exception(_('Please install python lib PyCNAB'))


class Cnab240Parser(object):
    """Class for defining parser for OFX file format."""

    @classmethod
    def parser_for(cls, parser_name):
        """Used by the new_bank_statement_parser class factory. Return true if
        the providen name is 'ofx_so'.
        """
        return parser_name == 'cnab240_so'

    @staticmethod
    def determine_bank(nome_impt):
        if nome_impt == 'bradesco_pag_for':
            from cnab240.bancos import bradescoPagFor
            return bradescoPagFor
        elif nome_impt == 'bradesco_cobranca_240':
            from cnab240.bancos import bradesco
            return bradesco
        elif nome_impt == 'itau_cobranca_240':
            from cnab240.bancos import itau
            return itau
        else:
            raise Warning(_('Modo de importação não encontrado.'))

    def parse(self, data, banco_impt):
        """Launch the parsing itself."""
        cnab240_file = tempfile.NamedTemporaryFile()
        cnab240_file.seek(0)
        cnab240_file.write(data)
        cnab240_file.flush()
        ret_file = codecs.open(cnab240_file.name, encoding='ascii')

        # Nome_modo_impt é o nome da pasta do json. Código do banco é inválido
        # nessa situação
        arquivo = Arquivo((self.determine_bank(banco_impt)), arquivo=ret_file)

        cnab240_file.close()

        res = []
        transacoes = []
        for lote in arquivo.lotes:
            for evento in lote.eventos:
                transacoes.append({
                    'name': evento.sacado_nome,
                    'date': datetime.datetime.strptime(
                        str(evento.vencimento_titulo), '%d%m%Y'),
                    'amount': evento.valor_titulo,
                    'ref': evento.numero_documento,
                    'label': evento.sacado_inscricao_numero,  # cnpj
                    'transaction_id': evento.numero_documento,
                    # nosso numero, Alfanumérico
                    'unique_import_id': evento.numero_documento,
                })

                res.append({
                    'name': evento.sacado_nome,
                    'date': datetime.datetime.strptime(
                        str(evento.vencimento_titulo), '%d%m%Y'),
                    'amount': evento.valor_titulo,
                    'ref': evento.numero_documento,
                    'label': evento.sacado_inscricao_numero,  # cnpj
                    'transaction_id': evento.numero_documento,
                    # nosso numero
                    'commission_amount': evento.valor_tarifas,

                    'currency_code': u'BRL',  # Código da moeda
                    'account_number': evento.cedente_conta,
                    'transactions': transacoes,
                })
                transacoes = []

        self.result_row_list = res
        return res

    def get_st_line_vals(self, line, *args, **kwargs):
        """This method must return a dict of vals that can be passed to create
        method of statement line in order to record it. It is the
        responsibility of every parser to give this dict of vals, so each one
        can implement his own way of recording the lines.
            :param: line: a dict of vals that represent a line of
                result_row_list
            :return: dict of values to give to the create method of statement
                line
        """
        return {
            'name': line.get('name', ''),
            'date': line.get('date', datetime.datetime.now().date()),
            'amount': line.get('amount', 0.0),
            'ref': line.get('ref', '/'),
            'label': line.get('label', ''),
            'transaction_id': line.get('transaction_id', '/'),
            'commission_amount': line.get('commission_amount', 0.0)
        }
