# Copyright 2020 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import dataclasses
import re
from datetime import datetime
from importlib import resources

import nfelib
from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import TnfeProc

from odoo import Command, api
from odoo.tests.common import TransactionCase

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
        value = getattr(node, fname)
        if value is None or value == []:
            continue
        key = f"nfe40_{fspec.metadata.get('name', fname)}"
        # Value-driven dispatch (see spec_driven_model): classify from the
        # runtime binding value, which is stable across xsdata annotation
        # format changes (ForwardRef, PEP 585, PEP 563).
        if isinstance(value, list):
            items = [li for li in value if li]
            is_list = bool(items) and dataclasses.is_dataclass(items[0])
            is_complex = is_list
        else:
            items = None
            is_list = False
            is_complex = dataclasses.is_dataclass(value)
        if not is_complex:
            # SimpleType
            if fields[key]["type"] == "datetime" and "T" in value:
                if tz_datetime.match(value):
                    old_value = value
                    value = old_value[:19]
                    # TODO see python3/pysped/xml_sped/base.py#L692
                # Odoo Datetime fields take naive values
                value = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")  # noqa: DTZ007
            vals[key] = value

        else:
            binding_value = items[0] if is_list else value
            binding_type = type(binding_value).__qualname__

            # ComplexType
            if fields.get(key) and fields[key].get("related"):
                key = fields[key]["related"][0]
                comodel_name = fields[key]["relation"]
            else:
                clean_type = binding_type.lower()
                comodel_name = f"nfe.40.{clean_type.split('.')[-1]}"
            comodel = self.env.get(comodel_name)
            if comodel is None:  # example skip ICMS100 class
                continue

            if not is_list:
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
                for line in items:
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


spec_mixin.NfeSpecMixin.build_fake = build_fake
spec_mixin.NfeSpecMixin.build_attrs_fake = build_attrs_fake
spec_mixin.NfeSpecMixin.match_or_create_m2o_fake = match_or_create_m2o_fake


class NFeImportTest(TransactionCase):
    def setUp(self):
        super().setUp()
        self.env = self.env(context=dict(self.env.context, tracking_disable=True))
        # the generated spec models are abstract and Odoo refuses to instantiate
        # abstract models, even as new (in memory) records: let the models of
        # this schema build new records during the test
        for name, model_cls in self.env.registry.items():
            if name.startswith("nfe.40.") and model_cls._abstract:
                self.patch(model_cls, "_abstract", False)

    def test_import_nfe1(self):
        file = (
            resources.files(nfelib)
            .joinpath("nfe")
            .joinpath("samples")
            .joinpath("v4_0")
            .joinpath("leiauteNFe")
            .joinpath("26180875335849000115550010000016871192213331-nfe.xml")
        )
        with file.open("rb") as f:
            nfe_stream = f.read()
        binding = TnfeProc.from_xml(nfe_stream.decode())
        nfe = (
            self.env["nfe.40.infnfe"]
            .with_context(tracking_disable=True, edoc_type="in")
            .build_fake(binding.NFe.infNFe, create=False)
        )
        self.assertEqual(nfe.nfe40_emit.nfe40_CNPJ, "75335849000115")
        self.assertEqual(len(nfe.nfe40_det), 3)
        self.assertEqual(nfe.nfe40_det[0].nfe40_prod.nfe40_cProd, "880945")

    def test_import_nfe2(self):
        file = (
            resources.files(nfelib)
            .joinpath("nfe")
            .joinpath("samples")
            .joinpath("v4_0")
            .joinpath("leiauteNFe")
            .joinpath("35180834128745000152550010000476491552806942-nfe.xml")
        )
        with file.open("rb") as f:
            nfe_stream = f.read()

        binding = TnfeProc.from_xml(nfe_stream.decode())
        nfe = (
            self.env["nfe.40.infnfe"]
            .with_context(tracking_disable=True, edoc_type="in")
            .build_fake(binding.NFe.infNFe, create=False)
        )
        self.assertEqual(nfe.nfe40_emit.nfe40_CNPJ, "34128745000152")
        self.assertEqual(len(nfe.nfe40_det), 16)
        self.assertEqual(nfe.nfe40_det[0].nfe40_prod.nfe40_cProd, "1094")
