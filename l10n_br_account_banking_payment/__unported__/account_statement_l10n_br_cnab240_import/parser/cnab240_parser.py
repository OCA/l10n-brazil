# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Luis Felipe Mileo - mileo at kmee.com.br
#    Copyright 2014 KMEE - www.kmee.com.br
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

import tempfile
import datetime
from openerp.tools.translate import _
from openerp.addons.account_statement_base_import.parser import \
    BankStatementImportParser

try:
    import cnab240
    from cnab240.bancos import cef
    from cnab240.tipos import Arquivo
    import codecs
except:
    raise Exception(_('Please install python lib cnab240'))


class Cnab240Parser(BankStatementImportParser):
    """Class for defining parser for OFX file format."""

    @classmethod
    def parser_for(cls, parser_name):
        """Used by the new_bank_statement_parser class factory. Return true if
        the providen name is 'ofx_so'.
        """
        return parser_name == 'cnab240_so'

    def _custom_format(self, *args, **kwargs):
        """No other work on data are needed in this parser."""
        return True

    def _pre(self, *args, **kwargs):
        """No pre-treatment needed for this parser."""
        return True

    def _parse(self, *args, **kwargs):
        """Launch the parsing itself."""
        cnab240_file = tempfile.NamedTemporaryFile()
        cnab240_file.seek(0)
        cnab240_file.write(self.filebuffer)
        cnab240_file.flush()

        ret_file = codecs.open(cnab240_file.name, encoding='ascii')
        arquivo = Arquivo(cef, arquivo=ret_file)

        cnab240_file.close()

        res = []
        for lote in arquivo.lotes:
            for evento in lote.eventos:
                res.append({
                    'name': evento.sacado_nome,
                    'date': datetime.datetime.strptime(
                        str(evento.vencimento_titulo), '%d%m%Y'),
                    'amount': evento.valor_titulo,
                    'ref': evento.numero_documento,
                    'label': evento.sacado_inscricao_numero,  # cnpj
                    'transaction_id': evento.nosso_numero_identificacao,
                    # nosso numero
                    'commission_amount': evento.valor_tarifas,
                })

        self.result_row_list = res
        return True

    def _validate(self, *args, **kwargs):
        """Nothing to do here. ofxparse trigger possible format errors."""
        return True

    def _post(self, *args, **kwargs):
        """Nothing is needed to do after parsing."""
        return True

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
