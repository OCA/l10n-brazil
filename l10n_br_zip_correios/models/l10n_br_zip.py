# -*- encoding: utf-8 -*-
##############################################################################
#
#    Address from Brazilian Localization ZIP by Correios to Odoo
#    Copyright (C) 2015 KMEE (http://www.kmee.com.br)
#    @author Michell Stuttgart <michell.stuttgart@kmee.com.br>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields
from openerp.exceptions import except_orm


class L10nBrZip(models.Model):

    _inherit = 'l10n_br.zip'

    def set_result(self, zip_obj=None):
        result = super(L10nBrZip, self).set_result(zip_obj=zip_obj)

        if 'street' in result:
            # Remove white space in begin of street name
            result['street'] = result['street'].lstrip()

        return result
