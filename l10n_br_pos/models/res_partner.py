# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create_from_ui(self, partner):
        res = super(ResPartner, self).create_from_ui(partner)
        partner_id = self.browse(res)
        fiscal_type = self.env['l10n_br_account.partner.fiscal.type'].search(
            [('name', '=', 'Não Contribuinte PF')]
        )
        partner_id.partner_fiscal_type_id = fiscal_type.id
        if self.env.user.company_id.parent_id:
            partner_id.company_id = self.env.user.company_id.parent_id.id
        return res
