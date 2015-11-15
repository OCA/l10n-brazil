# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2014  Renato Lima - Akretion                                  #
# Copyright (C) 2015  Luis Felipe Mileo - KMEE             #
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

import re
import string


def punctuation_rm(string_value):
    tmp_value = (
        re.sub('[%s]' % re.escape(string.punctuation), '', string_value or ''))
    return tmp_value


def calc_price_ratio(price_gross, amount_calc, amount_total):
    if amount_total:
        return price_gross * amount_calc / amount_total
    else:
        return 0.0
