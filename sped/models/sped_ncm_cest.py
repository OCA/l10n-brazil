# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class NCMCEST(models.Model):
    _description = 'NCM - CEST'
    _name = 'sped.ncm.cest.carrega'

    ncm_id = fields.Many2one('sped.ncm', 'NCM')
    cest_id = fields.Many2one('sped.cest', 'CEST')


class NCM(models.Model):
    _name = 'sped.ncm'
    _inherit = 'sped.ncm'

    cest_ids = fields.Many2many('sped.cest', 'sped_ncm_cest', 'ncm_id', 'cest_id', 'Códigos CEST')


class CEST(models.Model):
    _name = 'sped.cest'
    _inherit = 'sped.cest'

    ncm_ids = fields.Many2many('sped.ncm', 'sped_ncm_cest', 'cest_id', 'ncm_id', 'NCMs')
