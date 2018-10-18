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
            ('Administradora', _('Administrator')),
            ('Estabelecimento', _('Institute'))
        ],
        string="Institution",
        help=_("Institution selection for installment payments"),
        default='Estabelecimento',
    )

    credit_server = fields.Char(
        string=_("Credit Approval Server"),
        help=_("Which credit approval server should be used"),
    )

    debit_server = fields.Char(
        string=_("Debit Approval Server"),
        help=_("Which debit approval server should be used"),
    )
