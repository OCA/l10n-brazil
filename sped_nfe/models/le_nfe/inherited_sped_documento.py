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

from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_base.constante_tributaria import *

_logger = logging.getLogger(__name__)

try:
    from pysped.nfe.webservices_flags import *
    from pysped.nfe.leiaute import *
    from pybrasil.base import mascara
    from pybrasil.inscricao import limpa_formatacao
    from pybrasil.data import (parse_datetime, UTC, data_hora_horario_brasilia,
                               agora)
    from email_validator import validate_email
    from pybrasil.telefone import valida_fone_fixo, valida_fone_celular
    from pybrasil.valor import formata_valor
    from pybrasil.valor.decimal import Decimal as D
    from pybrasil.template import TemplateBrasil

except (ImportError, IOError) as err:
    _logger.debug(err)

from ..versao_nfe_padrao import ClasseNFe, ClasseNFCe, ClasseProcNFe, \
    ClasseReboque


class SpedDocumento(models.Model):
    _inherit = 'sped.documento'

    def le_nfe(self, processador=None, xml=None):
        self.ensure_one()

        if self.modelo not in (MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE):
            return

        if xml is None:
            return

        if ' Id="NFe' not in xml:
            return

        partes = xml.split(' Id="NFe')

        chave = partes[1][:44]

        #
        # Verifica se a chave já existe
        #
        documento = self.search([('chave', '=', chave)])

        if len(documento) > 0:
            #documento.unlink()
            return documento

        dados = {
            'chave': chave,
            'importado_xml': True,
        }

        procNFe = ProcNFe_310()

        procNFe.xml = xml

        nfe = procNFe.NFe
        #chave = nfe.infNFe.Id.valor[3:]

        #
        # Identificação da NF-e
        #
        self._le_nfe_identificacao(nfe.infNFe.ide, dados)

        #
        # Verificamos se o emitente ou destinatário da NF é uma empresa do
        # sistema para poder importar o xml
        #
        dados_emitente = {}
        dados_destinatario = {}
        self._le_nfe_emitente(nfe.infNFe.emit, dados_emitente)
        self._le_nfe_destinatario(nfe.infNFe.dest, dados_destinatario)

        if not self._pode_importar_nfe(nfe.infNFe.ide, dados, dados_emitente,
                                   dados_destinatario):
            return

        '''
        #
        # Notas referenciadas
        #
        for doc_ref in self.documento_referenciado_ids:
            nfe.infNFe.ide.NFref.append(docref.monta_nfe())

        #
        # Endereço de entrega e retirada
        #
        self._le_nfe_endereco_retirada(nfe.infNFe.retirada)
        self._le_nfe_endereco_entrega(nfe.infNFe.entrega)
        '''
        #
        # Itens
        #
        dados['item_ids'] = [(5, False, {})]
        for det in nfe.infNFe.det:
            dados_item = self.env['sped.documento.item'].le_nfe(det, dados)
            dados['item_ids'].append((0, False, dados_item))

        #
        # Transporte e frete
        #
        self._le_nfe_transporte(nfe.infNFe.transp, dados)

        #
        # Duplicatas e pagamentos
        #
        self._le_nfe_cobranca(nfe.infNFe.cobr, dados)
        self._le_nfe_pagamentos(nfe.infNFe.pag, dados)

        #
        # Totais
        #
        self._le_nfe_total(nfe.infNFe.total, dados)

        #
        # Informações adicionais
        #
        dados['infcomplementar'] = \
            nfe.infNFe.infAdic.infCpl.valor.replace('| ', '\n').\
                replace('|', '\n')
        dados['infadfisco'] = \
            nfe.infNFe.infAdic.infAdFisco.valor.replace('| ', '\n').\
                replace('|', '\n')

        if not self.id:
            self = self.create(dados)
        else:
            self.update(dados)

        #
        # Se certifica de que todos os campos foram totalizados
        #
        self._compute_soma_itens()

        #
        # Informações sobre a autorização
        #
        protNFe = procNFe.protNFe
        if protNFe.infProt.cStat.valor in ('100', '150', '110', '301',
                                           '302'):
            #self.grava_xml(procNFe.NFe)
            procNFe.NFe.chave = chave
            self.grava_xml_autorizacao(procNFe)

            #if self.modelo == MODELO_FISCAL_NFE:
                #res = self.grava_pdf(nfe, procNFe.danfe_pdf)
            #elif self.modelo == MODELO_FISCAL_NFCE:
                #res = self.grava_pdf(nfe, procNFe.danfce_pdf)

            data_autorizacao = protNFe.infProt.dhRecbto.valor
            data_autorizacao = UTC.normalize(data_autorizacao)

            self.data_hora_autorizacao = data_autorizacao
            self.protocolo_autorizacao = protNFe.infProt.nProt.valor
            self.chave = protNFe.infProt.chNFe.valor

            if protNFe.infProt.cStat.valor in ('100', '150'):
                #self.executa_antes_autorizar()
                self.situacao_nfe = SITUACAO_NFE_AUTORIZADA
                #self.executa_depois_autorizar()
            else:
                #self.executa_antes_denegar()
                self.situacao_fiscal = SITUACAO_FISCAL_DENEGADO
                self.situacao_nfe = SITUACAO_NFE_DENEGADA
                #self.executa_depois_denegar()

        return self

    def _pode_importar_nfe(self, ide, dados, dados_emitente, dados_destinatario):
        self.ensure_one()

        pode_importar = False

        dados['regime_tributario'] = dados_emitente['regime_tributario']

        #
        # Primeiro, localizamos o CNPJ ou CPF do emitente e do destinatário
        #
        cnpj_cpf = dados_emitente['cnpj_cpf']
        emitente = self.env['sped.participante'].search(
            [('cnpj_cpf_numero', '=', cnpj_cpf)])

        #
        # Se existe o emitente, e é uma empresa do sistema, *deve* ser uma
        # nota própria (cuidado para o caso de emissão de NF de uma empresa
        # para outra dentro do *mesmo banco*, ver mais abaixo
        #
        if len(emitente) > 0:
            emitente = emitente[0]
            pode_importar = pode_importar or emitente.eh_empresa

        #
        # Agora, buscamos o destinatário
        #
        cnpj_cpf = dados_destinatario['cnpj_cpf']
        destinatario = self.env['sped.participante'].search(
            [('cnpj_cpf_numero', '=', cnpj_cpf)])

        if len(destinatario) > 0:
            destinatario = destinatario[0]
            pode_importar = pode_importar or destinatario.eh_empresa

        #
        # Aqui já sabemos se ou o destinatário, ou o emitente, é uma empresa
        # do sistema, caso em que podemos importar a nota; nesse caso, se
        # o destinatário ou emitente não existirem no cadastro de
        # participantes, já podemos criar o registro
        #
        if not pode_importar:
            return False

        if not emitente:
            emitente = self.env['sped.participante'].create(dados_emitente)

        if not destinatario:
            destinatario = \
                self.env['sped.participante'].create(dados_destinatario)

        #
        # Aqui agora tratamos o caso de o emitente e o destinatário serem
        # empresas do sistema; para saber se a nota vai ser importada como
        # emitida ou recebida, usamos o CNPJ da empresa que está tratando a
        # nota
        #
        if emitente.eh_empresa:
            dados['regime_tributario'] = emitente.regime_tributario

            #
            # O destinatário também é uma empresa do sistema, nesse caso,
            # verificamos se a importação vai ser feita como sendo de
            # emissão própria ou de terceiros; nesse caso, checamos a empresa
            # que está importando a NF
            #
            if destinatario.eh_empresa and \
                emitente.cnpj_cpf != self.empresa_id.cnpj_cpf:
                dados['empresa_id'] = self.empresa_id.id
                dados['participante_id'] = emitente.id
                dados['emissao'] = TIPO_EMISSAO_TERCEIROS

                if dados['entrada_saida'] == ENTRADA_SAIDA_ENTRADA:
                    dados['entrada_saida'] = ENTRADA_SAIDA_SAIDA
                else:
                    dados['entrada_saida'] = ENTRADA_SAIDA_ENTRADA

                #dados['data_hora_entrada_saida'] = False
                emitente.eh_fornecedor = True

            #
            # É nota própria
            #
            else:
                cnpj = dados_emitente['cnpj_cpf']

                cnpj = cnpj[:2] + '.' + \
                       cnpj[2:5] + '.' + \
                       cnpj[5:8] + '/' + \
                       cnpj[8:12] + '-' + \
                       cnpj[12:14]

                empresa_id = self.env['sped.empresa']. \
                    search([('cnpj_cpf', '=', cnpj)])

                if(empresa_id):
                    dados['empresa_id'] = empresa_id.id

                dados['participante_id'] = destinatario.id
                dados['regime_tributario'] = emitente.regime_tributario

                if dados['entrada_saida'] == ENTRADA_SAIDA_SAIDA:
                    destinatario.eh_cliente = True
                else:
                    destinatario.eh_fornecedor = True

        #
        # É nota de terceiros
        #
        else:
            cnpj = dados_destinatario['cnpj_cpf']

            cnpj = cnpj[:2] + '.' + \
                   cnpj[2:5] + '.' + \
                   cnpj[5:8] + '/' + \
                   cnpj[8:12] + '-' + \
                   cnpj[12:14]

            empresa_id = self.env['sped.empresa']. \
                search([('cnpj_cpf', '=', cnpj)])

            if (empresa_id):
                dados['empresa_id'] = empresa_id.id

            dados['participante_id'] = emitente.id
            dados['emissao'] = TIPO_EMISSAO_TERCEIROS

            if dados['entrada_saida'] == ENTRADA_SAIDA_ENTRADA:
                dados['entrada_saida'] = ENTRADA_SAIDA_SAIDA
            else:
                dados['entrada_saida'] = ENTRADA_SAIDA_ENTRADA

            #dados['data_hora_entrada_saida'] = False
            emitente.eh_fornecedor = True

        #
        # Natureza da operação só pode ser importada no caso de emissão própria
        #
        if dados['emissao'] == TIPO_EMISSAO_PROPRIA:
            natureza = \
                self._busca_natureza_operacao(ide.natOp.valor)

            if not natureza:
                naturezas = self.search([(1, '=', 1)], order='id desc', limit=1)

                if naturezas:
                    ultima_natureza = naturezas[0].id
                else:
                    ultima_natureza = 0

                natureza = self.env['sped.natureza.operacao'].create({
                    'nome': ide.natOp.valor,
                    'codigo': str(ultima_natureza + 1).zfill(3),
                })

            dados['natureza_operacao_id'] = natureza.id
            dados['operacao_id'] = self._busca_operacao(natureza)

        return True

    def _busca_municipio(self, codigo_ibge):
        municipio = self.env['sped.municipio'].search(
            [('codigo_ibge', '=', codigo_ibge)]
            )

        if len(municipio) == 0:
            return False

        return municipio[0].id

    def _busca_natureza_operacao(self, natureza):
        natureza_operacao = self.env['sped.natureza.operacao'].search(
            [('nome_unico', '=', natureza.lower().replace(' ', ' '))]
            )

        if len(natureza_operacao) == 0:
            return False

        return natureza_operacao[0]

    def _busca_operacao(self, natureza):
        operacao = self.env['sped.operacao'].search(
            [('natureza_operacao_id', '=', natureza.id)]
            )

        if len(operacao) == 0:
            return False

        return operacao[0].id

    def _le_nfe_identificacao(self, ide, dados):
        dados.update({
            'ambiente_nfe': str(ide.tpAmb.valor),
            'ind_forma_pagamento': str(ide.indPag.valor),
            'serie': ide.serie.valor,
            'numero': ide.nNF.valor,
            'data_hora_emissao': str(UTC.normalize(ide.dhEmi.valor)),
            'tipo_emissao_nfe': str(ide.tpEmis.valor),
            'finalidade_nfe': str(ide.finNFe.valor),
            'presenca_comprador': str(ide.indPres.valor),
            'modelo': str(ide.mod.valor),
            'consumidor_final': ide.indFinal.valor,

            'emissao': TIPO_EMISSAO_PROPRIA,
            'entrada_saida': str(ide.tpNF.valor),
        })

        if ide.dhSaiEnt.valor:
            dados['data_hora_entrada_saida'] = \
                str(UTC.normalize(ide.dhSaiEnt.valor))
        else:
            dados['data_hora_entrada_saida'] = dados['data_hora_emissao']

        if ide.cMunFG.valor:
            dados['municipio_fato_gerador_id'] = self._busca_municipio(
                str(ide.cMunFG.valor) + '0000')

        #
        # Trata o problema da emissão vir sem horário (meia-noite), mas a
        # saída ser no meio da tarde do próprio dia
        #
        if '00:00:00' in dados['data_hora_emissao'] and \
            '00:00:00' not in dados['data_hora_entrada_saida']:
            if dados['data_hora_emissao'][:10] == \
                dados['data_hora_entrada_saida'][:10]:
                dados['data_hora_emissao'] = dados['data_hora_entrada_saida']

    def _le_nfe_emitente(self, emit, dados):
        dados.update({
            'cnpj_cpf': emit.CNPJ.valor,
            'nome': emit.xNome.valor,
            'razao_social': emit.xNome.valor,
            'fantasia': emit.xFant.valor,
            'endereco': emit.enderEmit.xLgr.valor,
            'numero': emit.enderEmit.nro.valor,
            'complemento': emit.enderEmit.xCpl.valor,
            'bairro': emit.enderEmit.xBairro.valor,
            'cep': emit.enderEmit.CEP.valor,
            'ie': emit.IE.valor,
            'contribuinte': INDICADOR_IE_DESTINATARIO_CONTRIBUINTE,
            'regime_tributario': str(emit.CRT.valor),
        })

        if emit.enderEmit.fone.valor:
            if valida_fone_fixo(str(emit.enderEmit.fone.valor)):
                dados['fone'] = str(emit.enderEmit.fone.valor)
            elif valida_fone_celular(str(emit.enderEmit.fone.valor)):
                dados['celular'] = str(emit.enderEmit.fone.valor)

        codigo_ibge = str(emit.enderEmit.cMun.valor) + '0000'
        dados['municipio_id'] = self._busca_municipio(codigo_ibge)

        #
        # Trata o caso do código do cliente na frente da razão social
        #
        partes = emit.xNome.valor.split('-')
        if len(partes) > 1:
            codigo = partes[0].strip()

            if codigo.isdigit():
                dados['codigo'] = codigo
                dados['razao_social'] = ''.join(partes[1:]).strip()
                dados['nome'] = '-'.join(partes[1:]).strip()

    def _le_nfe_destinatario(self, dest, dados):
        dados.update({
            'nome': dest.xNome.valor,
            'razao_social': dest.xNome.valor,
            'endereco': dest.enderDest.xLgr.valor,
            'numero': dest.enderDest.nro.valor,
            'complemento': dest.enderDest.xCpl.valor,
            'bairro': dest.enderDest.xBairro.valor,
            'cep': dest.enderDest.CEP.valor,
            'ie': dest.IE.valor,
            'contribuinte': dest.indIEDest.valor,
        })

        if dest.enderDest.fone.valor:
            if valida_fone_fixo(str(dest.enderDest.fone.valor)):
                dados['fone'] = str(dest.enderDest.fone.valor)
            elif valida_fone_celular(str(dest.enderDest.fone.valor)):
                dados['celular'] = str(dest.enderDest.fone.valor)

        if dest.email.valor:
            try:
                valido = validate_email(dest.email.valor)
                dados['email'] = dest.email.valor.lower()
                dados['email_nfe'] = dest.email.valor.lower()
            except:
                pass

        #
        # Tratamos o erro no preenchimento da NF-e em que estão enviando
        # a IE mas o indIEDest está vindo como Não contribuinte ou Isento
        #
        if dados['ie']:
            dados['contribuinte'] = INDICADOR_IE_DESTINATARIO_CONTRIBUINTE

        if dest.idEstrangeiro.valor:
            if not dest.idEstrangeiro.valor.startswith('EX'):
                dados['cnpj_cpf'] = 'EX' + dest.idEstrangeiro.valor
            else:
                dados['cnpj_cpf'] = dest.idEstrangeiro.valor

        elif dest.CNPJ.valor:
            dados['cnpj_cpf'] = dest.CNPJ.valor

        elif dest.CPF.valor:
            dados['cnpj_cpf'] = dest.CPF.valor

        codigo_ibge = ''
        if dest.enderDest.cMun.valor == '9999999' or \
            str(dest.enderDest.cPais.valor) != PAIS_BRASIL:
            codigo_ibge = '9999999' + str(dest.enderDest.cPais.valor)
            dados['cep'] = '99999999'
            dados['contribuinte'] = INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE

        elif dest.enderDest.cMun.valor:
            codigo_ibge = str(dest.enderDest.cMun.valor) + '0000'

        if codigo_ibge:
            dados['municipio_id'] = self._busca_municipio(codigo_ibge)

        #
        # Trata o caso do código do cliente na frente da razão social
        #
        partes = dest.xNome.valor.split('-')
        if len(partes) > 1:
            codigo = partes[0].strip()

            if codigo.isdigit():
                dados['codigo'] = codigo
                dados['razao_social'] = ''.join(partes[1:]).strip()
                dados['nome'] = '-'.join(partes[1:]).strip()

    def _le_nfe_endereco_retirada(self, retirada):
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

    def _le_nfe_endereco_entrega(self, entrega):
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

    def _le_nfe_transporte(self, transp, dados):
        if self.modelo != MODELO_FISCAL_NFE:
            return

        if transp.modFrete.valor == MODALIDADE_FRETE_REMETENTE_CIF:
            dados['modalidade_frete'] = MODALIDADE_FRETE_REMETENTE_PROPRIO
        elif transp.modFrete.valor == MODALIDADE_FRETE_DESTINATARIO_FOB:
            dados['modalidade_frete'] = MODALIDADE_FRETE_DESTINATARIO_PROPRIO
        else:
            dados['modalidade_frete'] = str(transp.modFrete.valor)

        dados_transportadora = {}

        #
        # Como a transportadora da NF-e não é um cadastro de participante
        # completo, evitamos fazer a importação caso ela já não esteja
        # cadastrada no sistema
        #
        cnpj_cpf = None
        if transp.transporta.CPF.valor:
            cnpj_cpf = transp.transporta.CPF.valor
        elif transp.transporta.CNPJ.valor:
            cnpj_cpf = transp.transporta.CNPJ.valor

        if cnpj_cpf is not None:
            transportadora = self.env['sped.participante'].search(
                [('cnpj_cpf_numero', '=', cnpj_cpf)])
            if len(transportadora) > 0:
                dados['transportadora_id'] = transportadora[0].id

        '''
        if transp.transporta.xNome.valor:
            dados_transportadora['nome'] = transp.transporta.xNome.valor
            dados_transportadora['razao_social'] = \
                transp.transporta.xNome.valor

        if transp.transporta.IE.valor:
            dados_transportadora['contribuinte'] = \
                INDICADOR_IE_DESTINATARIO_CONTRIBUINTE
            dados_transportadora['ie'] = transp.transporta.IE.valor
        else:
            dados_transportadora['contribuinte'] = \
                INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE

        if transp.transporta.xEnder.valor:
            dados_transportadora['endereco'] = transp.transporta.xEnder.valor
            dados_transportadora['numero'] = 's/nº'
            dados_transportadora['bairro'] = 'Centro'

        if transp.transpora.xMun.valor and

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
        for volume in self.volume_ids:
            transp.vol.append(volume.monta_nfe())
        '''

    def _le_nfe_cobranca(self, cobr, dados):
        if self.modelo != MODELO_FISCAL_NFE:
            return

        dados['duplicata_ids'] = [(5, False, {})]
        for dup in cobr.dup:
            dados_duplicata = {
                'numero': str(dup.nDup.valor),
                'data_vencimento': str(dup.dVenc.valor),
                'valor': dup.vDup.valor,
            }

            dados['duplicata_ids'].append([0, False, dados_duplicata])

    def _le_nfe_pagamentos(self, pag, dados):
        if self.modelo != MODELO_FISCAL_NFCE:
            return

        dados['pagamento_ids'] = [(5, False, {})]
        for pagamento in pag:
            dados_pagamento = {
                'forma_pagamento': str(pagamento.tPag.valor),
                'valor': pagamento.vPag.valor,
                'troco': pagamento.vTroco.valor,
                'cnpj_cpf': pagamento.card.CNPJ.valor,
                'bandeira_cartao': str(pagamento.card.tBand.valor),
                'integracao_cartao': str(pagamento.card.cAut.valor),
            }
            dados['pagamento_ids'].append([0, False, dados_pagamento])

    def _le_nfe_total(self, total, dados):
        dados.update({
            'bc_icms_proprio': total.ICMSTot.vBC.valor,
            'vr_icms_proprio': total.ICMSTot.vICMS.valor,
            'vr_icms_desonerado': total.ICMSTot.vICMSDeson.valor,
            'vr_fcp': total.ICMSTot.vFCPUFDest.valor,
            'vr_icms_estado_destino': total.ICMSTot.vICMSUFDest.valor,
            'vr_icms_estado_origem': total.ICMSTot.vICMSUFRemet.valor,
            'bc_icms_st': total.ICMSTot.vBCST.valor,
            'vr_icms_st': total.ICMSTot.vST.valor,
            'vr_produtos': total.ICMSTot.vProd.valor,
            'vr_frete': total.ICMSTot.vFrete.valor,
            'vr_seguro': total.ICMSTot.vSeg.valor,
            'vr_desconto': total.ICMSTot.vDesc.valor,
            'vr_ii': total.ICMSTot.vII.valor,
            'vr_ipi': total.ICMSTot.vIPI.valor,
            'vr_pis_proprio': total.ICMSTot.vPIS.valor,
            'vr_cofins_proprio': total.ICMSTot.vCOFINS.valor,
            'vr_outras': total.ICMSTot.vOutro.valor,
            'vr_nf': total.ICMSTot.vNF.valor,
            'vr_ibpt': total.ICMSTot.vTotTrib.valor,
        })

    def testa_importacao(self):
        #processador = self.processador_nfe()

        #caminho_a_processar = '/home/ari/diso/novembro/'
        #caminho_processado = '/home/ari/diso/importado/'
        #caminho_rejeitado = '/home/ari/diso/rejeitado/'

        caminho_a_processar = '/home/ari/zenir/'

        arquivos = os.listdir(caminho_a_processar)
        arquivos.sort()

        chaves = []
        chave_repetida = 0

        i = 1
        for nome_arq in arquivos:
            print(i, len(arquivos), nome_arq)
            i += 1
            if '.xml' not in nome_arq.lower():
                continue

            #
            # Codificação incorreta, arquivo não é UTF-8
            #
            try:
                xml = open(caminho_a_processar + nome_arq, 'r').read().decode('utf-8')
            except:
                print('erro codificacao', nome_arq)
                continue

            #
            # Não é do ambiente de produção
            #
            if not '<tpAmb>1</tpAmb>' in xml:
                print('erro ambiente', nome_arq)
                continue

            #
            # Não é versão 3.10 ou 4.00
            #
            if not 'versao="3.10"' in xml and not 'versao="4.00"' in xml:
                print('erro versao', nome_arq)
                continue

            #
            # Não é uma NF-e nem CT-e
            #
            if (not '</NFe>' in xml) and \
                (not '</cancNFe>' in xml) and \
                (not '<descEvento>Cancelamento</descEvento>' in xml) and \
                (not '</CTe>' in xml) and \
                (not '</cancCTe>' in xml):
                print('erro tipo', nome_arq)
                continue

            ##
            ## A assinatura é válida?
            ##
            #if '</NFe>' in xml or '</CTe>' in xml:
                #try:
                    #processador.certificado.verifica_assinatura_xml(xml)
                #except:
                    #continue

            #
            # É NF-e?
            #
            if '</nfeProc>' in xml:

                if ' Id="NFe' not in xml:
                    print('sem chave', nome_arq)
                    continue
                partes = xml.split(' Id="NFe')

                chave = partes[1][:44]

                if chave not in chaves:
                    chaves.append(chave)
                else:
                    chave_repetida += 1
                    print(chave_repetida, chave, len(chaves))

                print('vai importar')
                documento = self.env['sped.documento'].new()
                documento.modelo = '55'
                documento.empresa_id = \
                    self.env.user.company_id.sped_empresa_id.id
                d = documento.le_nfe(xml=xml)
                self.env.cr.commit()

            else:
                print('erro nao eh nfe', nome_arq)
