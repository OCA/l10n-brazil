# Copyright (C) 2020 - TODAY Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    partner_order = fields.Char(
        string=u'Código do Pedido (xPed)',
        size=15)

    partner_order_line = fields.Char(
        string=u'Item do Pedido (nItemPed)',
        size=6)

    @api.onchange('partner_order_line')
    def _check_partner_order_line(self):
        if (self.partner_order_line and
                not self.partner_order_line.isdigit()):
            raise ValidationError(
                _(u"Customer Order Line must "
                  "be a number with up to six digits"))
