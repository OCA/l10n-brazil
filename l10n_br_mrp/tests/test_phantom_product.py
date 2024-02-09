# Copyright (C) 2023-Today - Akretion (<https://akretion.com/pt-BR>).
# @author Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests.common import TransactionCase


class TestPhantomProduct(TransactionCase):

    # TODO criar um picking de testes com o item fantasma/kit

    @classmethod
    def setUpClass(cls):
        super(TestPhantomProduct, cls).setUpClass()
        bom_1 = cls.env['mrp.bom'].create({
            'product_id': cls.product_5.id,
            'product_tmpl_id': cls.product_5.product_tmpl_id.id,
            'product_uom_id': cls.product_5.uom_id.id,
            'product_qty': 1.0,
            'type': 'phantom',
            'sequence': 1,
            'bom_line_ids': [
                (0, 0, {'product_id': cls.product_4.id, 'product_qty': 2}),
                (0, 0, {'product_id': cls.product_3.id, 'product_qty': 3})
            ]})