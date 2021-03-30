# Copyright 2021 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo.models import NewId
from odoo.tests import SavepointCase
from odoo_test_helper import FakeModelLoader
from ..hooks import get_remaining_spec_models


class TestSpecModel(SavepointCase, FakeModelLoader):
    """
    A simple usage example using the reference PurchaseOrderSchema.xsd
    https://docs.microsoft.com/en-us/visualstudio/xml-tools/sample-xsd-file-purchase-order-schema?view=vs-2019
    """

    @classmethod
    def setUpClass(cls):
        super(TestSpecModel, cls).setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()

        # import a simpilified equivalend of purchase module
        from .fake_odoo_purchase import (
            PurchaseOrder as FakePurchaseOrder,
            PurchaseOrderLine as FakePurchaseOrderLine,
        )

        cls.loader.update_registry((FakePurchaseOrder, FakePurchaseOrderLine))

        # import generated spec mixins
        from .fake_mixin import PoXsdMixin
        from .spec_poxsd import (
            Item,
            Items,
            USAddress,
            PurchaseOrder,
        )

        cls.loader.update_registry((PoXsdMixin, Item, Items, USAddress, PurchaseOrder))

        # inject the mixins into existing Odoo models
        from .spec_purchase import (
            ResPartner,
            PurchaseOrderLine,
            PurchaseOrder as PurchaseOrder2,
        )

        cls.loader.update_registry((ResPartner, PurchaseOrderLine, PurchaseOrder2))
        # the binding lib should be loaded in sys.modules:
        from . import purchase_order_lib  # NOQA

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super(TestSpecModel, cls).tearDownClass()

    def test_loading_hook(self):
        remaining_spec_models = get_remaining_spec_models(
            self.env.cr,
            self.env.registry,
            "spec_driven_model",
            "odoo.addons.spec_driven_model.tests.spec_poxsd",
        )
        self.assertEqual(remaining_spec_models, set(["poxsd.10.dangling_model"]))

    def test_spec_models(self):
        self.assertTrue(
            set(self.env["res.partner"]._fields.keys()).issuperset(
                set(self.env["poxsd.10.usaddress"]._fields.keys())
            )
        )

        self.assertTrue(
            set(self.env["fake.purchase.order.line"]._fields.keys()).issuperset(
                set(self.env["poxsd.10.item"]._fields.keys())
            )
        )

    def test_stacked_model(self):
        po_fields_or_stacking = set(self.env["fake.purchase.order"]._fields.keys())
        po_fields_or_stacking.update(
            set(self.env["fake.purchase.order"]._stacking_points.keys())
        )
        self.assertTrue(
            po_fields_or_stacking.issuperset(
                set(self.env["poxsd.10.purchaseorder"]._fields.keys())
            )
        )
        self.assertEqual(
            list(self.env["fake.purchase.order"]._stacking_points.keys()),
            ["poxsd10_items"],
        )

        # let's ensure fields are remapṕed to their proper concrete types:
        self.assertEqual(
            self.env["fake.purchase.order"]._fields["poxsd10_shipTo"].comodel_name,
            "res.partner",
        )
        self.assertEqual(
            self.env["fake.purchase.order"]._fields["poxsd10_billTo"].comodel_name,
            "res.partner",
        )

        self.assertEqual(
            self.env["fake.purchase.order"]._fields["poxsd10_item"].comodel_name,
            "fake.purchase.order.line",
        )

    def test_create_export_import(self):

        # 1st we create an Odoo PO:
        po = self.env["fake.purchase.order"].create(
            {
                "name": "PO XSD",
                "partner_id": self.env.ref("base.res_partner_1").id,
                "dest_address_id": self.env.ref("base.res_partner_1").id,
            }
        )
        self.env["fake.purchase.order.line"].create(
            {
                "name": "Some product desc",
                "product_qty": 42,
                "price_unit": 13,
                "order_id": po.id,
            }
        )

        # 2nd we serialize it into a binding object:
        # (that could be further XML serialized)
        po_binding = po._build_generateds()
        self.assertEqual(po_binding.billTo.name, "Wood Corner")
        self.assertEqual(po_binding.items.item[0].productName, "Some product desc")
        self.assertEqual(po_binding.items.item[0].quantity, 42)
        self.assertEqual(po_binding.items.item[0].USPrice, "13")  # FIXME

        # 3rd we import an Odoo PO from this binding object
        # first we will do a dry run import:
        imported_po_dry_run = self.env["fake.purchase.order"].build(
            po_binding, dry_run=True
        )
        assert isinstance(imported_po_dry_run.id, NewId)

        # now a real import:
        imported_po = self.env["fake.purchase.order"].build(po_binding)
        self.assertEqual(imported_po.partner_id.name, "Wood Corner")
        self.assertEqual(
            imported_po.partner_id.id, self.env.ref("base.res_partner_1").id
        )
        self.assertEqual(imported_po.order_line[0].name, "Some product desc")
