# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2016  Magno Costa - Akretion
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

from openerp import models, api
from openerp.addons.l10n_br_zip_correios.models.webservice_client\
    import WebServiceClient


class L10nBrZip(models.Model, WebServiceClient):

    _inherit = 'l10n_br.zip'

    @api.multi
    def zip_search_multi(self, country_id=False,
                         state_id=False, l10n_br_city_id=False,
                         district=False, street=False, zip_code=False):

        self.get_address(zip_code)
        return super(L10nBrZip, self).zip_search_multi(
            country_id, state_id, l10n_br_city_id, district, street, zip_code)
