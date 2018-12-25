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
        try:
            kargs = {
                'country_id': self.country_id.id,
                'state_id': self.state_id.id,
                'city_id': self.city_id.id,
                'district': self.district,
                'street': self.street,
                'zip_code': self.zip}
        except AttributeError as e:
            raise UserError(
                u'Erro a Carregar Atributo: ' + str(e)) 

        return self.env['l10n_br.zip'].zip_search(**kargs)

