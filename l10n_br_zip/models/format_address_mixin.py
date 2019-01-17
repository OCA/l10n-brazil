# -*- coding: utf-8 -*-
# Copyright (C) 2010-2012  Renato Lima (Akretion)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api
from odoo.exceptions import UserError


class FormatAddressMixin(models.AbstractModel):
    _inherit = "format.address.mixin"

    @api.multi
    def zip_search(self):
        self.ensure_one()
        return self.env['l10n_br.zip'].zip_search(self)
