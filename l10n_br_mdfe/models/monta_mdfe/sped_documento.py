# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

#from __future__ import division, print_function, unicode_literals

import sys
import logging
from mdfelib.v3_00 import mdfe as mdfe3
from mdfelib.v3_00 import mdfeModalRodoviario as rodo3

_logger = logging.getLogger(__name__)

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import (
    MODELO_FISCAL_MDFE,
    TIPO_TRANSPORTADOR,
    MODALIDADE_TRANSPORTE,
    TIPO_EMITENTE,
    TIPO_RODADO,
    TIPO_CARROCERIA,
    AMBIENTE_MDFE_PRODUCAO,
    TIPO_EMISSAO_MDFE_NORMAL,
    TIPO_EMISSAO_MDFE_CONTINGENCIA,
)

try:
    from pysped.nfe.webservices_flags import *
    from pysped.nfe.leiaute import *
    from pybrasil.inscricao import limpa_formatacao
    from pybrasil.data import (parse_datetime, UTC, data_hora_horario_brasilia,
                               agora)
    from pybrasil.valor import formata_valor
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedDocumento(models.Model):
    _inherit = 'sped.documento'

    def monta_mdfe(self, processador=None):
        self.ensure_one()

        ender_emit = mdfe3.TEndeEmi(
            xLgr=self.empresa_id.endereco,
            nro=self.empresa_id.numero,
            xBairro=self.empresa_id.bairro,
            cMun=self.empresa_id.municipio_id.codigo_ibge[:7],
            xMun=self.empresa_id.municipio_id.nome,
            CEP=self.empresa_id.cep,
            UF=self.empresa_id.estado,
            fone=self.empresa_id.fone or '',
            xCpl=self.empresa_id.complemento or ''
        )

        emit = mdfe3.emitType(
            CNPJ=self.empresa_id.cnpj_cpf_numero,
            IE=self.empresa_id.participante_id.ie,
            xNome=self.empresa_id.participante_id.razao_social,
            xFant=self.empresa_id.participante_id.fantasia,
            enderEmit=ender_emit
        )

        carregamento_1 = mdfe3.infMunCarregaType(
            # FIXME: pegar do carregamento_ids
            cMunCarrega=self.empresa_id.participante_id.municipio_id.codigo_ibge[:7],
            xMunCarrega=self.empresa_id.cidade
        )

        ide = mdfe3.ideType(
            cUF=self.empresa_id.estado,
            tpAmb=self.ambiente_nfe,
            tpEmit=self.tipo_emitente,
            tpTransp=self.tipo_transportador or '',
            mod=self.modelo,
            serie=self.serie,
            nMDF=str(int(self.numero)),
            cMDF=str(int(self.numero)),
            cDV=self.chave[-1:] if self.chave else '',
            modal=self.operacao_id.modalidade_transporte,
            dhEmi=self.data_hora_emissao,
            tpEmis=self.emissao,
            procEmi='0',
            verProc='Odoo',
            UFIni=self.empresa_id.estado,
            UFFim=self.descarregamento_estado_id,
            infMunCarrega=[carregamento_1], #todo: funcao lambda para municipios de carregamento
            infPercurso=None, # todo: gerar lista
            dhIniViagem=self.data_hora_entrada_saida,
            indCanalVerde=None,
        )


        #todo: for para adicionar `as listas
        lista_cte = []
        lista_nfe = []

        nfe_1 = mdfe3.infNFeType(
            chNFe='23180341426966004836558720000002681197872700',
            SegCodBarra=None,
            indReentrega=None,
            infUnidTransp=None,
            peri=None,
        )

        nfe_2 = mdfe3.infNFeType(
            chNFe='23180341426966003600558720000012321410321707',
            SegCodBarra=None,
            indReentrega=None,
            infUnidTransp=None,
            peri=None,
        )

        lista_nfe.append(nfe_1)
        lista_nfe.append(nfe_2)

        infMunDescarga = mdfe3.infMunDescargaType(
            cMunDescarga='2305506', #todo: lista com todos os codigos IBGE Municipios de Descarga
            xMunDescarga='Cidade', #todo: lista com todos os nomes dos Municipios de Descarga
            infCTe=lista_cte,
            infNFe=lista_nfe,
            infMDFeTransp=None, #somente aquaviario
        )

        tot = mdfe3.totType(
            qCTe=None, #todo: quantidade de CTe's de lista_cte
            qNFe='2', #todo: quantidade de NFe's de lista_nfe
            qMDFe=None,
            vCarga='3044.00', #todo: soma do valor das NFe's
            cUnid='01', # 01-KG, 02-TON
            qCarga='57.0000', #todo: Peso Bruto Total
        )


        infDoc = mdfe3.infDocType(infMunDescarga=[infMunDescarga])

        condutor_1 = rodo3.condutorType(
            xNome=self.condutor_ids[0].condutor_id.name,
            CPF=''.join(d for d in self.condutor_ids[0].condutor_id.cnpj_cpf if d.isdigit())
        )

        veiculo = rodo3.veicTracaoType(
            cInt='0001',
            placa=self.veiculo_placa,
            RENAVAM=None,
            tara=self.veiculo_tara_kg or '',
            capKG=self.veiculo_capacidade_kg or '',
            capM3=self.veiculo_capacidade_m3 or '',
            prop=None,
            condutor=condutor_1,
            tpRod=self.veiculo_tipo_rodado or '',
            tpCar=str(int(self.veiculo_tipo_carroceria)).zfill(2) or '00',
            UF=self.veiculo_estado_id.uf
        )

        rodo = rodo3.rodo(
            infANTT=None,
            veicTracao=None,
            veicReboque=None,
            codAgPorto=None,
            lacRodo=None
        )

        modal = mdfe3.infModalType(versaoModal="3.00", anytypeobjs_=rodo)

        mdfe = mdfe3.infMDFeType(
            versao="3.00", Id=None, ide=ide, emit=emit, infModal=modal,
            infDoc=infDoc, seg=None, tot=tot, lacres=None, autXML=None,
            infAdic=None
        )

        return mdfe.export(sys.stdout, 0)
