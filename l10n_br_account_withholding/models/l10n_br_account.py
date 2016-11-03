# -*- coding: utf-8 -*-
# © 2016 KMEE(http://www.kmee.com.br)
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models
from openerp.addons import decimal_precision as dp


class L10nbrAccountPartnerFiscalType(models.Model):
    _inherit = 'l10n_br_account.partner.fiscal.type'

    issqn_wh = fields.Boolean(u'Retém ISSQN')
    inss_wh = fields.Boolean(u'Retém INSS')
    pis_wh = fields.Boolean(u'Retém PIS')
    cofins_wh = fields.Boolean(u'Retém COFINS')
    csll_wh = fields.Boolean(u'Retém CSLL')
    irrf_wh = fields.Boolean(u'Retém IRRF')
    irrf_wh_percent = fields.Float(u'Retenção de IRRF (%)',
                                   digits_compute=dp.get_precision('Discount'))
