# -*- coding: utf-8 -*-
# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp import models, api


class ResBank(models.Model):
    _inherit = 'res.bank'

    @api.multi
    @api.constrains('bic')
    def check_bic_length(self):
        # TODO - https://github.com/OCA/l10n-brazil/issues/588
        for record in self:
            if record.country_id.code == 'BR':
                return True
            return super(ResBank, record).check_bic_length()


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    @api.multi
    @api.constrains('bank_bic')
    def check_bic_length(self):
        # TODO - https://github.com/OCA/l10n-brazil/issues/588
        for record in self:
            if record.bank.country_id.code == 'BR':
                return True
            return super(ResBank, record).check_bic_length()
