# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from ..constante_tributaria import (
    MODALIDADE_BASE_IPI,
    MODALIDADE_BASE_IPI_ALIQUOTA,
    MODALIDADE_BASE_IPI_QUANTIDADE,
    ST_IPI_ENTRADA,
    ST_IPI_ENTRADA_RECUPERACAO_CREDITO,
    ST_IPI_SAIDA,
    ST_IPI_SAIDA_TRIBUTADA,
)

import logging
_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor import formata_valor

except (ImportError, IOError) as err:
    _logger.debug(err)


class AliquotaIPI(models.Model):
    _description = u'Alíquota do IPI'
    _inherit = 'sped.base'
    _name = 'sped.aliquota.ipi'
    _rec_name = 'descricao'
    _order = 'al_ipi'

    al_ipi = fields.Monetary(
        string=u'Alíquota',
        required=True,
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    md_ipi = fields.Selection(
        selection=MODALIDADE_BASE_IPI,
        string='Modalidade da base de cálculo',
        required=True,
        default=MODALIDADE_BASE_IPI_ALIQUOTA,
    )
    cst_ipi_entrada = fields.Selection(
        selection=ST_IPI_ENTRADA,
        string=u'Situação tributária nas entradas',
        required=True,
        default=ST_IPI_ENTRADA_RECUPERACAO_CREDITO,
    )
    cst_ipi_saida = fields.Selection(
        selection=ST_IPI_SAIDA,
        string=u'Situação tributária do nas saídas',
        required=True,
        default=ST_IPI_SAIDA_TRIBUTADA,
    )
    descricao = fields.Char(
        string=u'Alíquota do IPI',
        compute='_compute_descricao',
        store=True,
    )

    @api.depends('al_ipi', 'md_ipi', 'cst_ipi_entrada', 'cst_ipi_saida')
    def _compute_descricao(self):
        for al_ipi in self:
            if al_ipi.al_ipi == -1:
                al_ipi.descricao = u'Não tributado'

            else:
                if al_ipi.md_ipi == MODALIDADE_BASE_IPI_ALIQUOTA:
                    al_ipi.descricao = formata_valor(al_ipi.al_ipi or 0) + '%'

                elif al_ipi.md_ipi == MODALIDADE_BASE_IPI_QUANTIDADE:
                    al_ipi.descricao = u'por quantidade, a R$ ' + \
                        formata_valor(al_ipi.al_ipi or 0)

                al_ipi.descricao += u' - CST ' + al_ipi.cst_ipi_entrada
                al_ipi.descricao += u' entrada, ' + al_ipi.cst_ipi_saida
                al_ipi.descricao += u' saída'

    @api.depends('al_ipi', 'md_ipi')
    def _check_al_ipi(self):
        for al_ipi in self:
            busca = [
                ('al_ipi', '=', al_ipi.al_ipi),
                ('md_ipi', '=', al_ipi.md_ipi),
            ]

            if al_ipi.id or al_ipi._origin.id:
                busca.append(('id', '!=', al_ipi.id or al_ipi._origin.id))

            al_ipi_ids = self.search(busca)

            if al_ipi_ids:
                raise ValidationError(u'Alíquota de IPI já existe!')
