# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2015 Luis Felipe Mileo - www.kmee.com.br                      #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from openerp import models, fields


class L10n_brAccountFiscalDocument(models.Model):
    _inherit = 'l10n_br_account.fiscal.document'

    edoc_type = fields.Selection(
        selection_add=[('nfe', u'55 - Nota Fiscal Eletrônica')]
    )