# -*- coding: utf-8 -*-
# Copyright (C) 2009 Gabriel C. Stabel
# Copyright (C) 2009 Renato Lima (Akretion)
# Copyright (C) 2012 Raphaël Valyi (Akretion)
# Copyright (C) 2018 Luis Felipe Mileo (KMEE INFORMATICA LTDA)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import re

from odoo import models, fields, api


class ResPartnerBank(models.Model):
    """ Adiciona campos necessários para o cadastramentos de contas
    bancárias no Brasil."""
    _inherit = 'res.partner.bank'

    number = fields.Char(u'Número', size=10)
    street = fields.Char('Street', size=128)
    street2 = fields.Char('Street2', size=128)
    district = fields.Char('Bairro', size=32)
    state_id = fields.Many2one(
        "res.country.state", 'Fed. State',
        change_default=True,
    )
    l10n_br_city_id = fields.Many2one(
        'l10n_br_base.city', 'Municipio',
        domain="[('state_id','=',state_id)]")
    acc_number = fields.Char("Account Number", size=64, required=False)
    bank = fields.Many2one('res.bank', 'Bank', required=False)
    acc_number_dig = fields.Char('Digito Conta', size=8)
    bra_number = fields.Char(u'Agência', size=8)
    bra_number_dig = fields.Char(u'Dígito Agência', size=8)
    zip = fields.Char('CEP', size=24, change_default=True)
    country_id = fields.Many2one('res.country', 'País', ondelete='restrict')

    @api.multi
    def onchange_partner_id(self, partner_id):
        result = super(ResPartnerBank, self).onchange_partner_id(partner_id)
        partner = self.env['res.partner'].browse(partner_id)
        result['value']['number'] = partner.number
        result['value']['district'] = partner.district
        result['value']['l10n_br_city_id'] = partner.l10n_br_city_id.id
        return result

    @api.onchange('zip')
    def _onchange_zip(self):
        if self.zip:
            val = re.sub('[^0-9]', '', self.zip)
            if len(val) == 8:
                self.zip = "%s-%s" % (val[0:5], val[5:8])
