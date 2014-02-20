# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

import re
import string
from datetime import datetime

from openerp import pooler
from openerp.osv import orm
from openerp.tools.translate import _
from openerp.addons.l10n_br_account_product.sped.nfe.document import NFe200

from pysped.nfe.leiaute import NFe_200, Det_200, NFRef_200, Dup_200


class NFe200(NFe200):

    def __init__(self):
        super(NFe200, self).__init__()
