# -*- coding: utf-8 -*-
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Thinkopen - Brasil
#    Copyright (C) Thinkopen Solutions (<http://www.thinkopensolutions.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def zip_search(self):
        self.ensure_one()
        return self.env['l10n_br.zip'].zip_search(self)
