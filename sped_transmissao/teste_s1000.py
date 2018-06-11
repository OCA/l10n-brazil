# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

import pysped


if __name__ == '__main__':
    s1000 = pysped.esocial.leiaute.S1000_2()
    s1000.evento.ideEvento.tpAmb.valor = '2'
    s1000.evento.ideEvento.procEmi.valor = '1'
    s1000.evento.ideEvento.verProc.valor = '6.1'
    s1000.evento.ideEmpregador.tpInsc.valor = '1'
    s1000.evento.ideEmpregador.nrInsc.valor = '03541876000133'

    s1000.evento.infoEmpregador.operacao = 'I'
    s1000.evento.infoEmpregador.idePeriodo.iniValid.valor = '2018-01'

    s1000.evento.infoEmpregador.infoCadastro.nmRazao.valor = 'CENTRAL SERVICE VIGILÂNCIA LTDA'
    s1000.evento.infoEmpregador.infoCadastro.contato.nmCtt.valor = 'CENTRAL SERVICE VIGILÂNCIA LTDA'
    s1000.evento.infoEmpregador.infoCadastro.contato.cpfCtt.valor = '06615190907'

    data_hora = '20180507180000'
    s1000.gera_id_evento(data_hora)

    processador = pysped.ProcessadorESocial()
    processador.certificado.arquivo = '/home/wagner/Downloads/abgf.p12'
    processador.certificado.senha = '122017'  # ou "abgf@2016"

    processo = processador.enviar_lote([s1000])

    print(processo.resposta.xml)

    if processo.resposta.retornoEnvioLoteEventos.status.ocorrencias:
        for ocorrencia in processo.resposta.retornoEnvioLoteEventos.status.ocorrencias:
            print('nova ocorrencia')
            print(ocorrencia.xml)


#if __name__ == '__main__':
    #retorno = pysped.esocial.leiaute.RetornoLoteEventosEsocial_10100()
    #retorno.xml = '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><EnviarLoteEventosResponse xmlns="http://www.esocial.gov.br/servicos/empregador/lote/eventos/envio/v1_1_0"> <EnviarLoteEventosResult><eSocial xmlns="http://www.esocial.gov.br/schema/lote/eventos/envio/retornoEnvio/v1_1_0" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><retornoEnvioLoteEventos><status><cdResposta>401</cdResposta><descResposta>Lote Incorreto - Erro preenchimento.</descResposta><ocorrencias><ocorrencia><codigo>381</codigo><descricao>CPF inv\xc3\xa1lido.</descricao><tipo>1</tipo><localizacao>/eSocial/envioLoteEventos/ideEmpregador/nrInsc</localizacao></ocorrencia><ocorrencia><codigo>381</codigo><descricao>CPF inv\xc3\xa1lido.</descricao><tipo>1</tipo><localizacao>/eSocial/envioLoteEventos/ideTransmissor/nrInsc</localizacao></ocorrencia></ocorrencias></status></retornoEnvioLoteEventos></eSocial></EnviarLoteEventosResult></EnviarLoteEventosResponse></s:Body></s:Envelope>'

    #print('original')
    #print('<eSocial xmlns="http://www.esocial.gov.br/schema/lote/eventos/envio/retornoEnvio/v1_1_0"><retornoEnvioLoteEventos><status><cdResposta>401</cdResposta><descResposta>Lote Incorreto - Erro preenchimento.</descResposta><ocorrencias><ocorrencia><codigo>381</codigo><descricao>CPF inv\xc3\xa1lido.</descricao><tipo>1</tipo><localizacao>/eSocial/envioLoteEventos/ideEmpregador/nrInsc</localizacao></ocorrencia><ocorrencia><codigo>381</codigo><descricao>CPF inv\xc3\xa1lido.</descricao><tipo>1</tipo><localizacao>/eSocial/envioLoteEventos/ideTransmissor/nrInsc</localizacao></ocorrencia></ocorrencias></status></retornoEnvioLoteEventos></eSocial>')
    #print('')
    #print('tratado')
    #print(retorno.xml)
