# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from mdfelib.v3_00 import mdfe as mdfe3
from odoo.addons.l10n_br_base.constante_tributaria import (
    MODELO_FISCAL,
    SITUACAO_NFE,
    MODELO_FISCAL_CTE,
    MODELO_FISCAL_NFE,
    MODALIDADE_TRANSPORTE_AQUAVIARIO,
)


class L10nBrMdfeItem(models.Model):
    _inherit = 'l10n_br.mdfe.item'

    def monta_mdfe(self):
        inf_mun_descarga = []

        cidades_descarga = self.mapped('destinatario_cidade_id')

        for cidade in cidades_descarga:
            doc = self.filtered(lambda d: d.destinatario_cidade_id == cidade)

            lista_nfe = []
            lista_cte = []

            for nfe in doc.filtered(
                    lambda f: f.documento_id.modelo in MODELO_FISCAL_NFE):
                lista_nfe.append(
                    mdfe3.infNFeType(
                        chNFe=nfe.documento_chave,
                        # SegCodBarra=None,
                        # indReentrega=None,
                        # infUnidTransp=None,
                        # peri=None,
                    )
                )

            for cte in doc.filtered(
                    lambda f: f.documento_id.modelo in MODELO_FISCAL_CTE):
                lista_cte.append(
                    mdfe3.infCTeType(
                        chNFe=cte.documento_chave,
                        # SegCodBarra=None,
                        # indReentrega=None,
                        # infUnidTransp=None,
                        # peri=None,
                    )
                )
            #
            # Somente aquaviario
            #
            inf_mdfe_transporte = None

            if (doc.mdfe_id.modalidade_transporte ==
                    MODALIDADE_TRANSPORTE_AQUAVIARIO):
                raise NotImplementedError

            inf_mun_descarga.append(mdfe3.infMunDescargaType(
                cMunDescarga=cidade.codigo_ibge[:7],
                xMunDescarga=cidade.nome,
                infCTe=lista_cte,
                infNFe=lista_nfe,
                infMDFeTransp=inf_mdfe_transporte,
            ))

        return inf_mun_descarga
