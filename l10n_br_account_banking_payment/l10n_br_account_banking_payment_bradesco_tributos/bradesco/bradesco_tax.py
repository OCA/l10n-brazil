# coding: utf-8
# ###########################################################################
#
#    Author: Luis Felipe Mileo
#            Luiz Felipe do Divino
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

from fixedwidth.fixedwidth import FixedWidth
from openerp.addons.l10n_br_base.tools.misc import punctuation_rm
from decimal import Decimal
import unicodedata

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

class BradescoTax(object):
    def __init__(self):
        pass

    def remessa(self, order):
        return False

    def retorno(self, cnab_file):
        return object


class BradescoTaxLine(object):

    def __init__(self, ):
        pass

    def remessa(self, order):
        return False

    def retorno(self, cnab_file):
        return object


class BradescoGnre(BradescoTaxLine):

    def __init__(self):
        self.LAYOUT_GNRE = {

            "identificador_tributo": {
                "required": False,
                "type": "string",
                "start_pos": 1,
                "end_pos": 1,
                "alignment": "left",
                "padding": " "
            },

            "nome_cliente": {
                "required": False,
                "type": "string",
                "start_pos": 2,
                "end_pos": 41,
                "alignment": "left",
                "padding": " "
            },

            "endereco_cliente": {
                "required": False,
                "type": "string",
                "start_pos": 42,
                "end_pos": 81,
                "alignment": "left",
                "padding": " "
            },

            "cep_cliente": {
                "type": "string",
                "start_pos": 82,
                "end_pos": 89,
                "padding": " ",
                "required": False,
                "alignment": "left"
            },

            "uf_cliente": {
                "type": "string",
                "start_pos": 90,
                "padding": " ",
                "end_pos": 91,
                "alignment": "left",
                "required": False
            },

            "cidade_cliente": {
                "type": "string",
                "start_pos": 92,
                "padding": " ",
                "end_pos": 111,
                "alignment": "left",
                "required": False
            },

            "tipo_inscricao": {
                "type": "string",
                "start_pos": 112,
                "padding": " ",
                "end_pos": 112,
                "alignment": "left",
                "required": False
            },

            "numero_inscricao": {
                "type": "string",
                "start_pos": 113,
                "padding": " ",
                "end_pos": 127,
                "alignment": "left",
                "required": False
            },

            "telefone_cliente": {
                "type": "string",
                "start_pos": 128,
                "padding": " ",
                "end_pos": 147,
                "alignment": "left",
                "required": False
            },

            "data_pagamento_tributo": {
                "type": "string",
                "start_pos": 148,
                "padding": " ",
                "end_pos": 155,
                "alignment": "left",
                "required": False
            },

            "autoriza_pagamento": {
                "type": "string",
                "start_pos": 156,
                "padding": " ",
                "end_pos": 156,
                "alignment": "left",
                "required": False
            },

            "valor_do_principal": {
                "type": "string",
                "start_pos": 157,
                "padding": "0",
                "end_pos": 171,
                "alignment": "right",
                "required": False
            },

            "valor_de_juros": {
                "type": "string",
                "start_pos": 172,
                "padding": "0",
                "end_pos": 186,
                "alignment": "right",
                "required": False
            },

            "valor_de_multa": {
                "type": "string",
                "start_pos": 187,
                "padding": "0",
                "end_pos": 201,
                "alignment": "right",
                "required": False
            },

            "valor_atualizacao_monetaria": {
                "type": "string",
                "start_pos": 202,
                "padding": "0",
                "end_pos": 216,
                "alignment": "right",
                "required": False
            },

            "codigo_barras": {
                "type": "string",
                "start_pos": 217,
                "padding": " ",
                "end_pos": 264,
                "alignment": "left",
                "required": False
            },

            "data_vencimento_tributo": {
                "type": "string",
                "start_pos": 265,
                "padding": " ",
                "end_pos": 272,
                "alignment": "left",
                "required": False
            },

            "codigo_de_receita": {
                "type": "string",
                "start_pos": 273,
                "padding": " ",
                "end_pos": 278,
                "alignment": "left",
                "required": False
            },

            "uf_favorecida": {
                "type": "string",
                "start_pos": 279,
                "padding": " ",
                "end_pos": 280,
                "alignment": "left",
                "required": False
            },

            "num_doc_origem": {
                "type": "string",
                "start_pos": 281,
                "padding": "0",
                "end_pos": 293,
                "alignment": "right",
                "required": False
            },

            "reserva": {
                "type": "string",
                "start_pos": 294,
                "padding": " ",
                "end_pos": 294,
                "alignment": "left",
                "required": False
            },

            "referencia": {
                "type": "string",
                "start_pos": 295,
                "padding": " ",
                "end_pos": 295,
                "alignment": "left",
                "required": False
            },

            "mes": {
                "type": "string",
                "start_pos": 296,
                "padding": " ",
                "end_pos": 297,
                "alignment": "left",
                "required": False
            },

            "ano": {
                "type": "string",
                "start_pos": 298,
                "padding": " ",
                "end_pos": 301,
                "alignment": "left",
                "required": False
            },

            "reserva2": {
                "type": "string",
                "start_pos": 302,
                "padding": " ",
                "end_pos": 314,
                "alignment": "left",
                "required": False
            },

            "convenio": {
                "type": "string",
                "start_pos": 315,
                "padding": " ",
                "end_pos": 354,
                "alignment": "left",
                "required": False
            },

            "produto": {
                "type": "string",
                "start_pos": 355,
                "padding": " ",
                "end_pos": 356,
                "alignment": "left",
                "required": False
            },

            "codigo_subreceita": {
                "type": "string",
                "start_pos": 357,
                "padding": " ",
                "end_pos": 358,
                "alignment": "left",
                "required": False
            },

            "uso_da_empresa": {
                "type": "string",
                "start_pos": 359,
                "padding": " ",
                "end_pos": 458,
                "alignment": "left",
                "required": False
            },

            "inscricao_estadual": {
                "type": "string",
                "start_pos": 459,
                "padding": " ",
                "end_pos": 475,
                "alignment": "left",
                "required": False
            },

            "reserva3": {
                "type": "string",
                "start_pos": 476,
                "padding": " ",
                "end_pos": 663,
                "alignment": "left",
                "required": False
            },

            "cr_lf": {
                "type": "string",
                "start_pos": 664,
                "padding": " ",
                "end_pos": 665,
                "alignment": "left",
                "required": False
            },
        }


    def remessa(self, order):
        result = ''
        for line in order.line_ids:
            if line.partner_id.is_company:
                tipo_inscricao = '2'
            else:
                tipo_inscricao = '1'

            endereco01 = strip_accents(line.partner_id.street)
            # endereco02 = str(line.partner_id.street2.replace('º', ''))
            endereco_cliente = endereco01
            vals = {
                'identificador_tributo': 'G',
                'nome_cliente': str(line.partner_id.name),
                'endereco_cliente': endereco_cliente,
                'cep_cliente': str(punctuation_rm(line.partner_id.zip)),
                'uf_cliente': str(line.partner_id.state_id.code),
                'autoriza_pagamento': 'S',
                'tipo_inscricao': tipo_inscricao,
                'uf_favorecida': str(line.partner_id.state_id.code),
                'telefone_cliente': str(punctuation_rm(line.partner_id.phone)),
                'numero_inscricao': str(
                    punctuation_rm(line.partner_id.cnpj_cpf)
                                        ),
                'valor_do_principal': punctuation_rm(str(line.amount_currency)),
                'data_pagamento_tributo': punctuation_rm(line.date),
                'data_vencimento_tributo': punctuation_rm(line.date),
                'codigo_de_receita': str(punctuation_rm(
                    line.order_id.mode.gnre_type.code)),
                'num_doc_origem': str(punctuation_rm(line.ml_inv_ref.internal_number)),
            }
            result += "%s\n" % self._remessa(**vals)
        return result

    def _remessa(self, **kwargs):
        fw_obj = FixedWidth(self.LAYOUT_GNRE)
        fw_obj.update(**kwargs)
        return fw_obj.line

    def _retorno(self, line):
        fw_obj = FixedWidth(self.LAYOUT_GNRE)
        fw_obj.line = line
        return fw_obj.data
