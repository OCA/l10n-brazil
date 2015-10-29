# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 KMEE (http://www.kmee.com.br)
#    @author Luiz Felipe do Divino (luiz.divino@kmee.com.br)
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

from pyserasa import crednet
from pyserasa import parserStringDados
from openerp.addons.l10n_br_base.tools.misc import punctuation_rm


def consulta_cnpj(partner, company):

    # TODO:
    logon = '31563967'
    senha = '10203040'

    if partner.is_company:
        tipo_pessoa_busca = 'J'
    else:
        tipo_pessoa_busca = 'F'

    document = punctuation_rm(partner.cnpj_cpf)
    company_document = punctuation_rm(company.cnpj_cpf)

    documento_consultado = "%015d" % int(document)
    documento_consultor = "%014d" % int(company_document)

    # Objeto que gerencia todas as funções de parsing
    parser = parserStringDados.ParserStringDados()

    # Variavel que recebe o a string de retorno do Serasa
    string_dados = parser.realizarBuscaSerasa(parser.gerarStringEnvio(
        logon, senha, documento_consultado, tipo_pessoa_busca,
        documento_consultor))

    arquivo = crednet.Crednet()

    # Gera o arquivo parseado separando os blocos da string de retorno
    # segundo o manual do Crednet do Serasa versão:06 de Janeiro/2014
    arquivo = parser.parserStringDadosRetorno(string_dados, arquivo)


    #TODO: ME tire daqui por favor!
    if arquivo.T999.codigo == u'023':
        from openerp.exceptions import Warning
        raise Warning(arquivo.T999.mensagem)

    retorno_consulta = {
            'status': '',
            'fundacao': '',
            'texto': '',
            'pefin': '',
            'protesto': '',
            'cheque': '',
        }

    retorno_consulta = retorna_pefin(
        retorno_consulta, arquivo.getBlocoDeRegistros('pendenciasFinanceiras'))
    retorno_consulta = retorna_protesto(
        retorno_consulta, arquivo.getBlocoDeRegistros('protestosEstados'))
    retorno_consulta = retorna_cheques(
        retorno_consulta, arquivo.getBlocoDeRegistros('chequesSemFundos'))
    retorno_consulta = retorno_detalhes_string_retorno(
        retorno_consulta, arquivo)

    blocoN200 = arquivo.getBlocoDeRegistros('N200')

    retorno_consulta['fundacao'] = blocoN200.dataNascFundacao

    return retorno_consulta


def retorna_pefin(retorno_consulta, bloco):
    if len(bloco.blocos) > 1:
        retorno_consulta['status'] = "Não aprovado"
    else:
        retorno_consulta['status'] = "Aprovado"

    pefin = []

    if len(bloco.blocos) > 0:
        for registro in bloco.blocos:
            if registro.campos.campos[1]._valor == u'00':
                pefin_dic = {
                    'modalidade': registro.campos.campos[3]._valor,
                    'origem': registro.campos.campos[8]._valor,
                    'avalista': 'Não' if registro.campos.campos[4] else 'Sim',
                    'date': registro.campos.campos[2]._valor,
                    'value': registro.campos.campos[6]._valor,
                }
                pefin.append(pefin_dic)

    retorno_consulta['pefin'] = pefin
    pefin = []

    return retorno_consulta


def retorna_protesto(retorno_consulta, bloco):
    if len(bloco.blocos) > 1:
        retorno_consulta['status'] = "Não aprovado"
    else:
        retorno_consulta['status'] = "Aprovado"

    protesto = []

    if len(bloco.blocos) > 0:
        for registro in bloco.blocos:
            if registro.campos.campos[1]._valor == u'00':
                protesto_dic = {
                    'cartorio': registro.campos.campos[5]._valor,
                    'city': registro.campos.campos[6]._valor,
                    'uf': registro.campos.campos[7]._valor,
                    'date': registro.campos.campos[2]._valor,
                    'value': registro.campos.campos[4]._valor,
                }
                protesto.append(protesto_dic)

        retorno_consulta['protestosEstados'] = protesto
        protesto = []

        return retorno_consulta


def retorna_cheques(retorno_consulta, bloco):
    if len(bloco.blocos) > 1:
        retorno_consulta['status'] = "Não aprovado"
    else:
        retorno_consulta['status'] = "Aprovado"

    cheque = []

    if len(bloco.blocos) > 0:
        for registro in bloco.blocos:
            if registro.campos.campos[1]._valor == u'00':
                cheque_dic = {
                    'num_cheque': registro.campos.campos[3]._valor,
                    'alinea': int(registro.campos.campos[4]._valor),
                    'name_bank': registro.campos.campos[8]._valor,
                    'date': registro.campos.campos[2]._valor,
                    'city': registro.campos.campos[10]._valor,
                    'uf': registro.campos.campos[11]._valor,
                    'value': registro.campos.campos[6]._valor,
                }
                cheque.append(cheque_dic)

    retorno_consulta['cheque'] = cheque
    cheque = []

    return retorno_consulta


def retorno_detalhes_string_retorno(retorno_consulta, arquivo, bloco=None):
    if bloco is None:
        retorno_string = arquivo.get_string()
    else:
        retorno_string = arquivo.get_string(bloco)

    retorno_consulta['texto'] = retorno_string
    return retorno_consulta
