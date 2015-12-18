# -*- encoding: utf-8 -*-
##############################################################################
#
#    Brazillian 5 acts module for OpenERP
#    Copyright (C) 2015 KMEE (http://www.kmee.com.br)
#    @author Bianca Tella <bianca.tella@kmee.com.br>
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

from sped.fci import arquivos
import base64
from openerp import api
from openerp.exceptions import Warning
from openerp.addons.l10n_br_base.tools.misc import punctuation_rm


@api.multi
def create_fci(fci):
    arq = arquivos.ArquivoDigital()

    cpf_cnpj_numbers = punctuation_rm(fci.company_id.partner_id.cnpj_cpf)
    inscr_est_numbers = punctuation_rm(fci.company_id.partner_id.inscr_est)
    zip_numbers = punctuation_rm(fci.company_id.partner_id.zip)

    input0000 = ('0000|' + cpf_cnpj_numbers + '|' +
                 fci.company_id.partner_id.name + '|' +
                 '1.0')
    input0010 = ('0010|' + cpf_cnpj_numbers + '|' +
                 fci.company_id.partner_id.legal_name + '|' +
                 inscr_est_numbers + '|' +
                 fci.company_id.partner_id.street + ', ' +
                 fci.company_id.partner_id.number + '|' +
                 zip_numbers + '|' +
                 fci.company_id.partner_id.l10n_br_city_id.name + '|' +
                 fci.company_id.partner_id.state_id.code)
    for line in fci.fci_line:
        if not line.valor_parcela_importada:
            raise Warning(('Error!'), (
                'O campo Valor parcela importada nao pode ser zero'))
        else:
            line.ncm_id_numbers = punctuation_rm(line.fiscal_classification_id)
            input5020 = ('5020|' +
                         line.name + '|' +
                         str(line.ncm_id_numbers) + '|' +
                         line.default_code + '|' +
                         str(line.ean13) + '|' +
                         (line.product_uom.name or '99') + '|' +
                         str("{0:.2f}".format(round(line.list_price))).
                         replace('.', ',') + '|' +
                         str("{0:.2f}".
                             format(round(line.valor_parcela_importada, 2))).
                         replace('.',',') + '|' +
                         str("{0:.2f}".
                             format(round(line.conteudo_importacao, 2))).
                         replace('.', ','))
        arq.read_registro(input5020)
    arq.read_registro(input0000)
    arq.read_registro(input0010)

    return base64.b64encode(arq.getstring().encode('utf-8'))


def import_fci(file_name):
    arq_entrada = arquivos.ArquivoDigital()

    file_entrada = base64.decodestring(file_name)
    file_entrada = file_entrada.lstrip()
    file_entrada = file_entrada.rstrip()
    registros = file_entrada.split('\r\n')

    for reg in registros:
        arq_entrada.read_registro(reg)

    list_default_code = []
    list_fci_codes = []
    res = {
        'hash_code': arq_entrada._registro_abertura.valores[05],
        'dt_recepcao': arq_entrada._registro_abertura.valores[6],
        'cod_recepcao': arq_entrada._registro_abertura.valores[7],
        'dt_validacao': arq_entrada._registro_abertura.valores[8],
        'in_validacao': arq_entrada._registro_abertura.valores[9],
        'cnpj_cpf': arq_entrada._registro_abertura.valores[02],
        'default_code': list_default_code,
        'fci_codes': list_fci_codes
    }

    a = (res['cnpj_cpf'][:2] + "." + res['cnpj_cpf'][2:5] + "." +
         res['cnpj_cpf'][5:8] + "/" + res['cnpj_cpf'][8:12] + "-" +
         res['cnpj_cpf'][-2:])
    res['cnpj_cpf'] = a

    for registro5020 in arq_entrada._blocos['5'].registros:
        if registro5020.valores[01] == '5020':
            list_default_code.append(registro5020.valores[04])
            list_fci_codes.append(registro5020.valores[10])
    res['default_code'] = list_default_code

    return res
