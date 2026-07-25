# Copyright 2024 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestOperation(TransactionCase):
    def test_copy(self):
        """Test Operation copy()"""
        operation_venda = self.env.ref("l10n_br_fiscal.fo_venda")
        operation_venda_copy = operation_venda.copy()
        self.assertEqual(operation_venda_copy.name, "Venda")
        self.assertEqual(operation_venda_copy.code, "VD (Copy)")

    def test_bonificacao_line_definition(self):
        """Bonificação resolve linha para destinatário e produto quaisquer.

        ind_ie_dest e product_type são critério de match em _line_domain, onde
        vazio funciona como curinga, e a operação tem uma única linha. Se algum
        deles for fixado, a bonificação para não contribuinte, ou para produto
        sem classificação fiscal, fica sem linha e portanto sem CFOP e sem
        impostos.
        """
        operation = self.env.ref("l10n_br_fiscal.fo_bonificacao")
        partner = self.env["res.partner"].create(
            {"name": "Destinatário não contribuinte", "ind_ie_dest": "9"}
        )
        product = self.env["product.product"].create(
            {"name": "Produto sem tipo fiscal"}
        )
        line = operation.line_definition(self.env.company, partner, product)
        self.assertTrue(line, "bonificação ficou sem linha de operação")
        self.assertEqual(line.cfop_internal_id.code, "5910")
