# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE
#   Wagner Pereira <wagner.pereira@kmee.com.br>
# Copyright 2018 ABGF - Wagner Pereira <wagner.pereira@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import fields, models


class TipoLotacaoClassificacao(models.Model):
    _name = "sped.lotacao_classificacao"
    _description = 'Compatibilidade entre Tipos de Lotação' \
                   ' e Classificação Tributária'

    name = fields.Char(string='Class. Tributária')
    classificacao_tributaria_ids = fields.Many2many(
        'sped.lotacao_tributaria', string='Tipos de Lotação Tributária',
        relation='classificacao_tributaria_codigo_ids'
    )
