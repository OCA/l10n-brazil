# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from __future__ import division, print_function, unicode_literals

import logging
_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor import formata_valor

except (ImportError, IOError) as err:
    _logger.debug(err)

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from ..constante_tributaria import *


class AliquotaICMSST(models.Model):
    _description = 'Alíquota do ICMS ST'
    _name = 'sped.aliquota.icms.st'
    _rec_name = 'descricao'
    _order = 'al_icms, md_icms, pr_icms, rd_icms, rd_mva'

    al_icms = fields.Porcentagem('Alíquota', required=True)
    md_icms = fields.Selection(MODALIDADE_BASE_ICMS_ST, 'Modalidade da base de cálculo', required=True,
                               default=MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO)
    pr_icms = fields.Quantidade('Parâmetro da base de cálculo', required=True,
                                help='A margem de valor agregado, ou o valor da pauta/preço tabelado máximo/lista, '
                                     'de acordo com o definido na modalidade da base de cálculo.')
    rd_icms = fields.Porcentagem('Percentual de redução da alíquota')
    rd_mva = fields.Porcentagem('Percentual de redução do MVA para o SIMPLES')
    descricao = fields.Char(string='Alíquota do ICMS ST', compute='_compute_descricao', store=False)

    @api.depends('al_icms', 'md_icms', 'pr_icms', 'rd_icms')
    def _compute_descricao(self):
        if self.al_icms == -1:
            self.descricao = 'Não tributado'
        else:
            self.descricao = formata_valor(self.al_icms or 0) + '%'

            if self.md_icms == MODALIDADE_BASE_ICMS_ST_PRECO_TABELADO_MAXIMO:
                self.descricao += ', por preço máximo'
            elif self.md_icms == MODALIDADE_BASE_ICMS_ST_LISTA_NEGATIVA:
                self.descricao += ', por lista negativa'
            elif self.md_icms == MODALIDADE_BASE_ICMS_ST_LISTA_POSITIVA:
                self.descricao += ', por lista positiva'
            elif self.md_icms == MODALIDADE_BASE_ICMS_ST_LISTA_NEUTRA:
                self.descricao += ', por lista neutra'
            elif self.md_icms == MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO:
                self.descricao += ', por MVA'
            elif self.md_icms == MODALIDADE_BASE_ICMS_ST_PAUTA:
                self.descricao += ', por pauta'

            if self.pr_icms:
                if self.md_icms == MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO:
                    self.descricao += ' de ' + formata_valor(self.pr_icms, casas_decimais=4) + '%'
                else:
                    self.descricao += ' de R$ ' + formata_valor(self.pr_icms, casas_decimais=4)

            if self.rd_icms != 0:
                self.descricao += ', com redução de ' + formata_valor(self.rd_icms) + '%'

            if self.rd_mva != 0:
                self.descricao += ', com MVA reduzido em ' + formata_valor(self.rd_mva) + '% para o SIMPLES'

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
                raise ValidationError('Alíquota de ICMS ST já existe!')
