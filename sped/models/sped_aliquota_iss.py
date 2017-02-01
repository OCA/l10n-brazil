# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import fields, models
import odoo.addons.decimal_precision as dp


class AliquotaISS(models.Model):
    _description = 'Alíquota do ISS'
    _inherit = 'sped.base'
    _name = 'sped.aliquota.iss'
    _rec_name = 'al_iss'
    _order = 'servico_id, municipio_id, al_iss'

    servico_id = fields.Many2one('sped.servico', 'Serviço', ondelete='cascade', required=True)
    municipio_id = fields.Many2one('sped.municipio', 'Município', ondelete='restrict', required=True)
    al_iss = fields.Monetary('Alíquota', required=True, digits=(5, 2), currency_field='currency_aliquota_id')
    codigo = fields.Char('Código específico', size=10)
