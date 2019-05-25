# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, api


class AccountFiscalPositionAbstract(object):
    pass


class AccountFiscalPositionTaxAbstract(object):

    tax_group_id = fields.Many2one(
        comodel_name='account.tax.group',
        string=u'Grupo de Impostos',
    )

    @api.onchange('tax_src_id',
                  'tax_group_id',
                  'position_id')
    def _onchange_tax_group(self):
        type_tax_use = {'input': 'purchase', 'output': 'sale'}
        domain = []

        if self.position_id.type:
            domain = [('type_tax_use', '=',
                      (type_tax_use.get(self.position_id.type)))]

        if self.tax_group_id:
            domain.append(('tax_group_id', '=', self.tax_group_id.id))

        if self.tax_src_id:
            domain.append(('tax_group_id', '=',
                           self.tax_src_id.tax_group_id.id))

        return {'domain': {'tax_dest_id': domain, 'tax_src_id': domain}}
