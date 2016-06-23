# -*- coding: utf-8 -*-
# See README.rst file on addon root folder for license details

from openerp import models, fields
from openerp.addons import decimal_precision as dp

SIMPLIFIED_INVOICE_TYPE = [
    ('nfce', u'NFC-E'),
    ('sat', u'SAT'),
    ('paf', u'PAF-ECF'),
]


class PosConfig(models.Model):
    _inherit = 'pos.config'

    simplified_invoice_limit = fields.Float(
        string=u'Simplified invoice limit',
        digits=dp.get_precision('Account'),
        help=u'Over this amount is not legally posible to create a '
             u'simplified invoice',
        default=3000)
    simplified_invoice_type = fields.Selection(
        string='Simplified Invoice Type',
        selection=SIMPLIFIED_INVOICE_TYPE,
        help=u'Tipo de documento emitido pelo PDV',
    )

    save_identity_automatic = fields.Boolean(
        string='Save new client identity automatic',
        default=True
    )

    iface_sat_via_proxy = fields.Boolean(
        'SAT',
        help="Ao utilizar o SAT é necessário ativar esta opção"
    )
