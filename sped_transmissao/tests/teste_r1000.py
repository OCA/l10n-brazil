# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

import pysped


if __name__ == '__main__':

    # R-1000 - Informações do Contribuinte
    r1000 = pysped.efdreinf.leiaute.R1000_1()
    r1000.evento.ideEvento.tpAmb.valor = '2'
    r1000.evento.ideEvento.procEmi.valor = '1'

    r1000.evento.ideEvento.verProc.valor = '8.0'
    # r1000.evento.ideEvento.verProc.valor = 'RemoverContribuinte'

    r1000.evento.ideContri.tpInsc.valor = '1'
    r1000.evento.ideContri.nrInsc.valor = '17909518'

    r1000.evento.infoContri.operacao = 'I'
    r1000.evento.infoContri.idePeriodo.iniValid.valor = '2018-05'

    r1000.evento.infoContri.infoCadastro.classTrib.valor = '99'
    # r1000.evento.infoContri.infoCadastro.classTrib.valor = '00'

    r1000.evento.infoContri.infoCadastro.indEscrituracao.valor = '1'
    r1000.evento.infoContri.infoCadastro.indDesoneracao.valor = '0'
    r1000.evento.infoContri.infoCadastro.indAcordoIsenMulta.valor = '0'
    r1000.evento.infoContri.infoCadastro.indSitPJ.valor = '0'

    r1000.evento.infoContri.infoCadastro.contato.nmCtt.valor = 'WagnerPereira'
    r1000.evento.infoContri.infoCadastro.contato.cpfCtt.valor = '13438768852'
    r1000.evento.infoContri.infoCadastro.contato.foneFixo.valor = '6132466242'
    # r1000.evento.infoContri.infoCadastro.contato.foneCel.valor = ''
    # r1000.evento.infoContri.infoCadastro.contato.email.valor = ''

    # r1000.evento.infoContri.infoCadastro.softHouse.cnpjSoftHouse = ''
    # r1000.evento.infoContri.infoCadastro.softHouse.nmRazao = ''
    # r1000.evento.infoContri.infoCadastro.softHouse.nmCont = ''
    # r1000.evento.infoContri.infoCadastro.softHouse.telefone = ''
    # r1000.evento.infoContri.infoCadastro.softHouse.email = ''

    # r1000.evento.infoContri.infoCadastro.infoEFR.ideEFR = ''
    # r1000.evento.infoContri.infoCadastro.infoEFR.cnpjEFR = ''

    data_hora = '20180529' \
                '130000'
    r1000.gera_id_evento(data_hora)

    processador = pysped.ProcessadorEFDReinf()
    processador.certificado.arquivo = '/home/wagner/Downloads/abgf.p12'
    processador.certificado.senha = '122017'  # ou "abgf@2016"

    processo = processador.enviar_lote([r1000])

    if processo.resposta.retornoLoteEventos.status.dadosRegistroOcorrenciaLote.ocorrencias:
        for ocorrencia in processo.resposta.retornoLoteEventos.status.dadosRegistroOcorrenciaLote.ocorrencias:
            print('Ocorrencia\n==========')
            print(ocorrencia.tipo.valor)
            print(ocorrencia.localizacaoErroAviso.valor)
            print(ocorrencia.codigo.valor)
            print(ocorrencia.descricao.valor)

    for evento in processo.resposta.retornoLoteEventos.retornoEventos.eventos:
        print("Evento ID %s" % evento.evtTotal.Id.valor)
        print("===================================")
        print(evento.evtTotal.ideRecRetorno.ideStatus.cdRetorno.valor)
        print(evento.evtTotal.ideRecRetorno.ideStatus.descRetorno.valor)

        if evento.evtTotal.ideRecRetorno.ideStatus.regOcorrs:
            for ocorrencia in evento.evtTotal.ideRecRetorno.ideStatus.regOcorrs:
                print("Ocorrência\n--------------")
                print(ocorrencia.tpOcorr.valor)
                print(ocorrencia.localErroAviso.valor)
                print(ocorrencia.codResp.valor)
                print(ocorrencia.dscResp.valor)

    # elif processo.resposta.retornoLoteEventos.retornoEventos.evento.evtTotal.evtTotal.ideRecRetorno.ideStatus.regOcorrs:
    #     for ocorrencia in processo.resposta.retornoLoteEventos.retornoEventos.evento.evtTotal.evtTotal.ideRecRetorno.ideStatus.regOcorrs:
    #         print('Ocorrência do Evento\n================')
    #         print(ocorrencia.tpOcorr.valor)
    #         print(ocorrencia.localErroAviso.valor)
    #         print(ocorrencia.codResp.valor)
    #         print(ocorrencia.dscResp.valor)
    #
    # else:
    #     print(processo.resposta.original)
    #     print("Registro processado com sucesso !")

