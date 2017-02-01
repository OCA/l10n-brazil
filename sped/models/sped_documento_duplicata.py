# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp


class DocumentoDuplicata(models.Model):
    _description = 'Duplicata do Documento Fiscal'
    _inherit = 'sped.base'
    _name = 'sped.documento.duplicata'
    _order = 'documento_id, data_vencimento'
    # _rec_name = 'numero'

    documento_id = fields.Many2one('sped.documento', 'Documento', ondelete='cascade', required=True)
    numero = fields.Char('Número', size=60, required=True)
    data_vencimento = fields.Date('Data de vencimento', required=True)
    valor = fields.Monetary('Valor', digits=(18, 2), required=True)
