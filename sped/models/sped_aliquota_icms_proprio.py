# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.addons.l10n_br_base.constante_tributaria import (
    MODALIDADE_BASE_ICMS_PROPRIO,
    MODALIDADE_BASE_ICMS_PROPRIO_MARGEM_VALOR_AGREGADO,
    MODALIDADE_BASE_ICMS_PROPRIO_PAUTA,
    MODALIDADE_BASE_ICMS_PROPRIO_PRECO_TABELADO_MAXIMO,
    MODALIDADE_BASE_ICMS_PROPRIO_VALOR_OPERACAO,
)

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor import formata_valor

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedAliquotaICMSProprio(models.Model):
    _name = b'sped.aliquota.icms.proprio'
    _description = 'Alíquotas do ICMS próprio'
    _inherit = 'sped.base'
    _rec_name = 'descricao'
    _order = 'al_icms, md_icms, pr_icms, rd_icms'

    al_icms = fields.Monetary(
        string='Alíquota',
        required=True,
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    md_icms = fields.Selection(
        selection=MODALIDADE_BASE_ICMS_PROPRIO,
        string='Modalidade da base de cálculo',
        required=True,
        default=MODALIDADE_BASE_ICMS_PROPRIO_VALOR_OPERACAO
    )
    pr_icms = fields.Float(
        string='Parâmetro da base de cálculo',
        digits=(18, 4),
        help='A margem de valor agregado, ou o valor da pauta/preço tabelado '
             'máximo, de acordo com o definido na modalidade da base de '
             'cálculo.',
    )
    rd_icms = fields.Monetary(
        string='Percentual de redução da alíquota',
        digits=(5, 2),
        currency_field='currency_aliquota_id'
    )
    importado = fields.Boolean(
        string='Padrão para produtos importados?',
        default=False
    )
    descricao = fields.Char(
        string='Alíquota do ICMS próprio',
        compute='_compute_descricao',
        store=False
    )

    @api.depends('al_icms', 'md_icms', 'pr_icms', 'rd_icms', 'importado')
    def _compute_descricao(self):
        for al_icms in self:
            if al_icms.al_icms == -1:
                al_icms.descricao = 'Não tributado'
            else:
                al_icms.descricao = formata_valor(al_icms.al_icms or 0) + '%'

                if (al_icms.md_icms !=
                        MODALIDADE_BASE_ICMS_PROPRIO_VALOR_OPERACAO):
                    if al_icms.md_icms == \
                            MODALIDADE_BASE_ICMS_PROPRIO_MARGEM_VALOR_AGREGADO:
                        al_icms.descricao += ', por MVA de ' + \
                            formata_valor(al_icms.pr_icms,
                                          casas_decimais=4) + '%'
                    elif al_icms.md_icms == MODALIDADE_BASE_ICMS_PROPRIO_PAUTA:
                        al_icms.descricao += ', por pauta de R$ ' + \
                            formata_valor(al_icms.pr_icms, casas_decimais=4)
                    elif al_icms.md_icms == \
                            MODALIDADE_BASE_ICMS_PROPRIO_PRECO_TABELADO_MAXIMO:
                        al_icms.descricao += ', por preço máximo de R$ ' + \
                                             formata_valor(
                                                 al_icms.pr_icms,
                                                 casas_decimais=4)

                if al_icms.rd_icms != 0:
                    al_icms.descricao += ', com redução de ' + \
                        formata_valor(al_icms.rd_icms) + '%'

                if al_icms.importado:
                    al_icms.descricao += ' (padrão para importados)'

    @api.depends('al_icms', 'md_icms', 'pr_icms', 'rd_icms')
    def _check_al_icms(self):
        for al_icms in self:
            busca = [
                ('al_icms', '=', al_icms.al_icms),
                ('md_icms', '=', al_icms.md_icms),
                ('pr_icms', '=', al_icms.pr_icms),
                ('rd_icms', '=', al_icms.rd_icms),
            ]

            if al_icms.id or al_icms._origin.id:
                busca.append(('id', '!=', al_icms.id or al_icms._origin.id))

            al_icms_ids = self.search(busca)

            if al_icms_ids:
                raise ValidationError('Alíquota de ICMS já existe!')
