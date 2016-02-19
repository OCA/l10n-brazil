# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 KMEE (http://www.kmee.com.br)
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

    if partner.is_company:
        tipo_pessoa_busca = 'J'
    else:
        tipo_pessoa_busca = 'F'

    document = punctuation_rm(partner.cnpj_cpf)
    company_document = punctuation_rm(company.cnpj_cpf)

    documento_consultado = "%015d" % int(document)
    documento_consultor = "%014d" % int(company_document)
    login = str("%08d" % int(company.logon_serasa))
    senha = str("%08s" % str(company.senha_serasa))

    # Objeto que gerencia todas as funções de parsing
    parser = parserStringDados.ParserStringDados()

    # Variavel que recebe o a string de retorno do Serasa
    # string_teste_completa = 'B49C      006343654000102JC     FI0001000000000000000N99SFIMAN                            SS              N                                            14201058000108  000000000               00  2016021615580200000025    0026                                                                        0000                    3#                                                                             P002RE02                                                                                                           N00100PPX2PJN0    776593                       FEX                                                                 N00300                     RS                                                                                      N20000MARCIO SANTOS DA ROSA                                                 240620042 13022016                     N20001                                                                                                             N21099NAO CONSTAM OCORRENCIAS                                                                                      N23099NAO CONSTAM OCORRENCIAS                                                                                      N2400016062015DUPLICATA                     NR$ 0000000000465192102163340001014GETNET S/A                    NHO   N24001                                                                             V1758223121                     N2409000001062015062015000000000046519V                                                                            N2500018012016R$ 000000000072204UNSANTA MARIA                   RS                                                 N25001N                                                                            A0225920010                     N2500014012016R$ 000000000058437UNSANTA MARIA                   RS                                                 N25001N                                                                            A0225784271                     N2500014012016R$ 000000000022300UNSANTA MARIA                   RS                                                 N25001N                                                                            A0225784260                     N2500012012016R$ 000000000055300UNSANTA MARIA                   RS                                                 N25001N                                                                            A0225645901                     N2500018122015R$ 000000000072204UNSANTA MARIA                   RS                                                 N25001N                                                                            A0224751641                     N2509000088052014012016R$ 000000006986166                                                                          N2700017122015CCF-BB         00003               041BANRISUL      0377SANTA MARIA                   RS0119225042   N270900000330102015171220150410377BANRISUL                                                                         N44003008000000000                                                                                                 T999000PROCESSO ENCERRADO NORMALMENTE'
    # string_dados = string_teste_completa
    string_dados = parser.realizar_busca_serasa(parser.gerar_string_envio(
        documento_consultado, tipo_pessoa_busca, documento_consultor,
        partner.state_id.code,login, senha))

    arquivo = crednet.Crednet()

    # Gera o arquivo parseado separando os blocos da string de retorno
    # segundo o manual do Crednet do Serasa versão:06 de Janeiro/2014
    arquivo = parser.parser_string_dados_retorno(string_dados, arquivo)

    if len(arquivo.blocos) == 4:
        print string_dados
        return "Usuario ou senha do serasa invalidos"

    retorno_consulta = {
            'status': 'Aprovado',
            'fundacao': '',
            'texto': '',
            'pefin': '',
            'total_pefin': '',
            'protesto': '',
            'total_protesto': '',
            'cheque': '',
            'total_cheque': '',
        }

    retorno_consulta = retorna_pefin(
        retorno_consulta, arquivo.get_bloco_de_registros(
            'pendenciasFinanceiras'))
    retorno_consulta = retorna_protesto(
        retorno_consulta, arquivo.get_bloco_de_registros('protestosEstados'))
    retorno_consulta = retorna_cheques(
        retorno_consulta, arquivo.get_bloco_de_registros('chequesSemFundos'))
    retorno_consulta = retorno_detalhes_string_retorno(
        retorno_consulta, arquivo)

    blocoN200 = arquivo.get_bloco_de_registros('N200')

    retorno_consulta['fundacao'] = blocoN200.dataNascFundacao

    return retorno_consulta


def retorna_pefin(retorno_consulta, bloco):
    if len(bloco.blocos) > 1:
        retorno_consulta['status'] = "Não aprovado"

    pefin = []

    if len(bloco.blocos) > 0:
        for registro in bloco.blocos:
            if registro.campos.campos[1]._valor == u'00':
                pefin_dic = {
                    'modalidade': registro.campos.campos[3]._valor,
                    'origem': registro.campos.campos[8]._valor,
                    'avalista': 'Não' if registro.campos.campos[4] else 'Sim',
                    'contrato': registro.campos.campos[7]._valor,
                    'date': registro.campos.campos[2]._valor,
                    'value': registro.campos.campos[6]._valor,
                }
                pefin.append(pefin_dic)
            if registro.campos.campos[1]._valor == u'90':
                pefin_total = {
                    'num_ocorrencias': registro.campos.campos[2]._valor,
                    'total': registro.campos.campos[5]._valor,
                }
                retorno_consulta['total_pefin'] = pefin_total
    retorno_consulta['pefin'] = pefin
    pefin = []

    return retorno_consulta


def retorna_protesto(retorno_consulta, bloco):
    if len(bloco.blocos) > 1:
        retorno_consulta['status'] = "Não aprovado"

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
            if registro.campos.campos[1]._valor == u'90':
                protesto_total = {
                    'num_ocorrencias': registro.campos.campos[2]._valor,
                    'total': registro.campos.campos[6]._valor,
                }
                retorno_consulta['total_protesto'] = protesto_total
        retorno_consulta['protestosEstados'] = protesto
        protesto = []

        return retorno_consulta


def retorna_cheques(retorno_consulta, bloco):
    if len(bloco.blocos) > 1:
        retorno_consulta['status'] = "Não aprovado"

    cheque = []

    if len(bloco.blocos) > 0:
        for registro in bloco.blocos:
            if registro.campos.campos[1]._valor == u'00':
                if registro.campos.campos[6]._valor.replace(" ","") != "":
                    cheque_dic = {
                        'num_cheque': registro.campos.campos[3]._valor,
                        'alinea': int(registro.campos.campos[4]._valor)
                        if registro.campos.campos[4]._valor.replace(" ", "") !=
                           '' else 0,
                        'name_bank': registro.campos.campos[8]._valor,
                        'date': registro.campos.campos[2]._valor,
                        'city': registro.campos.campos[10]._valor,
                        'uf': registro.campos.campos[11]._valor,
                        'value': registro.campos.campos[6]._valor,
                    }
                    cheque.append(cheque_dic)
                else:
                    cheque_dic = {
                        'num_cheque': registro.campos.campos[3]._valor,
                        'alinea': int(registro.campos.campos[4]._valor)
                        if registro.campos.campos[4]._valor.replace(" ", "") !=
                           '' else 0,
                        'name_bank': registro.campos.campos[8]._valor,
                        'date': registro.campos.campos[2]._valor,
                        'city': registro.campos.campos[10]._valor,
                        'uf': registro.campos.campos[11]._valor,
                        'value': 0.00,
                    }
                    cheque.append(cheque_dic)
            if registro.campos.campos[1]._valor == u'90':
                cheque_total = {
                    'num_ocorrencias': registro.campos.campos[2]._valor,
                }
                retorno_consulta['total_cheque'] = cheque_total
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
