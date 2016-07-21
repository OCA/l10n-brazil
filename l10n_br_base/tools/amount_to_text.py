# -*- coding: utf-8 -*-
# @ 2016 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# NOTE we can remove this once this is merged
# https://github.com/odoo/odoo/pull/11388

import openerp

# -------------------------------------------------------------
# Brazilian Portuguese
# -------------------------------------------------------------

to_19_br = ('Zero',  'Um', 'Dois', u'Três', 'Quatro', 'Cinco', 'Seis', 'Sete',
            'Oito', 'Nove', 'Dez', 'Onze', 'Doze', 'Treze', 'Quatorze',
            'Quinze', 'Dezesseis', 'Dezessete', 'Dezoito', 'Dezenove')
tens_br = ('Vinte', 'Trinta', 'Quarenta', 'Cinquenta',
           'Sessenta', 'Setenta', 'Oitenta', 'Noventa')
hundreds_br = ('Cem', 'Duzentos', 'Trezentos', 'Quatrocentos', 'Quinhentos',
               'Seicentos', 'Setecentos', 'Oitocentos', 'Novecentos')
denom_br = ('', 'Mil', u'Milhão', u'Bilhão', u'Trilhão', u'Quatrilhão',
            u'Quintilhão',  u'Sextilhão', u'Septilhão', u'Octilhão',
            u'Nonilhão', u'Decilhão', u'Undecilhão', u'Duodecilhão',
            u'Tredecilhão', u'Quattuordecilhão', u'Quindecilhão',
            u'Sexdecilhão', u'Septendecillion', u'Octodecilhão',
            u'Novendecilhão', u'Vigintilhão')
denoms_br = ('', 'Mil', u'Milhões', u'Bilhões', u'Trilhões', u'Quatrilhões',
             u'Quintilhões', u'Sextilhões', u'Septilhões', u'Octilhões',
             u'Nonilhões', u'Decilhões', u'Undecilhões', u'Duodecilhões',
             u'Tredecilhões', u'Quattuordecilhões', u'Quindecilhões',
             u'Sexdecilhões', u'Septendecilliões', u'Octodecilhões',
             u'Novendecilhões', u'Vigintilhões')


def _convert_nn_br(val):
    """ convert a value < 100 to Brazilian Portuguese
    """
    if val < 20:
        return to_19_br[val]
    for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens_br)):
        if dval + 10 > val:
            if val % 10:
                return dcap + ' e ' + to_19_br[val % 10]
            return dcap


def _convert_nnn_br(val):
    """ convert a value < 1000 to Brazilian Portuguese
        special cased because it is the level that kicks
        off the < 100 special case.  The rest are more general.
        This also allows you to get strings in the form of
        'forty-five hundred' if called directly.
    """
    word = ''
    if val > 0:
        for (dcap, dval) in (
                (k, 100 + (100 * v)) for (v, k) in enumerate(hundreds_br)):
            if dval + 100 > val:
                (mod, rem) = (val % 100, val // 100)
                if rem > 0:
                    word += dcap
                    if mod > 0:
                        word += ' e '
                if mod > 0:
                    word += _convert_nn_br(mod)
                return word


def brazil_number(val):
    if val < 100:
        return _convert_nn_br(val)
    if val < 1000:
        return _convert_nnn_br(val)
    for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom_br))):
        if dval > val:
            mod = 1000 ** didx
            l = val // mod
            r = val - (l * mod)
            if mod > 99999 and l > 2:
                ret = _convert_nnn_br(l) + ' ' + denoms_br[didx]
            else:
                ret = _convert_nnn_br(l) + ' ' + denom_br[didx]

            if r > 0:
                ret = ret + ', ' + brazil_number(r)

            return ret


def amount_to_text_br(number, currency):
    number = '%.2f' % number
    units_name = currency
    list = str(number).split('.')
    start_word = brazil_number(int(list[0]))
    end_word = brazil_number(int(list[1]))
    cents_number = int(list[1])
    cents_name = (cents_number > 1) and 'Centavos' or 'Centavo'
    final_result = (start_word + ' ' + units_name +
                    ' e ' + ' ' + end_word + ' ' + cents_name)
    return final_result

openerp.tools.amount_to_text_br = amount_to_text_br
