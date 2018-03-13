# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import os
import logging
import base64
from io import BytesIO
from builtins import str

from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_base.constante_tributaria import *

_logger = logging.getLogger(__name__)

from ..versao_nfe_padrao import ClasseVol

try:
    from pysped.nfe.webservices_flags import *
    from pysped.nfe.leiaute import *
    from pybrasil.inscricao import limpa_formatacao
    from pybrasil.data import (parse_datetime, UTC, data_hora_horario_brasilia,
                               agora)
    from pybrasil.valor import formata_valor
    from pybrasil.valor.decimal import Decimal as D
    from pysped.nfe.leiaute import Pag_400, DetPag_400

except (ImportError, IOError) as err:
    _logger.debug(err)

from ..versao_nfe_padrao import ClasseNFe, ClasseNFCe, ClasseProcNFe, \
    ClasseReboque


class SpedDocumento(models.Model):
    _inherit = 'sped.documento'

    def monta_nfe(self, processador=None):
        self.ensure_one()

        if self.modelo == MODELO_FISCAL_NFE:
            nfe = ClasseNFe()
        elif self.modelo == MODELO_FISCAL_NFCE:
            nfe = ClasseNFCe()
        else:
            return

        #
        # Identificação da NF-e
        #
        self._monta_nfe_identificacao(nfe.infNFe.ide)

        #
        # Notas referenciadas
        #
        for doc_ref in self.documento_referenciado_ids:
            nfe.infNFe.ide.NFref.append(doc_ref.monta_nfe())

        #
        # Emitente
        #
        self._monta_nfe_emitente(nfe.infNFe.emit)

        #
        # Destinatário
        #
        self._monta_nfe_destinatario(nfe.infNFe.dest)

        #
        # Endereço de entrega e retirada
        #
        self._monta_nfe_endereco_retirada(nfe.infNFe.retirada)
        self._monta_nfe_endereco_entrega(nfe.infNFe.entrega)

        #
        # Itens
        #
        i = 1
        for item in self.item_ids:
            nfe.infNFe.det.append(item.monta_nfe(i, nfe))
            i += 1

        #
        # Transporte e frete
        #
        self._monta_nfe_transporte(nfe.infNFe.transp)

        #
        # Duplicatas e pagamentos
        #
        if self.condicao_pagamento_id.forma_pagamento == '14':
            self._monta_nfe_cobranca(nfe.infNFe.cobr)
        self._monta_nfe_pagamentos(nfe.infNFe.pag)

        #
        # Totais
        #
        self._monta_nfe_total(nfe)

        #
        # Informações adicionais
        #
        nfe.infNFe.infAdic.infCpl.valor = \
            self._monta_nfe_informacao_complementar(nfe)
        nfe.infNFe.infAdic.infAdFisco.valor = \
            self._monta_nfe_informacao_fisco()

        nfe.gera_nova_chave()
        nfe.monta_chave()

        if self.empresa_id.certificado_id:
            certificado = self.empresa_id.certificado_id.certificado_nfe()
            certificado.assina_xmlnfe(nfe)

        return nfe

    def _monta_nfe_identificacao(self, ide):
        empresa = self.empresa_id
        participante = self.participante_id

        ide.tpAmb.valor = int(self.ambiente_nfe)
        ide.tpNF.valor = int(self.entrada_saida)
        ide.cUF.valor = UF_CODIGO[empresa.estado]
        ide.natOp.valor = self.natureza_operacao_id.nome
        ide.indPag.valor = int(self.ind_forma_pagamento)
        ide.serie.valor = self.serie
        ide.nNF.valor = str(D(self.numero).quantize(D('1')))

        #
        # Tratamento das datas de UTC para o horário de brasília
        #
        ide.dhEmi.valor = data_hora_horario_brasilia(
            parse_datetime(self.data_hora_emissao + ' GMT')
        )
        ide.dEmi.valor = ide.dhEmi.valor

        if self.data_hora_entrada_saida:
            ide.dhSaiEnt.valor = data_hora_horario_brasilia(
                parse_datetime(self.data_hora_entrada_saida + ' GMT')
            )
        else:
            ide.dhSaiEnt.valor = data_hora_horario_brasilia(
                parse_datetime(self.data_hora_emissao + ' GMT')
            )

        ide.dSaiEnt.valor = ide.dhSaiEnt.valor
        ide.hSaiEnt.valor = ide.dhSaiEnt.valor

        ide.cMunFG.valor = empresa.municipio_id.codigo_ibge[:7]
        # ide.tpImp.valor = 1  # DANFE em retrato
        ide.tpEmis.valor = self.tipo_emissao_nfe
        ide.finNFe.valor = self.finalidade_nfe
        ide.procEmi.valor = 0  # Emissão por aplicativo próprio
        ide.verProc.valor = 'Odoo ERP'
        ide.indPres.valor = self.presenca_comprador

        #
        # NFC-e é sempre emissão para dentro do estado
        # e sempre para consumidor final
        #
        if self.modelo == MODELO_FISCAL_NFCE:
            ide.idDest.valor = IDENTIFICACAO_DESTINO_INTERNO
            ide.indFinal.valor = TIPO_CONSUMIDOR_FINAL_CONSUMIDOR_FINAL

        else:
            if participante.estado == 'EX':
                ide.idDest.valor = IDENTIFICACAO_DESTINO_EXTERIOR
            elif participante.estado == empresa.estado:
                ide.idDest.valor = IDENTIFICACAO_DESTINO_INTERNO
            else:
                ide.idDest.valor = IDENTIFICACAO_DESTINO_INTERESTADUAL

            if (self.consumidor_final) or (
                        participante.contribuinte ==
                        INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE):
                ide.indFinal.valor = TIPO_CONSUMIDOR_FINAL_CONSUMIDOR_FINAL

    def _monta_nfe_emitente(self, emit):
        empresa = self.empresa_id

        emit.CNPJ.valor = limpa_formatacao(empresa.cnpj_cpf)
        emit.xNome.valor = empresa.razao_social
        emit.xFant.valor = empresa.fantasia or ''
        emit.enderEmit.xLgr.valor = empresa.endereco
        emit.enderEmit.nro.valor = empresa.numero
        emit.enderEmit.xCpl.valor = empresa.complemento or ''
        emit.enderEmit.xBairro.valor = empresa.bairro
        emit.enderEmit.cMun.valor = empresa.municipio_id.codigo_ibge[:7]
        emit.enderEmit.xMun.valor = empresa.cidade
        emit.enderEmit.UF.valor = empresa.estado
        emit.enderEmit.CEP.valor = limpa_formatacao(empresa.cep)
        # emit.enderEmit.cPais.valor = '1058'
        # emit.enderEmit.xPais.valor = 'Brasil'
        emit.enderEmit.fone.valor = limpa_formatacao(empresa.fone or '')
        emit.IE.valor = limpa_formatacao(empresa.ie or '')
        #
        # Usa o regime tributário da NF e não da empresa, e trata o código
        # interno 3.1 para o lucro real, que na NF deve ir somente 3
        #
        emit.CRT.valor = self.regime_tributario[0]

        if self.modelo == MODELO_FISCAL_NFCE:
            emit.csc.id = empresa.csc_id or 1
            emit.csc.codigo = empresa.csc_codigo or ''
            # emit.csc.codigo = emit.csc.codigo.strip()

    def _monta_nfe_destinatario(self, dest):
        participante = self.participante_id

        #
        # Para a NFC-e, o destinatário é sempre não contribuinte
        #
        if self.modelo == MODELO_FISCAL_NFCE:
            dest.indIEDest.valor = INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE

        else:
            dest.indIEDest.valor = participante.contribuinte

            if participante.contribuinte == \
                    INDICADOR_IE_DESTINATARIO_CONTRIBUINTE:
                dest.IE.valor = limpa_formatacao(participante.ie or '')

        #
        # Trata a possibilidade de ausência do destinatário na NFC-e
        #
        if self.modelo == MODELO_FISCAL_NFCE and not participante.cnpj_cpf:
            return

        #
        # Participantes estrangeiros tem a ID de estrangeiro sempre começando
        # com EX
        #
        if participante.cnpj_cpf.startswith('EX'):
            dest.idEstrangeiro.valor = \
                limpa_formatacao(participante.cnpj_cpf or '')

        elif len(participante.cnpj_cpf or '') == 14:
            dest.CPF.valor = limpa_formatacao(participante.cnpj_cpf)

        elif len(participante.cnpj_cpf or '') == 18:
            dest.CNPJ.valor = limpa_formatacao(participante.cnpj_cpf)

        #if self.ambiente_nfe == AMBIENTE_NFE_HOMOLOGACAO:
            #dest.xNome.valor = 'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - ' \
                               #'SEM VALOR FISCAL'
        #else:
        dest.xNome.valor = participante.razao_social or ''

        #
        # Para a NFC-e, o endereço do participante pode não ter sido
        # preenchido
        #
        dest.enderDest.xLgr.valor = participante.endereco or ''
        dest.enderDest.nro.valor = participante.numero or ''
        dest.enderDest.xCpl.valor = participante.complemento or ''
        dest.enderDest.xBairro.valor = participante.bairro or ''

        if not participante.cnpj_cpf.startswith('EX'):
            dest.enderDest.CEP.valor = limpa_formatacao(participante.cep)
        else:
            dest.enderDest.CEP.valor = '99999999'

        #
        # Pode haver cadastro de participante sem município para NFC-e
        #
        if participante.municipio_id:
            dest.enderDest.cMun.valor = \
                participante.municipio_id.codigo_ibge[:7]
            dest.enderDest.xMun.valor = participante.cidade
            dest.enderDest.UF.valor = participante.estado

            if participante.cnpj_cpf.startswith('EX'):
                dest.enderDest.cPais.valor = \
                    participante.municipio_id.pais_id.codigo_bacen
                dest.enderDest.xPais.valor = \
                    participante.municipio_id.pais_id.nome

        dest.enderDest.fone.valor = limpa_formatacao(participante.fone or '')
        email_dest = participante.email_nfe or ''
        dest.email.valor = email_dest[:60]

    def _monta_nfe_endereco_retirada(self, retirada):
        return
        if not self.endereco_retirada_id:
            return

        retirada.xLgr.valor = self.endereco_retirada_id.endereco or ''
        retirada.nro.valor = self.endereco_retirada_id.numero or ''
        retirada.xCpl.valor = self.endereco_retirada_id.complemento or ''
        retirada.xBairro.valor = self.endereco_retirada_id.bairro or ''
        retirada.cMun.valor = \
            self.endereco_retirada_id.municipio_id.codigo_ibge[:7]
        retirada.xMun.valor = self.endereco_retirada_id.municipio_id.nome
        retirada.UF.valor = self.endereco_retirada_id.municipio_id.estado_id.uf

        if self.endereco_retirada_id.cpf:
            if len(self.endereco_retirada_id.cpf) == 18:
                retirada.CNPJ.valor = \
                    limpa_formatacao(self.endereco_retirada_id.cpf)
            else:
                retirada.CPF.valor = \
                    limpa_formatacao(self.endereco_retirada_id.cpf)

    def _monta_nfe_endereco_entrega(self, entrega):
        return
        if not self.endereco_entrega_id:
            return

        entrega.xLgr.valor = self.endereco_entrega_id.endereco or ''
        entrega.nro.valor = self.endereco_entrega_id.numero or ''
        entrega.xCpl.valor = self.endereco_entrega_id.complemento or ''
        entrega.xBairro.valor = self.endereco_entrega_id.bairro or ''
        entrega.cMun.valor = \
            self.endereco_entrega_id.municipio_id.codigo_ibge[:7]
        entrega.xMun.valor = self.endereco_entrega_id.municipio_id.nome
        entrega.UF.valor = self.endereco_entrega_id.municipio_id.estado_id.uf

        if self.endereco_entrega_id.cnpj_cpf:
            if len(self.endereco_entrega_id.cnpj_cpf) == 18:
                entrega.CNPJ.valor = \
                    limpa_formatacao(self.endereco_entrega_id.cnpj_cpf)
            else:
                entrega.CPF.valor = \
                    limpa_formatacao(self.endereco_entrega_id.cnpj_cpf)

    def _monta_nfe_transporte(self, transp):
        if self.modelo != MODELO_FISCAL_NFE:
            return
        #
        # Temporário até o início da NF-e 4.00
        #
        if self.modalidade_frete == MODALIDADE_FRETE_REMETENTE_PROPRIO:
            transp.modFrete.valor = MODALIDADE_FRETE_REMETENTE_CIF
        elif self.modalidade_frete == MODALIDADE_FRETE_DESTINATARIO_PROPRIO:
            transp.modFrete.valor = MODALIDADE_FRETE_DESTINATARIO_FOB
        else:
            transp.modFrete.valor = \
                self.modalidade_frete or MODALIDADE_FRETE_SEM_FRETE

        if self.transportadora_id:
            if len(self.transportadora_id.cnpj_cpf) == 14:
                transp.transporta.CPF.valor = \
                    limpa_formatacao(self.transportadora_id.cnpj_cpf)
            else:
                transp.transporta.CNPJ.valor = \
                    limpa_formatacao(self.transportadora_id.cnpj_cpf)

            transp.transporta.xNome.valor = \
                self.transportadora_id.razao_social or ''
            transp.transporta.IE.valor = \
                limpa_formatacao(self.transportadora_id.ie or 'ISENTO')
            ender = self.transportadora_id.endereco or ''
            ender += ' '
            ender += self.transportadora_id.numero or ''
            ender += ' '
            ender += self.transportadora_id.complemento or ''
            transp.transporta.xEnder.valor = ender.strip()
            transp.transporta.xMun.valor = self.transportadora_id.cidade or ''
            transp.transporta.UF.valor = self.transportadora_id.estado or ''

        if self.veiculo_id:
            transp.veicTransp.placa.valor = self.veiculo_id.placa or ''
            transp.veicTransp.UF.valor = self.veiculo_id.estado_id.uf or ''
            transp.veicTransp.RNTC.valor = self.veiculo_id.rntrc or ''

        transp.reboque = []
        if self.reboque_1_id:
            reb = ClasseReboque()
            reb.placa.valor = self.reboque_1_id.placa or ''
            reb.UF.valor = self.reboque_1_id.estado_id.uf or ''
            reb.RNTC.valor = self.reboque_1_id.rntrc or ''
            transp.reboque.append(reb)
        if self.reboque_2_id:
            reb = ClasseReboque()
            reb.placa.valor = self.reboque_2_id.placa or ''
            reb.UF.valor = self.reboque_2_id.estado_id.uf or ''
            reb.RNTC.valor = self.reboque_2_id.rntrc or ''
            transp.reboque.append(reb)
        if self.reboque_3_id:
            reb = ClasseReboque()
            reb.placa.valor = self.reboque_3_id.placa or ''
            reb.UF.valor = self.reboque_3_id.estado_id.uf or ''
            reb.RNTC.valor = self.reboque_3_id.rntrc or ''
            transp.reboque.append(reb)
        if self.reboque_4_id:
            reb = ClasseReboque()
            reb.placa.valor = self.reboque_4_id.placa or ''
            reb.UF.valor = self.reboque_4_id.estado_id.uf or ''
            reb.RNTC.valor = self.reboque_4_id.rntrc or ''
            transp.reboque.append(reb)
        if self.reboque_5_id:
            reb = ClasseReboque()
            reb.placa.valor = self.reboque_5_id.placa or ''
            reb.UF.valor = self.reboque_5_id.estado_id.uf or ''
            reb.RNTC.valor = self.reboque_5_id.rntrc or ''
            transp.reboque.append(reb)

        #
        # Volumes
        #
        transp.vol = []
        if len(self.volume_ids) == 0:
            vol = ClasseVol()

            vol.qVol.valor = str(D(1))
            vol.esp.valor = ''
            vol.marca.valor = ''
            vol.nVol.valor = ''
            vol.pesoL.valor = str(
                D(self.peso_liquido or 0).quantize(D('0.001')))
            vol.pesoB.valor = str(D(self.peso_bruto or 0).quantize(D('0.001')))

            transp.vol.append(vol)
        else:
            for volume in self.volume_ids:
                transp.vol.append(volume.monta_nfe())

    def _monta_nfe_cobranca(self, cobr):
        if self.modelo != MODELO_FISCAL_NFE:
            return

        if self.ind_forma_pagamento not in \
                (IND_FORMA_PAGAMENTO_A_VISTA, IND_FORMA_PAGAMENTO_A_PRAZO):
            return
        cobr.fat.nFat.valor = formata_valor(self.numero, casas_decimais=0)
        cobr.fat.vOrig.valor = str(D(self.vr_operacao))
        cobr.fat.vDesc.valor = str(D(self.vr_desconto))
        cobr.fat.vLiq.valor = str(D(self.vr_fatura))

        for duplicata in self.duplicata_ids:
            cobr.dup.append(duplicata.monta_nfe())

    def _monta_pagamento(self, pag):
        self.ensure_one()

        if self.modelo != MODELO_FISCAL_NFE and \
                self.modelo != MODELO_FISCAL_NFCE:
            return

        detPag = DetPag_400()
        detPag.tPag.valor = self.condicao_pagamento_id.forma_pagamento
        detPag.vPag.valor = str(D(self.vr_fatura))
        # Troco somente na NF-e 4.00
        pag.vTroco.valor = str(D(self.vr_troco))

        if self.condicao_pagamento_id.forma_pagamento in FORMA_PAGAMENTO_CARTOES:
            detPag.card.CNPJ.valor = limpa_formatacao(
                self.condicao_pagamento_id.participante_id.cnpj_cpf or '')
            detPag.card.tBand.valor = self.condicao_pagamento_id.bandeira_cartao
            detPag.card.cAut.valor = self.condicao_pagamento_id.integracao_cartao
            detPag.card.tpIntegra.valor = self.condicao_pagamento_id.integracao_cartao

        pag.detPag.append(detPag)

        return pag

    def _monta_nfe_pagamentos(self, pag):
        if self.modelo not in [MODELO_FISCAL_NFCE, MODELO_FISCAL_NFE]:
            return

        if self.modelo == MODELO_FISCAL_NFE:
            self._monta_pagamento(pag)
        else:
            for pagamento in self.pagamento_ids:
                pag.append(pagamento.monta_nfe())

    def _monta_nfe_total(self, nfe):
        nfe.infNFe.total.ICMSTot.vBC.valor = str(D(self.bc_icms_proprio))
        nfe.infNFe.total.ICMSTot.vICMS.valor = str(D(self.vr_icms_proprio))
        nfe.infNFe.total.ICMSTot.vICMSDeson.valor = str(D(self.vr_icms_desonerado))
        nfe.infNFe.total.ICMSTot.vFCPUFDest.valor = str(D(self.vr_fcp))
        if nfe.infNFe.ide.idDest.valor == \
            IDENTIFICACAO_DESTINO_INTERESTADUAL and \
            nfe.infNFe.ide.indFinal.valor == \
            TIPO_CONSUMIDOR_FINAL_CONSUMIDOR_FINAL and \
            nfe.infNFe.dest.indIEDest.valor == \
            INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE:

            nfe.infNFe.total.ICMSTot.vICMSUFDest.valor = str(D(self.vr_icms_estado_destino))
            nfe.infNFe.total.ICMSTot.vICMSUFRemet.valor = str(D(self.vr_icms_estado_origem))

        nfe.infNFe.total.ICMSTot.vBCST.valor = str(D(self.bc_icms_st))
        nfe.infNFe.total.ICMSTot.vST.valor = str(D(self.vr_icms_st))
        nfe.infNFe.total.ICMSTot.vProd.valor = str(D(self.vr_produtos))
        nfe.infNFe.total.ICMSTot.vFrete.valor = str(D(self.vr_frete))
        nfe.infNFe.total.ICMSTot.vSeg.valor = str(D(self.vr_seguro))
        nfe.infNFe.total.ICMSTot.vDesc.valor = str(D(self.vr_desconto))
        nfe.infNFe.total.ICMSTot.vII.valor = str(D(self.vr_ii))
        nfe.infNFe.total.ICMSTot.vIPI.valor = str(D(self.vr_ipi))
        nfe.infNFe.total.ICMSTot.vPIS.valor = str(D(self.vr_pis_proprio))
        nfe.infNFe.total.ICMSTot.vCOFINS.valor = str(D(self.vr_cofins_proprio))
        nfe.infNFe.total.ICMSTot.vOutro.valor = str(D(self.vr_outras))
        nfe.infNFe.total.ICMSTot.vNF.valor = str(D(self.vr_nf))
        nfe.infNFe.total.ICMSTot.vTotTrib.valor = str(D(self.vr_ibpt))

    def _monta_nfe_informacao_complementar(self, nfe):
        infcomplementar = self.infcomplementar or ''

        dados_infcomplementar = {
            'nf': self,
        }

        #
        # Crédito de ICMS do SIMPLES
        #
        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES and \
                self.vr_icms_sn:
            if len(infcomplementar) > 0:
                infcomplementar += '\n'

            infcomplementar += \
                'Permite o aproveitamento de crédito de ' + \
                'ICMS no valor de R$ ${formata_valor(nf.vr_icms_sn)},' + \
                ' nos termos do art. 23 da LC 123/2006;'

        #
        # Valor do IBPT
        #
        if self.vr_ibpt:
            if len(infcomplementar) > 0:
                infcomplementar += '\n'

            infcomplementar += 'Valor aproximado dos tributos: ' + \
                               'R$ ${formata_valor(nf.vr_ibpt)} - fonte: IBPT;'

        #
        # ICMS para UF de destino
        #
        if nfe.infNFe.ide.idDest.valor == \
                IDENTIFICACAO_DESTINO_INTERESTADUAL and \
                nfe.infNFe.ide.indFinal.valor == \
                TIPO_CONSUMIDOR_FINAL_CONSUMIDOR_FINAL and \
                nfe.infNFe.dest.indIEDest.valor == \
                INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE:

            if len(infcomplementar) > 0:
                infcomplementar += '\n'

            infcomplementar += \
                'Partilha do ICMS de R$ ' + \
                '${formata_valor(nf.vr_icms_proprio)}% recolhida ' + \
                'conf. EC 87/2015: ' + \
                'R$ ${formata_valor(nf.vr_icms_estado_destino)} para o ' + \
                'estado de ${nf.participante_id.estado} e ' + \
                'R$ ${formata_valor(nf.vr_icms_estado_origem)} para o ' + \
                'estado de ${nf.empresa_id.estado}; Valor do diferencial ' + \
                'de alíquota: ' + \
                'R$ ${formata_valor(nf.vr_difal)};'

            if self.vr_fcp:
                infcomplementar += ' Fundo de combate à pobreza: R$ ' + \
                                   '${formata_valor(nf.vr_fcp)}'

        #
        # Aplica um template na observação
        #
        return self._renderizar_informacoes_template(
            dados_infcomplementar, infcomplementar)

    def _monta_nfe_informacao_fisco(self):
        infadfisco = self.infadfisco or ''

        dados_infadfisco = {
            'nf': self,
        }

        #
        # Aplica um template na observação
        #
        return self._renderizar_informacoes_template(
            dados_infadfisco, infadfisco)
