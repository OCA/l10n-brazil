# -*- coding: utf-8 -*-
# @ 2016 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# NOTE we can remove this once this is merged
# https://github.com/odoo/odoo/pull/11388

from openerp.tools import amount_to_text_br
from openerp.tests.common import TransactionCase


class Tests(TransactionCase):

    def test_01_amount_to_text(self):
        text_number = amount_to_text_br(99.99, 'REAIS')
        self.assertEqual(
            text_number,
            'Noventa e Nove REAIS e  Noventa e Nove Centavos')

    def test_02_amount_to_text(self):
        text_number = amount_to_text_br(1999.99, 'REAIS')
        self.assertEqual(
            text_number,
            'Um Mil, Novecentos e Noventa e Nove REAIS'
            ' e  Noventa e Nove Centavos')

    def test_03_amount_to_text(self):
        text_number = amount_to_text_br(77777.0, 'REAIS')
        self.assertEqual(
            text_number,
            u'Setenta e Sete Mil, Setecentos e Setenta'
            u' e Sete REAIS e  Zero Centavo')

    def test_04_amount_to_text(self):
        text_number = amount_to_text_br(1856333.0, 'REAIS')
        self.assertEqual(
            text_number,
            u'Um Milhão, Oitocentos e Cinquenta e Seis Mil,'
            u' Trezentos e Trinta e Três REAIS e  Zero Centavo')

    def test_05_amount_to_text(self):
        text_number = amount_to_text_br(9999999.0, 'REAIS')
        self.assertEqual(
            text_number,
            u'Nove Milhões, Novecentos e Noventa e Nove Mil,'
            u' Novecentos e Noventa e Nove REAIS e  Zero Centavo')

    def test_06_amount_to_text(self):
        text_number = amount_to_text_br(9999999999.0, 'REAIS')
        self.assertEqual(
            text_number,
            u'Nove Bilhões, Novecentos e Noventa e Nove Milhões,'
            u' Novecentos e Noventa e Nove Mil, Novecentos e'
            u' Noventa e Nove REAIS e  Zero Centavo')
