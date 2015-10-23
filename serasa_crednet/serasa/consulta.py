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
    logon = '32629955'
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

    # Gera o arquivo parseado separando os blocos da string de retorno
    # segundo o manual do Crednet do Serasa versão:06 de Janeiro/2014
    arquivo = parser.parserStringDadosRetorno(stringDados, arquivo)

    bloco = arquivo.getBlocoDeRegistros('pendenciasFinanceiras')

    if len(bloco.blocos) > 1:
        status = "Não aprovado"
    else:
        status = "Aprovado"
    texto = bloco.nome + "\n" + "------------------------------------------------------" + "\n"
    for registro in bloco.blocos:
        for campos in registro.campos.campos:
            texto = texto + campos._nome + ": " + str(campos._valor) + "\n"
        texto = texto + "\n"

    arquivo = None
    return status, texto
