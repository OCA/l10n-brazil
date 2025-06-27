# Copyright 2021 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo_test_helper import FakeModelLoader

from odoo.models import NewId
from odoo.tests import TransactionCase


class TestSpecModel(TransactionCase, FakeModelLoader):
    """
    A simple usage example using the reference PurchaseOrderSchema.xsd
    https://docs.microsoft.com/en-us/visualstudio/xml-tools/sample-xsd-file-purchase-order-schema?view=vs-2019
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()

        # import a simpilified equivalent of purchase module
        from .fake_mixin import PoXsdMixin
        from .spec_poxsd import (
            Items,
            Item,
            Usaddress,
            Comment,
            PurchaseOrderType,
        )
        from .fake_odoo_purchase import (
            PurchaseOrder as FakePurchaseOrder,
            PurchaseOrderLine as FakePurchaseOrderLine,
        )
        from .spec_purchase import (
            ResPartner,
            PurchaseOrder as SpecPurchaseOrder,
            PurchaseOrderLine as SpecPurchaseOrderLine,
        )

        cls.loader.update_registry(
            (
                PoXsdMixin,
                Items,
                Item,
                Usaddress,
                Comment,
                PurchaseOrderType,
                ResPartner,
                FakePurchaseOrder,
                FakePurchaseOrderLine,
                SpecPurchaseOrder,
                SpecPurchaseOrderLine,
            )
        )

        # import generated spec mixins
        from .fake_mixin import PoXsdMixin
        from .spec_poxsd import Item, Items, PurchaseOrderType, Usaddress

        cls.loader.update_registry(
            (PoXsdMixin, Item, Items, Usaddress, PurchaseOrderType)
        )

        # inject the mixins into existing Odoo models
        from .spec_purchase import (
            PurchaseOrder as PurchaseOrder2,
            PurchaseOrderLine,
            ResPartner,
        )

        cls.loader.update_registry((ResPartner, PurchaseOrderLine, PurchaseOrder2))
        # the binding lib should be loaded in sys.modules:
        from . import purchase_order_lib  # NOQA

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super(TestSpecModel, cls).tearDownClass()

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
            set(
                self.env["fake.purchase.order"]
                ._poxsd10_stacking_points
                .keys()
            )
        )
        self.assertTrue(
            po_fields_or_stacking.issuperset(
                set(self.env["poxsd.10.purchaseordertype"]._fields.keys())
            )
        )
        self.assertEqual(
            list(
                self.env["fake.purchase.order"]
                ._poxsd10_stacking_points
                .keys()
            ),
            ["poxsd10_items"],
        )

        # let's ensure fields are remapped to their proper concrete types:
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
                "date_order": "2024-10-08",
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
        po_binding = po._build_binding(spec_schema="poxsd", spec_version="10")
        self.assertEqual(
            [s.__name__ for s in type(po_binding).mro()],
            ["PurchaseOrderType", "object"],
        )
        self.assertEqual(po_binding.bill_to.name, "Wood Corner")
        self.assertEqual(po_binding.items.item[0].product_name, "Some product desc")
        self.assertEqual(po_binding.items.item[0].quantity, 42)
        self.assertEqual(po_binding.items.item[0].usprice, "13")  # FIXME

        # 3rd we serialize po_binding as XML and check the output:
        try:
            from xsdata.formats.dataclass.serializers import XmlSerializer
            from xsdata.formats.dataclass.serializers.config import SerializerConfig

            serializer = XmlSerializer(config=SerializerConfig(indent="  "))
            xml = serializer.render(obj=po_binding, ns_map=None)
            expected_xml = """<?xml version="1.0" encoding="UTF-8"?>
<PurchaseOrderType orderDate="2024-10-08">
  <ns0:shipTo xmlns:ns0="http://tempuri.org/PurchaseOrderSchema.xsd" country="US">
    <ns0:name>Wood Corner</ns0:name>
    <ns0:street>1839 Arbor Way</ns0:street>
    <ns0:city>Turlock</ns0:city>
    <ns0:state>California</ns0:state>
    <ns0:zip>0</ns0:zip>
  </ns0:shipTo>
  <ns0:billTo xmlns:ns0="http://tempuri.org/PurchaseOrderSchema.xsd" country="US">
    <ns0:name>Wood Corner</ns0:name>
    <ns0:street>1839 Arbor Way</ns0:street>
    <ns0:city>Turlock</ns0:city>
    <ns0:state>California</ns0:state>
    <ns0:zip>0</ns0:zip>
  </ns0:billTo>
  <ns0:items xmlns:ns0="http://tempuri.org/PurchaseOrderSchema.xsd">
    <ns0:item>
      <ns0:productName>Some product desc</ns0:productName>
      <ns0:quantity>42</ns0:quantity>
      <ns0:USPrice>13</ns0:USPrice>
    </ns0:item>
  </ns0:items>
</PurchaseOrderType>
"""
            self.assertEqual(xml, expected_xml)

        except ImportError:
            _logger.error(_("xsdata Python lib not installed, skipping XML test!"))

        # 4th we import an Odoo PO from this binding object
        # first we will do a dry run import:
        imported_po_dry_run = self.env["fake.purchase.order"].build_from_binding(
            "poxsd", "10", po_binding, dry_run=True
        )
        assert isinstance(imported_po_dry_run.id, NewId)

        # now a real import:
        imported_po = self.env["fake.purchase.order"].build_from_binding(
            "poxsd", "10", po_binding
        )
        self.assertEqual(imported_po.partner_id.name, "Wood Corner")
        self.assertEqual(
            imported_po.partner_id.id, self.env.ref("base.res_partner_1").id
        )
        self.assertEqual(imported_po.order_line[0].name, "Some product desc")
