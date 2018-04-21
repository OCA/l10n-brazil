# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# from __future__ import division, print_function, unicode_literals

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

    def _prepara_ender_emtit(self):
        return mdfe3.TEndeEmi(
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

    def _prepara_emit(self):
        return mdfe3.emitType(
            CNPJ=self.empresa_id.cnpj_cpf_numero,
            IE=self.empresa_id.participante_id.ie,
            xNome=self.empresa_id.participante_id.razao_social,
            xFant=self.empresa_id.participante_id.fantasia,
            enderEmit=self._prepara_ender_emtit()
        )

    def _prepara_ide(self):
        inf_municipio_caregamento = []
        inf_percurso = []

        for municipio in self.carregamento_municipio_ids:
            inf_municipio_caregamento.append(
                mdfe3.infMunCarregaType(
                    cMunCarrega=municipio.codigo_ibge[:7],
                    xMunCarrega=municipio.nome,
                )
            )

        for percurso in self.percurso_estado_ids:
            inf_percurso.append(
                mdfe3.infPercursoType(
                    UFPer=percurso.uf
                )
            )

        return mdfe3.ideType(
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
            UFFim=self.descarregamento_estado_id.uf,
            infMunCarrega=inf_municipio_caregamento,
            infPercurso=inf_percurso,
            dhIniViagem=self.data_hora_entrada_saida,
            dhIniViagem=self.data_hora_entrada_saida,
            indCanalVerde=None,
        )

    def _prepara_tot(self):
        return mdfe3.totType(
            qCTe=None,  # todo: quantidade de CTe's de lista_cte
            qNFe='2',  # todo: quantidade de NFe's de lista_nfe
            qMDFe=None,
            vCarga='3044.00',  # todo: soma do valor das NFe's
            cUnid='01',  # 01-KG, 02-TON
            qCarga='57.0000',  # todo: Peso Bruto Total
        )

    def _prepara_modal(self):
        veiculo = rodo3.veicTracaoType(
            cInt='0001',
            placa=self.veiculo_placa,
            RENAVAM=None,
            tara=str("%.2f" % self.veiculo_tara_kg),
            capKG=str("%.2f" % self.veiculo_capacidade_kg),
            capM3=str("%.2f" % self.veiculo_capacidade_m3),
            prop=None,
            condutor=self.condutor_ids.monta_mdfe(),
            tpRod=self.veiculo_tipo_rodado or '',
            tpCar=str(int(self.veiculo_tipo_carroceria)).zfill(2) or '00',
            UF=self.veiculo_estado_id.uf or '',
        )

        rodo = rodo3.rodo(
            infANTT=None,
            veicTracao=veiculo,
            veicReboque=None,
            codAgPorto=None,
            lacRodo=None
        )

        return mdfe3.infModalType(versaoModal="3.00", anytypeobjs_=rodo)

    def _prepara_inf_doc(self):

        inf_mun_descarga = self.item_mdfe_ids.monta_mdfe()
        return mdfe3.infDocType(
            infMunDescarga=inf_mun_descarga
        )

    def monta_mdfe(self, processador=None):
        self.ensure_one()

        mdfe = mdfe3.infMDFeType(
            versao="3.00",
            # Id=None,
            ide=self._prepara_ide(),
            emit=self._prepara_emit(),
            infModal=self._prepara_modal(),
            infDoc=self._prepara_inf_doc(),
            seg=self.seguro_ids.monta_mdfe(),
            tot=self._prepara_tot(),
            lacres=self.lacre_ids.monta_mdfe(),
            # autXML=None,
            infAdic=None
        )

        return mdfe.export(sys.stdout, 0)
