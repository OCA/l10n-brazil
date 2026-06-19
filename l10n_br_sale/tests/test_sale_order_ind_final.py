# Copyright 2026 Engenere
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import Form, TransactionCase
from odoo.tests.common import tagged


@tagged("post_install", "-at_install")
class TestSaleOrderIndFinal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.user = cls.env.user
        cls.user.company_ids |= cls.company
        cls.user.company_id = cls.company.id
        cls.product = cls.env.ref("product.product_product_6")

    def _create_sale_order_form(self, partner):
        """Create a sale order Form pre-filled with the given partner."""
        so_form = Form(self.env["sale.order"])
        so_form.company_id = self.company
        so_form.partner_id = partner
        so_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        return so_form

    def test_ind_final_propagation_on_manual_change(self):
        """Changing ind_final on a saved sale order must propagate to lines."""
        partner = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        partner.ind_final = "1"

        so_form = self._create_sale_order_form(partner)
        with so_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 1.0

        so = so_form.save()
        line = so.order_line.filtered(lambda line: not line.display_type)[0]
        self.assertEqual(so.ind_final, "1")
        self.assertEqual(line.ind_final, "1")

        # Manually change ind_final on the order
        so.write({"ind_final": "0"})
        self.assertEqual(so.ind_final, "0")
        self.assertEqual(line.ind_final, "0")

    def test_ind_final_propagation_on_partner_change(self):
        """Changing partner_id on a saved sale order must propagate ind_final
        to lines when the new partner has a different ind_final."""
        partner_final = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        partner_final.ind_final = "1"
        partner_not_final = self.env.ref("l10n_br_base.res_partner_cliente5_pe")
        partner_not_final.ind_final = "0"

        so_form = self._create_sale_order_form(partner_final)
        with so_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 1.0

        so = so_form.save()
        line = so.order_line.filtered(lambda line: not line.display_type)[0]
        self.assertEqual(so.ind_final, "1")
        self.assertEqual(line.ind_final, "1")

        # Change to a partner with ind_final="0"
        so.write({"partner_id": partner_not_final.id})
        self.assertEqual(so.ind_final, "0")
        self.assertEqual(line.ind_final, "0")

    def test_ind_final_propagation_on_form_partner_change(self):
        """Changing partner_id on a form before saving must propagate
        ind_final to lines when saved."""
        partner_final = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        partner_final.ind_final = "1"
        partner_not_final = self.env.ref("l10n_br_base.res_partner_cliente5_pe")
        partner_not_final.ind_final = "0"

        so_form = self._create_sale_order_form(partner_final)
        with so_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 1.0

        self.assertEqual(so_form.ind_final, "1")

        # Change partner before saving
        so_form.partner_id = partner_not_final
        self.assertEqual(so_form.ind_final, "0")

        so = so_form.save()
        line = so.order_line.filtered(lambda line: not line.display_type)[0]
        self.assertEqual(so.ind_final, "0")
        self.assertEqual(line.ind_final, "0")
