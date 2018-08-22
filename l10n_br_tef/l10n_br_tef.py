# -*- coding: utf-8 -*-

from openerp import models, fields, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    iface_tef = fields.Boolean(
        string="TEF",
        help=_("A TEF terminal is available on the Proxy"),
    )

    institution_selection = fields.Selection(
        selection=[
            ('Administradora', 'Administradora'),
            ('Estabelecimento', 'Estabelecimento')
        ],
        string="Institution",
        help=_("Institution selection for installment payments"),
        default='Estabelecimento',
    )
