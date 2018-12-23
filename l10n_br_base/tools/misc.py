# -*- coding: utf-8 -*-
# Copyright (C) 2014  Renato Lima - Akretion
# Copyright (C) 2015  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

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


def format_zipcode(zipcode, country_code):
    if zipcode and country_code.upper() == 'BR':
        zipcode_br = ''
        val = re.sub('[^0-9]', '', zipcode)
        if len(val) == 8:
            zipcode_br = "%s-%s" % (val[0:5], val[5:8])
        return zipcode_br
