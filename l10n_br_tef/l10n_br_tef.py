# -*- coding: utf-8 -*-

from openerp import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    iface_tef = fields.Boolean(
        'TEF',
        help="A TEF terminal is available on the Proxy")
