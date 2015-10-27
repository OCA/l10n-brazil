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
        tipoPessoaBusca = 'J'
    else:
        tipoPessoaBusca = 'F'

    document = punctuation_rm(partner.cnpj_cpf)
    company_document = punctuation_rm(company.cnpj_cpf)

    documentoConsultado = "%015d" % int(document)
    documentoConsultor = "%014d" % int(company_document)

    # Objeto que gerencia todas as funções de parsing
    parser = parserStringDados.ParserStringDados()

    # Variavel que recebe o a string de retorno do Serasa
    stringDados = parser.realizarBuscaSerasa(parser.gerarStringEnvio(logon, senha, documentoConsultado, tipoPessoaBusca,
                                                                     documentoConsultor))

    arquivo = crednet.Crednet()

    # stringDados = 'B49C      062173620000180JC     FI0001000000000000000N99SFIMAN                            SS              N                                            06217362000180  000000000               00  2014071811253000000025    0026                                                                        0000                    3#                                                                            P002RE02                                                                                                          N00100PPX25PN0    7                            EEX                                                                N20000SERASA S/A                                                            191019702 27022013                    N20001                                                                                                            N21099NAO CONSTAM OCORRENCIAS                                                                                     N23099NAO CONSTAM OCORRENCIAS                                                                                     N2400028052013FINANCIAMENTO                 NR$ 0000000012547899897879878974522SERASA                        SPO  N24001N                                                                            V0030188217                    N2400001012012ADIANT CONTA                  SR$ 00000000000165401              SERASA                        SPO  N24001N                                                                            V0026548030                    N2409000002012012052013000000001256443V                                                                           N2400001082012ADIANT CONTA                  NR$ 00000000012200101              B DO BRASIL                   SPO  N24001SDIVIDA SUB JUDICE                                                           I0025647992                    N2409000001082012082012000000000122001I                                                                           N2400012112013SENTENCA JUDICIAL             NR$ 0000000000080004599            E.B.O.T.E. EMPRESA B               N24001N                                                                            50032468375                    N2400010052011CERT DIV EN 76                NR$ 000000000030000123456789       BAU                           SPO  N24001N                                                                            50019767719                    N24090000020520111120130000000000380005                                                                           N25099NAO CONSTAM OCORRENCIAS                                                                                     N2700001082010CCF-BB         00006               409UNIBANCO      0001ALFENAS                       MG0010104940  N270000107201000000000450001200001000000000055400356ABN AMRO      2020                                0000051460  N270900002201072010011120104090001UNIBANCO                                                                        N44099NAO CONSTAM INFORMACOES                                                                                     T999000PROCESSO ENCERRADO NORMALMENTE                                                                             '

    # Gera o arquivo parseado separando os blocos da string de retorno
    # segundo o manual do Crednet do Serasa versão:06 de Janeiro/2014
    arquivo = parser.parserStringDadosRetorno(stringDados, arquivo)


    #TODO: ME tire daqui por favor!
    if arquivo.T999.codigo == u'023':
        from openerp.exceptions import Warning
        raise Warning(arquivo.T999.mensagem)

    retornoConsulta = {
            'status': '',
            'texto': '',
            'pefin': '',
            'protesto': '',
            'cheque': '',
        }

    retornoConsulta = retorna_pefin(retornoConsulta, arquivo.getBlocoDeRegistros('pendenciasFinanceiras'))
    retornoConsulta = retorna_protesto(retornoConsulta, arquivo.getBlocoDeRegistros('protestosEstados'))
    retornoConsulta = retorna_cheques(retornoConsulta, arquivo.getBlocoDeRegistros('chequesSemFundos'))
    retornoConsulta = retorno_detalhes_string_retorno(retornoConsulta, arquivo)

    return retornoConsulta


def retorna_pefin(retornoConsulta, bloco):
    if len(bloco.blocos) > 1:
        retornoConsulta['status'] = "Não aprovado"
    else:
        retornoConsulta['status'] = "Aprovado"

    pefin = []

    if len(bloco.blocos) > 0:
        for registro in bloco.blocos:
            if registro.campos.campos[1]._valor == u'00':
                pefinDic = {
                    'modalidade': registro.campos.campos[3]._valor,
                    'origem': registro.campos.campos[8]._valor,
                    'avalista': 'Não' if registro.campos.campos[4] else 'Sim',
                    'date': registro.campos.campos[2]._valor,
                    'value': registro.campos.campos[6]._valor,
                }
                pefin.append(pefinDic)

    retornoConsulta['pefin'] = pefin
    pefin = []

    return retornoConsulta


def retorna_protesto(retornoConsulta, bloco):
    if len(bloco.blocos) > 1:
        retornoConsulta['status'] = "Não aprovado"
    else:
        retornoConsulta['status'] = "Aprovado"

    protesto = []

    if len(bloco.blocos) > 0:
        for registro in bloco.blocos:
            if registro.campos.campos[1]._valor == u'00':
                protestoDic = {
                    'cartorio': registro.campos.campos[5]._valor,
                    'city': registro.campos.campos[6]._valor,
                    'uf': registro.campos.campos[7]._valor,
                    'date': registro.campos.campos[2]._valor,
                    'value': registro.campos.campos[4]._valor,
                }
                protesto.append(protestoDic)

        retornoConsulta['protestosEstados'] = protesto
        protesto = []

        return retornoConsulta


def retorna_cheques(retornoConsulta, bloco):
    if len(bloco.blocos) > 1:
        retornoConsulta['status'] = "Não aprovado"
    else:
        retornoConsulta['status'] = "Aprovado"

    cheque = []

    if len(bloco.blocos) > 0:
        for registro in bloco.blocos:
            if registro.campos.campos[1]._valor == u'00':
                chequeDic = {
                    'num_cheque': registro.campos.campos[3]._valor,
                    'name_bank': registro.campos.campos[8]._valor,
                    'date': registro.campos.campos[2]._valor,
                    'city': registro.campos.campos[10]._valor,
                    'uf': registro.campos.campos[11]._valor,
                    'value': registro.campos.campos[6]._valor,
                }
                cheque.append(chequeDic)

    retornoConsulta['cheque'] = cheque
    cheque = []

    return retornoConsulta


def retorno_detalhes_string_retorno(retornoConsulta, arquivo, bloco=None):
    if bloco is None:
        retorno_string = arquivo.get_string()
    else:
        retorno_string = arquivo.get_string(bloco)

    retornoConsulta['texto'] = retorno_string
    return retornoConsulta
