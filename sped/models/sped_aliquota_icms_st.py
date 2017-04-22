# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.addons.l10n_br_base.constante_tributaria import (
    MODALIDADE_BASE_ICMS_ST,
    MODALIDADE_BASE_ICMS_ST_LISTA_NEGATIVA,
    MODALIDADE_BASE_ICMS_ST_LISTA_NEUTRA,
    MODALIDADE_BASE_ICMS_ST_LISTA_POSITIVA,
    MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO,
    MODALIDADE_BASE_ICMS_ST_PAUTA,
    MODALIDADE_BASE_ICMS_ST_PRECO_TABELADO_MAXIMO,
)

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor import formata_valor

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedAliquotaICMSST(models.Model):
    _name = b'sped.aliquota.icms.st'
    _description = 'Alíquotas do ICMS ST'
    _inherit = 'sped.base'
    _rec_name = 'descricao'
    _order = 'al_icms, md_icms, pr_icms, rd_icms, rd_mva'

    al_icms = fields.Monetary(
        string='Alíquota',
        required=True,
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    md_icms = fields.Selection(
        selection=MODALIDADE_BASE_ICMS_ST,
        string='Modalidade da base de cálculo',
        required=True,
        default=MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO
    )
    pr_icms = fields.Float(
        string='Parâmetro da base de cálculo',
        required=True,
        digits=(18, 4),
        help='A margem de valor agregado, ou o valor da pauta/preço tabelado '
             'máximo/lista, de acordo com o definido na modalidade da '
             'base de cálculo.'
    )
    rd_icms = fields.Monetary(
        string='Percentual de redução da alíquota',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    rd_mva = fields.Monetary(
        string='Percentual de redução do MVA para o SIMPLES',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    descricao = fields.Char(
        string='Alíquota do ICMS ST',
        compute='_compute_descricao',
        store=False
    )

    @api.depends('al_icms', 'md_icms', 'pr_icms', 'rd_icms')
    def _compute_descricao(self):
        for al_icms in self:
            if al_icms.al_icms == -1:
                al_icms.descricao = 'Não tributado'
            else:
                al_icms.descricao = formata_valor(al_icms.al_icms or 0) + '%'

                if al_icms.md_icms == \
                        MODALIDADE_BASE_ICMS_ST_PRECO_TABELADO_MAXIMO:
                    al_icms.descricao += ', por preço máximo'
                elif al_icms.md_icms == MODALIDADE_BASE_ICMS_ST_LISTA_NEGATIVA:
                    al_icms.descricao += ', por lista negativa'
                elif al_icms.md_icms == MODALIDADE_BASE_ICMS_ST_LISTA_POSITIVA:
                    al_icms.descricao += ', por lista positiva'
                elif al_icms.md_icms == MODALIDADE_BASE_ICMS_ST_LISTA_NEUTRA:
                    al_icms.descricao += ', por lista neutra'
                elif al_icms.md_icms == \
                        MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO:
                    al_icms.descricao += ', por MVA'
                elif al_icms.md_icms == MODALIDADE_BASE_ICMS_ST_PAUTA:
                    al_icms.descricao += ', por pauta'

                if al_icms.pr_icms:
                    if al_icms.md_icms == \
                            MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO:
                        al_icms.descricao += ' de ' + \
                            formata_valor(al_icms.pr_icms,
                                          casas_decimais=4) + '%'
                    else:
                        al_icms.descricao += ' de R$ ' + \
                            formata_valor(al_icms.pr_icms, casas_decimais=4)

                if al_icms.rd_icms != 0:
                    al_icms.descricao += ', com redução de ' + \
                        formata_valor(al_icms.rd_icms) + '%'

                if al_icms.rd_mva != 0:
                    al_icms.descricao += ', com MVA reduzido em ' + \
                        formata_valor(al_icms.rd_mva) + '% para o SIMPLES'

    @api.depends('al_icms', 'md_icms', 'pr_icms', 'rd_icms', 'rd_mva')
    def _check_al_icms(self):
        for al_icms in self:
            busca = [
                ('al_icms', '=', al_icms.al_icms),
                ('md_icms', '=', al_icms.md_icms),
                ('pr_icms', '=', al_icms.pr_icms),
                ('rd_icms', '=', al_icms.rd_icms),
                ('rd_mva', '=', al_icms.rd_mva),
            ]

            if al_icms.id or al_icms._origin.id:
                busca.append(('id', '!=', al_icms.id or al_icms._origin.id))

            al_icms_ids = self.search(busca)

            if al_icms_ids:
                raise ValidationError(_(u'Alíquota de ICMS ST já existe!'))
