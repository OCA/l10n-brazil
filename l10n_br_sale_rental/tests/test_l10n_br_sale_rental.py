# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestL10nBrSaleRental(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env.user.company_ids |= cls.company
        cls.env.user.company_id = cls.company
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=[cls.company.id])
        )
        cls.fo_locacao = cls.env.ref("l10n_br_fiscal.fo_locacao")
        cls.fo_remessa = cls.env.ref("l10n_br_fiscal.fo_remessa_comodato")
        cls.fo_retorno = cls.env.ref("l10n_br_fiscal.fo_entrada_retorno_comodato")
        journal = cls.env["account.journal"].create(
            {
                "name": "Remessa e retorno de locacao",
                "code": "TLOC",
                "type": "sale",
                "company_id": cls.company.id,
            }
        )
        (cls.fo_remessa | cls.fo_retorno).journal_id = journal

        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        # sale_rental creates its routes for the main company: shared here so
        # the warehouse of another company can rent
        (
            cls.env.ref("sale_rental.route_warehouse0_rental")
            | cls.env.ref("sale_rental.route_warehouse0_sell_rented_product")
        ).company_id = False
        cls.warehouse.rental_allowed = True

        # construction companies are usually not ICMS taxpayers
        cls.partner = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")
        cls.partner.ind_ie_dest = "9"

        cls.equipment = cls.env["product.product"].create(
            {
                "name": "Betoneira 400 l",
                "detailed_type": "product",
                "fiscal_type": "00",
                "standard_price": 4800.0,
                "list_price": 6000.0,
            }
        )
        cls.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": cls.equipment.id,
                "location_id": cls.warehouse.rental_in_location_id.id,
                "inventory_quantity": 5,
            }
        )._apply_inventory()
        wizard = (
            cls.env["create.rental.product"]
            .with_context(active_model="product.product", active_id=cls.equipment.id)
            .create(
                {
                    "sale_price_per_day": 90.0,
                    "categ_id": cls.env.ref("product.product_category_all").id,
                }
            )
        )
        cls.rental_service = cls.env["product.product"].browse(
            wizard.create_rental_product()["res_id"]
        )

    def _create_order(self, partner=None):
        start = fields.Date.today()
        return self.env["sale.order"].create(
            {
                "partner_id": (partner or self.partner).id,
                "company_id": self.company.id,
                "warehouse_id": self.warehouse.id,
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_venda").id,
                # sale_start_end_dates computes the line dates from these
                "default_start_date": start,
                "default_end_date": start + timedelta(days=4),
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.rental_service.id,
                            "rental_type": "new_rental",
                            "rental_qty": 2,
                            "start_date": start,
                            "end_date": start + timedelta(days=4),
                            # as in sale_rental tests: the rental quantity check
                            # runs before the days are computed
                            "number_of_days": 5,
                            "product_uom_qty": 10,
                            "price_unit": 90.0,
                        },
                    )
                ],
            }
        )

    def _deliver(self, order):
        picking = order.picking_ids.filtered(
            lambda p: p.picking_type_id.l10n_br_rental_kind == "remessa"
        )
        picking.move_ids.quantity_done = 2
        picking._action_done()
        return picking

    def _invoice_picking(self, picking):
        wizard = (
            self.env["stock.invoice.onshipping"]
            .with_context(active_ids=picking.ids, active_model="stock.picking")
            .create({})
        )
        wizard.onchange_group()
        wizard.action_generate()
        return picking.invoice_ids

    def test_rental_service_product(self):
        self.assertEqual(self.rental_service.rented_product_id, self.equipment)
        self.assertEqual(self.rental_service.fiscal_type, "09")
        self.assertEqual(self.rental_service.tax_icms_or_issqn, "issqn")

    def test_rental_rules(self):
        out_type = self.warehouse.l10n_br_rental_out_type_id
        in_type = self.warehouse.l10n_br_rental_in_type_id
        self.assertEqual(out_type.l10n_br_rental_kind, "remessa")
        self.assertEqual(in_type.l10n_br_rental_kind, "retorno")
        rules = self.env["stock.rule"].search(
            [
                ("route_id", "=", self.warehouse.rental_route_id.id),
                ("warehouse_id", "=", self.warehouse.id),
            ]
        )
        pull = rules.filtered(
            lambda r: r.action == "pull" and r.picking_type_id == out_type
        )
        push = rules.filtered(
            lambda r: r.action == "push" and r.picking_type_id == in_type
        )
        self.assertEqual(pull.fiscal_operation_id, self.fo_remessa)
        self.assertEqual(push.fiscal_operation_id, self.fo_retorno)
        self.assertEqual(set((pull | push).mapped("invoice_state")), {"2binvoiced"})

    def _rental_picking(self, order, kind):
        return order.picking_ids.filtered(
            lambda p: p.picking_type_id.l10n_br_rental_kind == kind
        )

    def test_remessa_and_retorno(self):
        order = self._create_order()
        order.action_confirm()
        # sale_rental creates the delivery and the return on confirmation
        self.assertEqual(len(order.picking_ids), 2)
        remessa = self._rental_picking(order, "remessa")
        self.assertEqual(remessa.fiscal_operation_id, self.fo_remessa)
        self.assertEqual(remessa.invoice_state, "2binvoiced")
        # company and lessee in SP, lessee not an ICMS taxpayer
        self.assertEqual(remessa.move_ids.cfop_id.code, "5908")
        self.assertEqual(remessa.move_ids.icms_cst_id.code, "41")
        self.assertEqual(remessa.move_ids.tax_classification_id.code, "410029")

        retorno = self._rental_picking(order, "retorno")
        self.assertEqual(retorno.fiscal_operation_id, self.fo_retorno)
        self.assertEqual(retorno.invoice_state, "2binvoiced")
        self.assertEqual(
            retorno.move_ids.fiscal_operation_line_id,
            self.env.ref("l10n_br_fiscal.fo_entrada_retorno_comodato_line"),
        )
        self.assertEqual(retorno.move_ids.cfop_id.code, "1909")

        self._deliver(order)
        self.assertEqual(retorno.state, "assigned")

    def test_retorno_taxpayer_lessee(self):
        self.partner.ind_ie_dest = "1"
        order = self._create_order()
        order.action_confirm()
        retorno = self._rental_picking(order, "retorno")
        # the lessee issues the return NF-e: nothing for the company to issue
        self.assertEqual(retorno.invoice_state, "none")

    def test_remessa_invoice(self):
        order = self._create_order()
        order.action_confirm()
        remessa = self._deliver(order)
        invoice = self._invoice_picking(remessa)
        self.assertEqual(invoice.move_type, "out_invoice")
        self.assertEqual(invoice.fiscal_operation_id, self.fo_remessa)
        line = invoice.invoice_line_ids
        self.assertEqual(line.product_id, self.equipment)
        self.assertEqual(line.cfop_id.code, "5908")
        # asset value, not the rental price
        self.assertEqual(line.price_unit, 4800.0)
        # not linked to the rental service line: the rent is still to invoice
        self.assertFalse(line.sale_line_ids)
        self.assertEqual(order.order_line.qty_invoiced, 0)

    def test_retorno_invoice(self):
        order = self._create_order()
        order.action_confirm()
        self._deliver(order)
        retorno = self._rental_picking(order, "retorno")
        retorno.move_ids.quantity_done = 2
        retorno._action_done()
        invoice = self._invoice_picking(retorno)
        self.assertEqual(invoice.move_type, "out_refund")
        self.assertEqual(invoice.issuer, "company")
        self.assertEqual(invoice.invoice_line_ids.cfop_id.code, "1909")

    def test_rental_charge(self):
        order = self._create_order()
        line = order.order_line
        self.assertEqual(line.fiscal_operation_id, self.fo_locacao)
        self.assertEqual(
            line.fiscal_operation_line_id,
            self.env.ref("l10n_br_fiscal.fo_locacao_line"),
        )
        order.action_confirm()
        self._deliver(order)
        invoice = order._create_invoices()
        self.assertEqual(invoice.fiscal_operation_id, self.fo_locacao)
        self.assertEqual(invoice.document_type_id.code, "SE")
        invoice_line = invoice.invoice_line_ids
        self.assertEqual(invoice_line.product_id, self.rental_service)
        self.assertEqual(invoice_line.tax_classification_id.code, "000001")
        # the rental charge is not an invoice of the remessa/retorno transfers
        self.assertFalse(invoice_line.move_line_ids)
        self.assertNotIn(invoice, order.picking_ids.mapped("invoice_ids"))
        # rental of movable goods: no ISS (STF Sumula Vinculante 31) and, not
        # being a goods operation, no ICMS/IPI either
        self.assertFalse(invoice_line.issqn_value)
        self.assertFalse(invoice_line.icms_tax_id)
        self.assertFalse(invoice_line.ipi_tax_id)
        self.assertAlmostEqual(invoice.amount_untaxed, 900.0)

    def test_remessa_simples_nacional(self):
        self.company.tax_framework = "1"
        order = self._create_order()
        order.action_confirm()
        move = self._rental_picking(order, "remessa").move_ids
        # Simples Nacional: ICMS by CSOSN, not by CST
        self.assertEqual(
            move.fiscal_operation_line_id,
            self.env.ref("l10n_br_fiscal.fo_remessa_comodato_line_sn"),
        )
        self.assertEqual(move.cfop_id.code, "5908")
        self.assertEqual(move.icms_cst_id.code, "400")
