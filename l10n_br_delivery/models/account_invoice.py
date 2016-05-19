# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2010  Renato Lima - Akretion
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

from openerp import api, fields, models
from openerp.tools.translate import _
from openerp.exceptions import Warning as UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    carrier_id = fields.Many2one(
        'delivery.carrier', 'Método de transporte', readonly=True,
        states={'draft': [('readonly', False)]})
    vehicle_id = fields.Many2one(
        'l10n_br_delivery.carrier.vehicle', u'Veículo', readonly=True,
        states={'draft': [('readonly', False)]})
    incoterm = fields.Many2one(
        'stock.incoterms', 'Tipo do Frete', readonly=True,
        states={'draft': [('readonly', False)]},
        help="Incoterm which stands for 'International Commercial terms' "
             "implies its a series of sales terms which are used in the "
             "commercial transaction.")

    @api.onchange('carrier_id')
    def onchange_carrier_id(self):
        self.partner_carrier_id = self.carrier_id.partner_id

    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        self.vehicle_plate = self.vehicle_id.plate
        self.vehicle_state_id = self.vehicle_id.state_id
        self.vehicle_l10n_br_city_id = self.vehicle_id.l10n_br_city_id

    @api.onchange('incoterm')
    def onchange_incoterm(self):
        self.freight_responsibility = self.incoterm.freight_responsibility

    def nfe_check(self, cr, uid, ids, context=None):
        result = super(AccountInvoice, self).nfe_check(cr, uid, ids, context)
        strErro = u''

        for inv in self.browse(cr, uid, ids, context=context):
            # Carrier
            if inv.carrier_id:

                if not inv.carrier_id.partner_id.legal_name:
                    strErro = u'Transportadora - Razão Social\n'

                if not inv.carrier_id.partner_id.cnpj_cpf:
                    strErro = 'Transportadora - CNPJ/CPF\n'

            # Carrier Vehicle
            if inv.vehicle_id:

                if not inv.vehicle_id.plate:
                    strErro = u'Transportadora / Veículo - Placa\n'

                if not inv.vehicle_id.state_id.code:
                    strErro = u'Transportadora / Veículo - UF da Placa\n'

                if not inv.vehicle_id.rntc_code:
                    strErro = u'Transportadora / Veículo - RNTC\n'

        if strErro:
            raise UserError(
                _('Error!'),
                _(u"Validação da Nota fiscal:\n '%s'") % (strErro))

        return result
