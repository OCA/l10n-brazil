# -*- coding: utf-8 -*-
# Copyright (C) 2012  Renato Lima - Akretion                                  #
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api


class CrmLead(models.Model):
    """ CRM Lead Case """
    _inherit = "crm.lead"

    @api.multi
    def zip_search(self):
        self.ensure_one()
        return self.env['l10n_br.zip'].zip_search(self)
