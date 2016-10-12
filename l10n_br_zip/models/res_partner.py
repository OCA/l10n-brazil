# -*- coding: utf-8 -*-
# Copyright (C) 2010-2012  Renato Lima (Akretion)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def zip_search(self):
        self.ensure_one()
        return self.env['l10n_br.zip'].zip_search(self)


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    @api.multi
    def zip_search(self):
        self.ensure_one()
        return self.env['l10n_br.zip'].zip_search(self)
