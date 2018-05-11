# -*- coding: utf-8 -*-
#  @ 2018 KMEE - www.kmee.com.br -
#  Bianca da Rocha Bartolomei <biancabartolomei@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestProductTemplate(TransactionCase):

    def setUp(self):
        super(TestProductTemplate, self).setUp()
        self.codebar = self.env['product.template']

    def test_00_valida_codigo_barras(self):
        """"
        Testa funcao de validacao de codigo de barras, em que codigo de
        barras esta correto
        """
        codigo_barras = self.codebar.create({
            'name': 'Teste Barcode',
            'barcode': '5901234123457',
        })
        try:
            codigo_barras._valida_codigo_barras()
        except Exception:
            assert u"Codigo de barras incorreto"

    def test_01_valida_codigo_barras_tributacao(self):
        """"
        Testa funcao de validacao de codigo de barras tributacao, em que
        codigo de barras esta correto
        """
        codigo_barras_tributacao = self.codebar.create({
            'name': 'Teste Barcode Tributacao',
            'codigo_barras_tributacao': '5901234123457',
        })

        try:
            codigo_barras_tributacao._valida_codigo_barras()
        except Exception:
            assert u"Codigo de barras incorreto"

    def test_02_valida_codigo_barras_incorreto(self):
        """"
        Testa funcao de validacao de codigo de barras, em que codigo de
        barras esta incorreto
        """
        with self.assertRaises(ValidationError):
            codigo_barras = self.codebar.create({
                'name': 'Teste Barcode',
                'barcode': 'A1234123457',
            })
            codigo_barras._valida_codigo_barras()

    def test_03_valida_codigo_barras_tributacao_incorreto(self):
        """"
        Testa funcao de validacao de codigo de barras tributacao, em que
        codigo de barras esta incorreto
        """
        with self.assertRaises(ValidationError):
            codigo_barras_tributacao = self.codebar.create({
                'name': 'Teste Barcode Tributacao',
                'codigo_barras_tributacao': 'A01234123457',
            })
            codigo_barras_tributacao._valida_codigo_barras()
