# Copyright 2021 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class ResPartner(spec_models.SpecModel):
    _name = "res.partner"
    _inherit = ["res.partner", "poxsd.10.usaddress"]

    poxsd10_country = fields.Char(related="country_id.name")
    poxsd10_name = fields.Char(related="name")
    poxsd10_street = fields.Char(related="street")
    poxsd10_city = fields.Char(related="city")
    poxsd10_state = fields.Char(related="state_id.name")
    # FIXME !!
    # poxsd10_zip = fields.Monetary(
    #     currency_field="brl_currency_id",
    #     string="zip", xsd_required=True,
    #     xsd_type="decimal")


class PurchaseOrderLine(spec_models.SpecModel):
    _name = "fake.purchase.order.line"
    _inherit = ["fake.purchase.order.line", "poxsd.10.item"]

    poxsd10_productName = fields.Char(related="name")
    poxsd10_quantity = fields.Integer(related="product_qty")
    poxsd10_USPrice = fields.Monetary(related="price_unit")


class PurchaseOrder(spec_models.StackedModel):
    """
    We use StackedModel to ensure the m2o poxsd10_items field
    from poxsd.10.purchaseorder get its content (the Items class
    with the poxsd10_item o2m field included inside PurchaseOrder).
    This poxsd10_item is then related to the purchase.order order_id o2m field.
    """

    _name = "fake.purchase.order"
    _inherit = ["fake.purchase.order", "poxsd.10.purchaseordertype"]
    _spec_module = "odoo.addons.spec_driven_model.tests.spec_poxsd"
    _stacked = "poxsd.10.purchaseordertype"
    _stacking_points = {}
    _poxsd10_spec_module_classes = None

    poxsd10_orderDate = fields.Date(compute="_compute_date")
    poxsd10_confirmDate = fields.Date(related="date_approve")
    poxsd10_shipTo = fields.Many2one(related="dest_address_id", readonly=False)
    poxsd10_billTo = fields.Many2one(related="partner_id", readonly=False)
    poxsd10_item = fields.One2many(related="order_line", relation_field="order_id")

    def _compute_date(self):
        """
        Example of data casting to accomodate with the xsd model
        """
        for po in self:
            po.poxsd10_orderDate = po.date_order.date()
