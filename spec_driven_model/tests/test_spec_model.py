# Copyright 2021 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# pylint: disable=reimported

import logging

from unittest.mock import patch

from odoo.tools import mute_logger

from odoo_test_helper import FakeModelLoader

from odoo.models import MetaModel, NewId
from odoo.tests import TransactionCase

_logger = logging.getLogger(__name__)


class TestSpecModel(TransactionCase, FakeModelLoader):
    """
    A simple usage example using the reference PurchaseOrderSchema.xsd
    https://docs.microsoft.com/en-us/visualstudio/xml-tools/sample-xsd-file-purchase-order-schema?view=vs-2019
    """

    def setUp(self):
        super().setUp()
        self.loader = FakeModelLoader(self.env, self.__module__)
        self.loader.backup_registry()

        # import a simpilified equivalent of purchase module
        from .fake_mixin import PoXsdMixin
        from .fake_odoo_purchase import (
            PurchaseOrder as FakePurchaseOrder,
        )
        from .fake_odoo_purchase import (
            PurchaseOrderLine as FakePurchaseOrderLine,
        )
        from .spec_poxsd import (
            Comment,
            Item,
            Items,
            PurchaseOrderType,
            Usaddress,
        )
        from .spec_purchase import (
            PurchaseOrder as SpecPurchaseOrder,
        )
        from .spec_purchase import (
            PurchaseOrderLine as SpecPurchaseOrderLine,
        )
        from .spec_purchase import (
            ResPartner,
        )

        # a downstream _inherit extension of the remaining model poxsd.10.comment
        # (mirrors l10n_br_account_nfe extending nfe.40.detpag, see issue #4668)
        from .fake_comment_extension import CommentExtension

        self.loader.update_registry(
            (
                PoXsdMixin,
                Items,
                Item,
                Usaddress,
                Comment,
                CommentExtension,
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

        self.loader.update_registry(
            (PoXsdMixin, Item, Items, Usaddress, PurchaseOrderType)
        )

        # inject the mixins into existing Odoo models
        from .spec_purchase import (
            PurchaseOrder as PurchaseOrder2,
        )
        from .spec_purchase import (
            PurchaseOrderLine,
            ResPartner,
        )

        self.loader.update_registry((ResPartner, PurchaseOrderLine, PurchaseOrder2))
        self.addCleanup(self.loader.restore_registry)
        # the binding lib should be loaded in sys.modules:
        from . import purchase_order_lib  # NOQA

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

    def test_fix_camel_case(self):
        partner = self.env["res.partner"]
        self.assertEqual(partner.fix_camel_case(""), "")
        self.assertEqual(partner.fix_camel_case("PedRegEvento"), "PedRegEvento")
        self.assertEqual(partner.fix_camel_case("TcinfDPS"), "TcinfDps")

    def test_stacked_model(self):
        po_fields_or_stacking = set(self.env["fake.purchase.order"]._fields.keys())
        po_fields_or_stacking.update(
            set(self.env["fake.purchase.order"]._poxsd10_stacking_points.keys())
        )
        self.assertTrue(
            po_fields_or_stacking.issuperset(
                set(self.env["poxsd.10.purchaseordertype"]._fields.keys())
            )
        )
        self.assertEqual(
            list(self.env["fake.purchase.order"]._poxsd10_stacking_points.keys()),
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
            _logger.error("xsdata Python lib not installed, skipping XML test!")

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

    def test_polymorphic_comodel_from_binding_type(self):
        binding_type = "Cte.Tcte.Ide"
        expected_model_name = "cte.40.ide"
        # in the l10n_br_cte module tcte_ide is actually expected
        # but expecting the last combo here allows us to check the iterations/combos
        available_models = {expected_model_name: "Found Fallback Model"}

        method_path = (
            "odoo.addons.spec_driven_model.models.spec_mixin."
            "SpecMixin._get_concrete_model"
        )
        with patch(method_path) as mock_get_concrete_model:
            mock_get_concrete_model.side_effect = lambda name: available_models.get(
                name
            )
            model_instance = self.env["spec.mixin"].with_context(
                spec_schema="cte", spec_version="40"
            )
            result = model_instance._comodel_from_binding_type(binding_type)

        assert result == "Found Fallback Model"

        # Check the full sequence of calls.
        actual_calls = [c.args[0] for c in mock_get_concrete_model.call_args_list]
        expected_model_suffixes = [
            "cte.40.cte_ide",
            "cte.40.cte_tcte_ide",
            "cte.40.ide",  # This is the one that should be found (in this test)
        ]

        assert actual_calls == expected_model_suffixes
        assert mock_get_concrete_model.call_count == len(expected_model_suffixes)

    def test_remaining_model_cleanup_survives_an_exception(self):
        """The module_to_models cleanup must run even when the hook raises.

        The cleanup that fixes #4668 sits at the end of
        _register_remaining_schema_models_hook, after init_models. Any exception
        raised in that window -- init_models recomputing a field that a
        downstream module broke, for instance -- used to skip the cleanup and
        leave the synthesized concrete class in MetaModel.module_to_models. From
        then on every registry build in the process fed that class back as a
        base of (SpecModel, ...) and died with an inconsistent MRO, so a single
        transient error turned into a server that could not rebuild its registry
        until the process was restarted.
        """
        from unittest import mock

        from odoo.models import MetaModel, is_definition_class
        from odoo.modules.registry import Registry

        from odoo.addons.spec_driven_model.models.spec_models import SpecModel

        from .fake_mixin import PoXsdMixin
        from .spec_poxsd import Comment

        registry = self.env.registry
        cr = self.env.cr
        module_to_models = MetaModel.module_to_models

        def concrete_classes_left():
            return [
                cls
                for cls in module_to_models["spec_driven_model"]
                if is_definition_class(cls)
                and issubclass(cls, SpecModel)
                and cls._name == "poxsd.10.comment"
            ]

        original_init_models = Registry.init_models

        def failing_init_models(self, cr, model_names, context, install=True):
            if any(name.startswith("poxsd.10.") for name in model_names):
                raise AttributeError("simulated failure inside the hook window")
            return original_init_models(self, cr, model_names, context, install)

        ready = registry.ready
        saved_module_classes = list(module_to_models["spec_driven_model"])
        try:
            registry.__dict__.pop("_poxsd_register_hook_loaded", None)
            self.loader.update_registry((PoXsdMixin, Comment))
            registry.ready = True
            with mock.patch.object(Registry, "init_models", failing_init_models):
                with self.assertRaises(AttributeError):
                    registry.setup_models(cr)

            self.assertEqual(
                concrete_classes_left(),
                [],
                "the hook leaked a concrete class after raising; the next "
                "registry build would crash with an inconsistent MRO (#4668)",
            )
        finally:
            module_to_models["spec_driven_model"] = saved_module_classes
            registry.ready = ready
            registry.__dict__.pop("_poxsd_register_hook_loaded", None)

    def test_registry_reload_with_extended_remaining_model(self):
        """Regression test for issue #4668.

        _register_remaining_schema_models_hook turns *remaining* spec models
        (those not injected into a concrete Odoo model, e.g. poxsd.10.comment
        or nfe.40.detpag) into concrete models by building a class
        ``type(name, (SpecModel, *definition_bases))``. A real server rebuilds
        the whole registry (``Registry.new``) on every module install/update.
        If that concrete class lingers in ``MetaModel.module_to_models``, that
        rebuild re-consumes it as a stale base of the model; being a subclass of
        the very classes that extend the model via ``_inherit`` (here
        CommentExtension, like l10n_br_account_nfe for nfe.40.detpag), Odoo
        accumulates it after the extension and ``setup_models`` crashes with
        "Cannot create a consistent method resolution order".
        """
        from unittest import mock

        from odoo_test_helper.fake_model_loader import FakePackage

        from odoo.models import MetaModel, is_definition_class

        from odoo.addons.spec_driven_model.models.spec_models import SpecModel

        from .fake_comment_extension import CommentExtension
        from .fake_mixin import PoXsdMixin
        from .spec_poxsd import Comment

        registry = self.env.registry
        cr = self.env.cr
        module_to_models = MetaModel.module_to_models

        def concrete_classes_left():
            # the concrete class the hook builds for poxsd.10.comment is a
            # SpecModel subclass named after the model (the genuine definition
            # classes -- Comment, CommentExtension -- are plain AbstractModels)
            return [
                cls
                for cls in module_to_models["spec_driven_model"]
                if is_definition_class(cls)
                and issubclass(cls, SpecModel)
                and cls._name == "poxsd.10.comment"
            ]

        def clear_hook_guard():
            # a fresh Registry.new() has no per-schema guard, so the hook runs
            registry.__dict__.pop("_poxsd_register_hook_loaded", None)

        ready = registry.ready
        saved_module_classes = list(module_to_models["spec_driven_model"])
        try:
            # build #1: rebuild the remaining model and its downstream _inherit
            # extension as abstract mixins, then run setup_models() so the hook
            # builds the concrete poxsd.10.comment (setup_models only runs
            # the registry hooks when the registry is ready, as after a real
            # module load). On a real server this concrete class stays
            # registered in module_to_models across registry rebuilds; the fix
            # must not leave it there.
            clear_hook_guard()
            self.loader.update_registry((PoXsdMixin, Comment, CommentExtension))
            registry.ready = True
            registry.setup_models(cr)

            self.assertEqual(
                concrete_classes_left(),
                [],
                "the hook left a concrete class in module_to_models; "
                "the next Registry.new() would rebuild it as a stale base and "
                "crash with an inconsistent MRO (#4668)",
            )

            # build #2: mimic the next Registry.new() -- re-consume
            # module_to_models and re-run setup_models() without scrubbing it
            # first (as a real server does). Were a stale concrete class
            # present, Odoo would rebuild it as a base of poxsd.10.comment and
            # raise "Cannot create a consistent method resolution order".
            clear_hook_guard()
            with mock.patch.object(cr, "commit"):
                registry.load(cr, FakePackage("spec_driven_model"))
                registry.setup_models(cr)
        finally:
            module_to_models["spec_driven_model"] = saved_module_classes
            registry.ready = ready

    def test_spec_prefix_without_schema_answers_a_single_value(self):
        """`_spec_prefix()` answers one value when asked for one."""
        model = self.env["spec.mixin"].with_context(
            spec_schema=False, spec_version=False
        )
        self.assertIsNone(model._spec_prefix())
        self.assertEqual(model._spec_prefix(split=True), (None, None))

    def test_model_without_odoo_module_does_not_break_the_registry(self):
        """A prefix that resolves without a spec module must not abort the load."""
        model = self.env["spec.mixin"].with_context(
            spec_schema="nosuch", spec_version="10"
        )
        self.assertEqual(model._spec_prefix(), "nosuch10")
        self.assertIsNone(model._get_spec_property("odoo_module"))
        self.assertIsNone(model._register_remaining_schema_models_hook())
        self.assertFalse(
            hasattr(self.env.registry, "_nosuch_register_hook_loaded"),
            "the model with no spec module consumed the load key of the schema",
        )

    def _clear_poxsd_hook_guard(self):
        # a fresh Registry.new() has no per-schema guard, so the hook runs;
        # here we clear it to run the hook again inside a single test process
        self.env.registry.__dict__.pop("_poxsd_register_hook_loaded", None)

    def test_hook_read_only_on_ordinary_registry_load(self):
        """hook v2: an ordinary registry load performs zero reflection writes.

        _register_remaining_schema_models_hook runs on every registry load
        (every ``Registry.new``). It must always rebuild the Python classes of
        the *remaining* spec models (poxsd.10.comment here, nfe.40.detpag/det/...
        in l10n_br_nfe) in memory, but reflecting them into the database (via
        ``registry.init_models``, plus ir.model.access and the ir.model.data
        magic-field create/unlink cycle) only has to happen on install/update.
        Once the models are reflected, a subsequent ordinary load (server boot,
        a fresh worker's own registry, a second ``Registry.new`` for another
        database on a dbfilter instance) must be read-only: it must NOT call
        ``init_models`` for the remaining models again -- that is the write
        churn concurrent workers race on (duplicate key / serialization /
        deadlock on ir_model_data). This is the write-churn sibling of the
        class-leak fixes #4664/#4670 and the successor of #3809.

        The hook cannot be invoked twice by hand on a live registry (the second
        build would consume the concrete class the first one left among the
        model bases and crash with an inconsistent MRO -- exactly #4668), so we
        drive it through real registry rebuilds like
        ``test_registry_reload_with_extended_remaining_model`` does, and spy on
        ``registry.init_models`` to see whether the hook reflected the remaining
        models on each rebuild.
        """
        from unittest import mock

        from odoo_test_helper.fake_model_loader import FakePackage

        from .fake_comment_extension import CommentExtension
        from .fake_mixin import PoXsdMixin
        from .spec_poxsd import Comment

        registry = self.env.registry
        cr = self.env.cr

        real_init_models = registry.init_models
        # setup_models() never calls init_models(); within a registry rebuild
        # the only caller reflecting poxsd.10.comment is our hook, so this spy
        # captures exactly the hook's reflection.
        reflected = []

        def spy_init_models(cr_, model_names, context, install=True):
            if "poxsd.10.comment" in set(model_names):
                reflected.append(list(model_names))
            return real_init_models(cr_, model_names, context, install)

        ready = registry.ready
        saved_updated_modules = registry.updated_modules
        saved_module_classes = list(MetaModel.module_to_models["spec_driven_model"])
        try:
            # rebuild #1 -- install/update in progress: the hook must reflect the
            # remaining model, whatever how the test db was built
            registry.updated_modules = ["spec_driven_model"]
            self._clear_poxsd_hook_guard()
            self.loader.update_registry((PoXsdMixin, Comment, CommentExtension))
            registry.ready = True
            with mock.patch.object(
                registry, "init_models", side_effect=spy_init_models
            ):
                registry.setup_models(cr)
            self.assertTrue(
                reflected,
                "sanity: on an install/update the hook must reflect the "
                "remaining models (else the read-only assertion below is void)",
            )

            # rebuild #2 -- an ordinary registry load (nothing installed or
            # updated): the hook must NOT reflect the remaining models again.
            reflected.clear()
            registry.updated_modules = []
            self._clear_poxsd_hook_guard()
            with mock.patch.object(
                registry, "init_models", side_effect=spy_init_models
            ), mock.patch.object(cr, "commit"):
                registry.load(cr, FakePackage("spec_driven_model"))
                registry.setup_models(cr)
            self.assertEqual(
                reflected,
                [],
                "an ordinary registry load re-reflected the remaining spec "
                "models (called init_models); it must be read-only once they "
                "are reflected, or concurrent workers race the same "
                "ir_model_data writes on a dbfilter instance",
            )
        finally:
            MetaModel.module_to_models["spec_driven_model"] = saved_module_classes
            registry.updated_modules = saved_updated_modules
            registry.ready = ready
            self._clear_poxsd_hook_guard()

    def test_reflection_needed_signals(self):
        """hook v2 guard: _spec_reflection_needed picks the full (writing) path
        exactly when it must -- while a module is installing/updating, and (the
        essential safety net) whenever a concrete remaining model is not yet
        backed by its SQL table -- and only then. This is what keeps
        install/update (and the pre-STEP-9 post_init_hook load, where a CT-e
        import builds cte.40.infoutros before its table exists) on the full path
        while letting the ordinary boot skip it.
        """
        registry = self.env.registry
        hook_model = self.env["spec.mixin.poxsd"]
        # a table that certainly exists, and one that certainly does not
        existing_table = self.env["ir.model"]._table  # "ir_model"
        missing_table = "poxsd_10_does_not_exist"

        saved_updated_modules = registry.updated_modules
        try:
            # a module install/update in progress always forces the full path,
            # even when every concrete table is already present
            registry.updated_modules = ["spec_driven_model"]
            self.assertTrue(
                hook_model._spec_reflection_needed([existing_table]),
                "an install/update in progress must take the full "
                "reflection path",
            )

            # ordinary load with a concrete table still missing -> full path. This is
            # the CI #4718 case: l10n_br_cte's post_init_hook runs the hook before
            # STEP 9, and reflecting is mandatory or the import INSERT fails
            registry.updated_modules = []
            self.assertTrue(
                hook_model._spec_reflection_needed([existing_table, missing_table]),
                "a concrete remaining model without its SQL table must fall "
                "back to the full reflection path",
            )

            # ordinary load with every concrete table present -> read-only
            self.assertFalse(
                hook_model._spec_reflection_needed([existing_table]),
                "with every concrete table present the load must be read-only",
            )

            # ordinary load with no concrete tables at all -> nothing to reflect
            self.assertFalse(
                hook_model._spec_reflection_needed([]),
                "with no concrete remaining models there is nothing to reflect",
            )
        finally:
            registry.updated_modules = saved_updated_modules
