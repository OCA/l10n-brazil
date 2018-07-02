# -*- coding: utf-8 -*-
#  ABGF <hendrix.costa@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

import pysped


if __name__ == '__main__':

    s2205 = pysped.esocial.leiaute.S2205_2()


    s2205.validar()

    # s1000.evento.ideEvento.tpAmb.valor = '2'
    # s1000.evento.ideEvento.procEmi.valor = '1'
    # s1000.evento.ideEvento.verProc.valor = '6.1'
    # s1000.evento.ideEmpregador.tpInsc.valor = '1'
    # s1000.evento.ideEmpregador.nrInsc.valor = '03541876000133'
    #
    # s1000.evento.infoEmpregador.operacao = 'I'
    # s1000.evento.infoEmpregador.idePeriodo.iniValid.valor = '2018-01'
    #
    # s1000.evento.infoEmpregador.infoCadastro.nmRazao.valor = 'CENTRAL SERVICE VIGILÂNCIA LTDA'
    # s1000.evento.infoEmpregador.infoCadastro.contato.nmCtt.valor = 'CENTRAL SERVICE VIGILÂNCIA LTDA'
    # s1000.evento.infoEmpregador.infoCadastro.contato.cpfCtt.valor = '06615190907'
    #
    # data_hora = '20180507180000'
    # s1000.gera_id_evento(data_hora)
    #
    # processador = pysped.ProcessadorESocial()
    # processador.certificado.arquivo = '/home/wagner/Downloads/abgf.p12'
    # processador.certificado.senha = '122017'  # ou "abgf@2016"
    #
    # processo = processador.enviar_lote([s1000])
    #
    # print(processo.resposta.xml)
    #
    # if processo.resposta.retornoEnvioLoteEventos.status.ocorrencias:
    #     for ocorrencia in processo.resposta.retornoEnvioLoteEventos.status.ocorrencias:
    #         print('nova ocorrencia')
    #         print(ocorrencia.xml)

