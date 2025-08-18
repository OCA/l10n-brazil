# Copyright 2020 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# flake8: noqa: C901

import re
from datetime import datetime
from importlib import resources

import nfelib
from nfelib.cte.bindings.v4_0.cte_v4_00 import Tcte
from odoo_test_helper import FakeModelLoader

from odoo import Command, api, models
from odoo.tests import TransactionCase

from odoo.addons.l10n_br_cte_spec.models.v4_0 import cte_tipos_basico_v4_00

from ..models import spec_mixin

tz_datetime = re.compile(r".*[-+]0[0-9]:00$")


@api.model
def build_fake(self, node, create=False):
    attrs = self.build_attrs_fake(node, create_m2o=True)
    return self.new(attrs)


@api.model
def build_attrs_fake(self, node, create_m2o=False):
    """
    Similar to build_attrs from spec_driven_model but simpler: assuming
    generated abstract mixins are not injected into concrete Odoo models.
    """
    fields = self.fields_get()
    vals = self.default_get(fields.keys())
    for fname, fspec in node.__dataclass_fields__.items():
        if fname == "any_element":  # FIXME in spec_driven_model
            continue
        value = getattr(node, fname)
        if value is None:
            continue
        key = f"{self._field_prefix}{fname}"
        if (
            fspec.type is str or not any(["." in str(i) for i in fspec.type.__args__])
        ) and not str(fspec.type).startswith("typing.List"):
            # SimpleType
            if fields[key]["type"] == "datetime":
                if "T" in value:
                    if tz_datetime.match(value):
                        old_value = value
                        value = old_value[:19]
                        # TODO see python3/pysped/xml_sped/base.py#L692
                    value = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
            vals[key] = value

        else:
            if hasattr(fspec.type.__args__[0], "__name__"):
                binding_type = fspec.type.__args__[0].__name__
            else:
                binding_type = fspec.type.__args__[0].__forward_arg__

            # ComplexType
            if fields.get(key) and fields[key].get("related"):
                key = fields[key]["related"][0]
                comodel_name = fields[key]["relation"]
                comodel = self.env.get(comodel_name)
            elif fields.get(key) and fields[key].get("relation"):
                comodel_name = fields[key]["relation"]
                comodel = self.env.get(comodel_name)
            else:
                comodel = None
                for name in self.env.keys():
                    if (
                        hasattr(self.env[name], "_binding_type")
                        and self.env[name]._binding_type == binding_type
                    ):
                        comodel = self.env[name]
            if comodel is None:  # example skip ICMS100 class
                continue

            if not str(fspec.type).startswith("typing.List"):
                # m2o
                new_value = comodel.build_attrs_fake(
                    value,
                    create_m2o=create_m2o,
                )
                if new_value is None:
                    continue
                if comodel._name == self._name:  # stacked m2o
                    vals.update(new_value)
                else:
                    vals[key] = self.match_or_create_m2o_fake(
                        comodel, new_value, create_m2o
                    )
            else:  # if attr.get_container() == 1:
                # o2m
                lines = []
                for line in [li for li in value if li]:
                    line_vals = comodel.build_attrs_fake(line, create_m2o=create_m2o)
                    lines.append(Command.create(line_vals))
                vals[key] = lines

    for k, v in fields.items():
        if (
            v.get("related") is not None
            and len(v["related"]) == 1
            and vals.get(k) is not None
        ):
            vals[v["related"][0]] = vals.get(k)

    return vals


@api.model
def match_or_create_m2o_fake(self, comodel, new_value, create_m2o=False):
    return comodel.new(new_value)._ids[0]


spec_mixin.CteSpecMixin.build_fake = build_fake
spec_mixin.CteSpecMixin.build_attrs_fake = build_attrs_fake
spec_mixin.CteSpecMixin.match_or_create_m2o_fake = match_or_create_m2o_fake


class NFeImportTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()

        # Get all classes from the module that inherit from AbstractModel
        modified_classes = []
        for _name, obj in vars(cte_tipos_basico_v4_00).items():
            if isinstance(obj, type) and models.AbstractModel in obj.__bases__:
                # Create new bases tuple with Model added
                new_bases = (models.Model,) + obj.__bases__

                # Create new class with same attributes but modified bases
                modified_class = type(obj.__name__, new_bases, dict(obj.__dict__))

                # Replace original class in module
                modified_classes.append(modified_class)
                cls.loader.update_registry(modified_classes)

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    def test_import_cte(self):
        file = (
            resources.files(nfelib)
            .joinpath("cte")
            .joinpath("samples")
            .joinpath("v4_0")
            .joinpath("43120178408960000182570010000000041000000047-cte.xml")
        )
        with file.open("rb") as f:
            cte_stream = f.read()

        binding = Tcte.from_xml(cte_stream.decode())
        cte = (
            self.env["cte.40.tcte_infcte"]
            .with_context(tracking_disable=True, edoc_type="in")
            .build_fake(binding.infCte, create=False)
        )
        self.assertEqual(cte.cte40_emit.cte40_xNome, "KERBER E CIA. LTDA.")

        self.assertEqual(cte.cte40_ide.cte40_cCT, "00000004")
        self.assertEqual(
            cte.cte40_Id, "CTe43120178408960000182570010000000041000000047"
        )

        self.assertEqual(cte.cte40_emit.cte40_CNPJ, "78408960000182")
        self.assertEqual(cte.cte40_receb.cte40_CNPJ, "81639791000104")

        self.assertEqual(cte.cte40_exped.cte40_CNPJ, "78408960000182")
        self.assertEqual(cte.cte40_dest.cte40_CNPJ, "81639791000104")

        self.assertEqual(
            cte.cte40_infCTeNorm.cte40_infCarga.cte40_proPred, "Pedra Brita"
        )
