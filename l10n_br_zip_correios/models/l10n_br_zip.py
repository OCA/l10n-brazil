# Copyright (C) 2016  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api
from odoo.addons.l10n_br_base.tools import misc

from .webservice_client import WebServiceClient


class L10nBrZip(models.Model):
    _inherit = 'l10n_br.zip'

    @api.model
    def zip_search(self, obj):

        zip_str = misc.punctuation_rm(obj.zip)

        if len(zip_str) == 8:
            WebServiceClient(self).get_address(zip_str)

        return super(L10nBrZip, self).zip_search(obj)
