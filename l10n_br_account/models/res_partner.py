# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _default_partner_fiscal_type_id(self, is_company=False):
        """Define o valor padão para o campo tipo fiscal, por padrão pega
        o tipo fiscal para não contribuinte já que quando é criado um novo
        parceiro o valor do campo is_company é false"""
        ft_ids = self.env['l10n_br_account.partner.fiscal.type'].search(
            [('default', '=', 'True'), ('is_company', '=', is_company)],
            limit=1)
        return ft_ids

    partner_fiscal_type_id = fields.Many2one(
        comodel_name='l10n_br_account.partner.fiscal.type',
        string=u'Tipo Fiscal do Parceiro',
        domain="[('is_company', '=', is_company)]",
        default=_default_partner_fiscal_type_id)

    partner_special_fiscal_type_id = fields.Many2many(
        comodel_name='l10n_br_account.partner.special.fiscal.type',
        relation='res_partner_l10n_br_special_type',
        string='Regime especial')

    @api.onchange('is_company')
    def _onchange_is_company(self):
        self.partner_fiscal_type_id = \
            self._default_partner_fiscal_type_id(self.is_company)
