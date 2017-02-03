# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from ..constante_tributaria import (
    MODALIDADE_BASE_ICMS_ST,
    MODALIDADE_BASE_ICMS_ST_LISTA_NEGATIVA,
    MODALIDADE_BASE_ICMS_ST_LISTA_NEUTRA,
    MODALIDADE_BASE_ICMS_ST_LISTA_POSITIVA,
    MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO,
    MODALIDADE_BASE_ICMS_ST_PAUTA,
    MODALIDADE_BASE_ICMS_ST_PRECO_TABELADO_MAXIMO,
)


import logging
_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor import formata_valor

except (ImportError, IOError) as err:
    _logger.debug(err)


class AliquotaICMSST(models.Model):
    _description = u'Alíquota do ICMS ST'
    _inherit = 'sped.base'
    _name = 'sped.aliquota.icms.st'
    _rec_name = 'descricao'
    _order = 'al_icms, md_icms, pr_icms, rd_icms, rd_mva'

    al_icms = fields.Monetary(
        string=u'Alíquota',
        required=True,
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    md_icms = fields.Selection(
        selection=MODALIDADE_BASE_ICMS_ST,
        string=u'Modalidade da base de cálculo',
        required=True,
        default=MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO
    )
    pr_icms = fields.Float(
        string=u'Parâmetro da base de cálculo',
        required=True,
        digits=(18, 4),
        help=u'A margem de valor agregado, ou o valor da pauta/preço tabelado '
             u'máximo/lista, de acordo com o definido na modalidade da '
             u'base de cálculo.'
    )
    rd_icms = fields.Monetary(
        string=u'Percentual de redução da alíquota',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    rd_mva = fields.Monetary(
        string=u'Percentual de redução do MVA para o SIMPLES',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    descricao = fields.Char(
        string=u'Alíquota do ICMS ST',
        compute='_compute_descricao',
        store=False
    )

    @api.depends('al_icms', 'md_icms', 'pr_icms', 'rd_icms')
    def _compute_descricao(self):
        for al_icms in self:
            if al_icms.al_icms == -1:
                al_icms.descricao = u'Não tributado'
            else:
                al_icms.descricao = formata_valor(al_icms.al_icms or 0) + '%'

                if al_icms.md_icms == \
                        MODALIDADE_BASE_ICMS_ST_PRECO_TABELADO_MAXIMO:
                    al_icms.descricao += u', por preço máximo'
                elif al_icms.md_icms == MODALIDADE_BASE_ICMS_ST_LISTA_NEGATIVA:
                    al_icms.descricao += u', por lista negativa'
                elif al_icms.md_icms == MODALIDADE_BASE_ICMS_ST_LISTA_POSITIVA:
                    al_icms.descricao += u', por lista positiva'
                elif al_icms.md_icms == MODALIDADE_BASE_ICMS_ST_LISTA_NEUTRA:
                    al_icms.descricao += u', por lista neutra'
                elif al_icms.md_icms == \
                        MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO:
                    al_icms.descricao += u', por MVA'
                elif al_icms.md_icms == MODALIDADE_BASE_ICMS_ST_PAUTA:
                    al_icms.descricao += u', por pauta'

                if al_icms.pr_icms:
                    if al_icms.md_icms == \
                            MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO:
                        al_icms.descricao += u' de ' + \
                            formata_valor(al_icms.pr_icms,
                                          casas_decimais=4) + '%'
                    else:
                        al_icms.descricao += u' de R$ ' + \
                            formata_valor(al_icms.pr_icms, casas_decimais=4)

                if al_icms.rd_icms != 0:
                    al_icms.descricao += u', com redução de ' + \
                        formata_valor(al_icms.rd_icms) + '%'

                if al_icms.rd_mva != 0:
                    al_icms.descricao += u', com MVA reduzido em ' + \
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
                raise ValidationError(u'Alíquota de ICMS ST já existe!')
