# Copyright 2021 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Sun Mar 21 09:03:49 2021 by https://github.com/akretion/generateds-odoo
# and generateDS.py.
# Python 3.8.5 (default, Jul 28 2020, 12:59:40)  [GCC 9.3.0]
#
import textwrap
from odoo import fields, models


class DanglingModelExample(models.AbstractModel):
    """
    All the code in this file is generated according to the header command
    from the PurchaseOrderSchema.xsd file,
    except this class which was hand written to serve as an example of
    spec mixin that would not be injected in any Odoo model and would
    eventually need to be turned concrete by the spec_model_driven_hook.
    """
    _name = 'poxsd.10.dangling_model'
    _description = 'dangling model example'
    _inherit = 'spec.mixin.poxsd'

    name = fields.Char()


class Items(models.AbstractModel):
    _description = 'items'
    _name = 'poxsd.10.items'
    _inherit = 'spec.mixin.poxsd'
    _generateds_type = 'Items'
    _concrete_rec_name = 'poxsd10_item'

    poxsd10_item = fields.One2many(
        "poxsd.10.item",
        "poxsd10_item_Items_id",
        string="item"
    )


class PurchaseOrder(models.AbstractModel):
    _description = 'purchaseorder'
    _name = 'poxsd.10.purchaseorder'
    _inherit = 'spec.mixin.poxsd'
    _generateds_type = 'PurchaseOrderType'
    _concrete_rec_name = 'poxsd10_orderDate'

    poxsd10_orderDate = fields.Date(
        string="orderDate",
        xsd_type="date")
    poxsd10_confirmDate = fields.Date(
        string="confirmDate", xsd_required=True,
        xsd_type="date")
    poxsd10_shipTo = fields.Many2one(
        "poxsd.10.usaddress",
        string="shipTo", xsd_required=True)
    poxsd10_billTo = fields.Many2one(
        "poxsd.10.usaddress",
        string="billTo", xsd_required=True)
    poxsd10_comment = fields.Char(
        string="comment",
        xsd_type="string")
    poxsd10_items = fields.Many2one(
        "poxsd.10.items",
        string="items", xsd_required=True)


class USAddress(models.AbstractModel):
    "Purchase order schema for Example.Microsoft.com."
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'poxsd.10.usaddress'
    _inherit = 'spec.mixin.poxsd'
    _generateds_type = 'USAddress'
    _concrete_rec_name = 'poxsd10_country'

    poxsd10_country = fields.Char(
        string="country",
        xsd_type="NMTOKEN")
    poxsd10_name = fields.Char(
        string="name", xsd_required=True,
        xsd_type="string")
    poxsd10_street = fields.Char(
        string="street", xsd_required=True,
        xsd_type="string")
    poxsd10_city = fields.Char(
        string="city", xsd_required=True,
        xsd_type="string")
    poxsd10_state = fields.Char(
        string="state", xsd_required=True,
        xsd_type="string")
    poxsd10_zip = fields.Monetary(
        currency_field="brl_currency_id",
        string="zip", xsd_required=True,
        xsd_type="decimal")


class Item(models.AbstractModel):
    _description = 'item'
    _name = 'poxsd.10.item'
    _inherit = 'spec.mixin.poxsd'
    _generateds_type = 'ItemType'
    _concrete_rec_name = 'poxsd10_partNum'

    poxsd10_item_Items_id = fields.Many2one(
        "poxsd.10.items")
    poxsd10_partNum = fields.Char(
        string="partNum",
        xsd_type="string")
    poxsd10_productName = fields.Char(
        string="productName", xsd_required=True,
        xsd_type="string")
    poxsd10_quantity = fields.Integer(
        string="quantity", xsd_required=True,
        xsd_type="quantityType")
    poxsd10_USPrice = fields.Monetary(
        currency_field="brl_currency_id",
        string="USPrice", xsd_required=True,
        xsd_type="decimal")
    poxsd10_comment = fields.Char(
        string="comment", xsd_required=True,
        xsd_type="string")
    poxsd10_shipDate = fields.Date(
        string="shipDate",
        xsd_type="date")
