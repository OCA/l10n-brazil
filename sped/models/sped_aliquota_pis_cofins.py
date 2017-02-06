# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from ..constante_tributaria import (
    MODALIDADE_BASE_PIS,
    MODALIDADE_BASE_PIS_ALIQUOTA,
    MODALIDADE_BASE_PIS_QUANTIDADE,
    ST_PIS_CRED_EXCL_TRIB_MERC_INTERNO,
    ST_PIS_ENTRADA,
    ST_PIS_SAIDA,
    ST_PIS_TRIB_NORMAL,
)

import logging
_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor import formata_valor

except (ImportError, IOError) as err:
    _logger.debug(err)


class AliquotaPISCOFINS(models.Model):
    _description = u'Alíquota do PIS-COFINS'
    _inherit = 'sped.base'
    _name = 'sped.aliquota.pis.cofins'
    _rec_name = 'descricao'
    _order = 'al_pis, al_cofins'

    al_pis = fields.Monetary(
        string=u'Alíquota do PIS',
        required=True,
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    al_cofins = fields.Monetary(
        string=u'Alíquota da COFINS',
        required=True,
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    md_pis_cofins = fields.Selection(
        selection=MODALIDADE_BASE_PIS,
        string=u'Modalidade da base de cálculo',
        required=True,
        default=MODALIDADE_BASE_PIS_ALIQUOTA,
    )
    cst_pis_cofins_entrada = fields.Selection(
        selection=ST_PIS_ENTRADA,
        string=u'Situação tributária nas entradas',
        required=True,
        default=ST_PIS_CRED_EXCL_TRIB_MERC_INTERNO,
    )
    cst_pis_cofins_saida = fields.Selection(
        selection=ST_PIS_SAIDA,
        string=u'Situação tributária nas saída',
        required=True,
        default=ST_PIS_TRIB_NORMAL,
    )
    codigo_justificativa = fields.Char(
        string=u'Código da justificativa',
        size=10,
    )
    descricao = fields.Char(
        string=u'Alíquota do PIS-COFINS',
        compute='_compute_descricao',
        store=True,
    )

    @api.depends('al_pis', 'al_cofins', 'md_pis_cofins',
                 'cst_pis_cofins_entrada', 'cst_pis_cofins_saida',
                 'codigo_justificativa')
    def _compute_descricao(self):
        for al_pis_cofins in self:
            if al_pis_cofins.al_pis == -1:
                al_pis_cofins.descricao = u'Não tributado'
            else:
                if al_pis_cofins.md_pis_cofins == MODALIDADE_BASE_PIS_ALIQUOTA:
                    al_pis_cofins.descricao = u'PIS ' + \
                        formata_valor(al_pis_cofins.al_pis or 0) + '%'
                    al_pis_cofins.descricao += u'; COFINS ' + \
                        formata_valor(al_pis_cofins.al_cofins or 0) + '%'

                elif (al_pis_cofins.md_pis_cofins ==
                      MODALIDADE_BASE_PIS_QUANTIDADE):
                    al_pis_cofins.descricao = (
                        u'por quantidade, PIS a R$ ' +
                        formata_valor(al_pis_cofins.al_pis)
                    )
                    al_pis_cofins.descricao += (
                        u'; COFINS a R$ ' +
                        formata_valor(al_pis_cofins.al_cofins)
                    )

                al_pis_cofins.descricao += (
                    u' - CST ' + al_pis_cofins.cst_pis_cofins_entrada)
                al_pis_cofins.descricao += (
                    u' entrada, ' + al_pis_cofins.cst_pis_cofins_saida)
                al_pis_cofins.descricao += u' saída'

                if al_pis_cofins.codigo_justificativa:
                    al_pis_cofins.descricao += u' - justificativa '
                    al_pis_cofins.descricao += (
                        al_pis_cofins.codigo_justificativa
                    )

    @api.depends('al_pis', 'al_cofins', 'md_pis_cofins',
                 'cst_pis_cofins_entrada', 'cst_pis_cofins_saida',
                 'codigo_justificativa')
    def _check_al_pis(self):
        for al_pis_cofins in self:
            busca = [
                ('al_pis', '=', al_pis_cofins.al_pis),
                ('al_cofins', '=', al_pis_cofins.al_cofins),
                ('md_pis_cofins', '=', al_pis_cofins.md_pis_cofins),
                ('cst_pis_cofins_entrada', '=',
                 al_pis_cofins.cst_pis_cofins_entrada),
                ('cst_pis_cofins_saida', '=',
                 al_pis_cofins.cst_pis_cofins_saida),
                ('codigo_justificativa', '=',
                 al_pis_cofins.codigo_justificativa),
            ]

            if al_pis_cofins.id or al_pis_cofins._origin.id:
                busca.append(
                    ('id', '!=', al_pis_cofins.id or al_pis_cofins._origin.id))

            al_pis_cofins_ids = self.search(busca)

            if al_pis_cofins_ids:
                raise ValidationError(u'Alíquotas de PIS e COFINS já existem!')
