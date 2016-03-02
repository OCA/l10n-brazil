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
    # string_teste_completa = 'B49C      071037337000111JC     FI0001000000000000000N99SFIMAN                            SS              N                                            14201058000108  000000000               00  2016030114084600000037    0038                                                                        0000                    3#                                                                             P002RE02                                                                                                           N00100PPX2PJN0    712406                       FCM                                                                 N00300                     MG                                                                                      N20000RELOJOARIA QUEIROZ LTDA ME                                            060519932 03022016                     N20001                                                                                                             N21099NAO CONSTAM OCORRENCIAS                                                                                      N23099NAO CONSTAM OCORRENCIAS                                                                                      N2400027012016DUPLICATA                     NR$ 00000000004305001DE1 028540904 ORIENT                              N24001                                                                             V1897063290                     N2400023072014OUTRAS OPER                   NR$ 0000000000171008825            JOSE ANTONIO ALVES ASSIS ME         N24001                                                                             V1832800078                     N2400011072014OUTRAS OPER                   NR$ 0000000002806502302            ALVES & LUCIANO LTDA ME             N24001                                                                             V1817659459                     N2400010072014OUTRAS OPER                   NR$ 0000000002225827417            JOSE ANTONIO ALVES ASSIS ME         N24001                                                                             V1832800073                     N2409000004072014012016000000000563382V                                                                            N2400006102015DUPLICATA DE VENDA MERCANTIL  NR$ 00000000004024015739825376     EWC RIO C E R ART DE                N24001                                                                             51834899746                     N2400006092015DUPLICATA DE VENDA MERCANTIL  NR$ 00000000004024015739825375     EWC RIO C E R ART DE                N24001                                                                             51834192792                     N2400007082015DUPLICATA DE VENDA MERCANTIL  NR$ 00000000004024015739825374     EWC RIO C E R ART DE                N24001                                                                             51834192789                     N24090000030820151020150000000001207205                                                                            N2500004122015R$ 00000000008480001DIVINOPOLIS                   MG                                                 N25001N                                                                            A0223790769                     N2500030112015R$ 00000000004395701DIVINOPOLIS                   MG                                                 N25001N                                                                            A0223710944                     N2500025112015R$ 00000000003594201DIVINOPOLIS                   MG                                                 N25001N                                                                            A0223527004                     N2500024112015R$ 00000000006133501DIVINOPOLIS                   MG                                                 N25001N                                                                            A0223526858                     N2500023112015R$ 00000000004381401DIVINOPOLIS                   MG                                                 N25001N                                                                            A0223526774                     N2509000039102012122015R$ 000000002607113                                                                          N27099NAO CONSTAM OCORRENCIAS                                                                                      N44003002000000000                                                                                                 T999000PROCESSO ENCERRADO NORMALMENTE    '
    # string_dados = string_teste_completa
    string_dados = parser.realizar_busca_serasa(parser.gerar_string_envio(
        documento_consultado, tipo_pessoa_busca, documento_consultor,
        partner.state_id.code,login, senha))

    arquivo = crednet.Crednet()

    # Gera o arquivo parseado separando os blocos da string de retorno
    # segundo o manual do Crednet do Serasa versão:06 de Janeiro/2014
    if 'HA INCONSISTENCIAS NOS DADOS ENVIADOS' in string_dados:
        return u"Há inconsistencias nos dados enviados, " \
               u"verificar o cpf/cnpj e se o cliente é empresa ou pessoa fisica"
    else:
        arquivo = parser.parser_string_dados_retorno(string_dados, arquivo)

    if len(arquivo.blocos) == 4:
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
