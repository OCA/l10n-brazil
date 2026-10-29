# Copyright 2020 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# Copyright 2026 KMEE
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# flake8: noqa: C901

import dataclasses
import re
from datetime import datetime
from importlib import resources

import nfelib
from nfelib.nfse.bindings.v1_0.dps_v1_00 import Dps

from odoo import Command, api
from odoo.tests import TransactionCase

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
        if value is None or value == []:
            continue
        key = f"nfse10_{fspec.metadata.get('name', fname)}"
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
            if fields[key]["type"] == "datetime":
                if "T" in value:
                    if tz_datetime.match(value):
                        old_value = value
                        value = old_value[:19]
                        # TODO see python3/pysped/xml_sped/base.py#L692
                    value = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
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
                comodel_name = f"nfse.10.{clean_type.split('.')[-1]}"
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


spec_mixin.NfseSpecMixin.build_fake = build_fake
spec_mixin.NfseSpecMixin.build_attrs_fake = build_attrs_fake
spec_mixin.NfseSpecMixin.match_or_create_m2o_fake = match_or_create_m2o_fake


class NFSeImportTest(TransactionCase):
    # the generated spec models are abstract: the test builds them as new
    # (in memory) records, which does not require concrete models
    def setUp(self):
        super().setUp()
        self.env = self.env(context=dict(self.env.context, tracking_disable=True))

    def _import_dps(self, file_name):
        file = (
            resources.files(nfelib)
            .joinpath("nfse")
            .joinpath("samples")
            .joinpath("v1_0")
            .joinpath(file_name)
        )
        with file.open("rb") as f:
            dps_stream = f.read()
        binding = Dps.from_xml(dps_stream.decode())
        return (
            self.env["nfse.10.tcinfdps"]
            .with_context(tracking_disable=True, edoc_type="in")
            .build_fake(binding.infDPS, create=False)
        )

    def test_import_dps_simples(self):
        dps = self._import_dps("dps-simples.xml")
        self.assertEqual(dps.nfse10_nDPS, "6")
        self.assertEqual(dps.nfse10_prest.nfse10_CNPJ, "01761135000132")
        self.assertEqual(dps.nfse10_serv.nfse10_cServ.nfse10_cTribNac, "010101")

    def test_import_dps_regime_normal(self):
        dps = self._import_dps("dps-regime-normal.xml")
        self.assertEqual(dps.nfse10_nDPS, "2")
        self.assertEqual(dps.nfse10_prest.nfse10_CNPJ, "00000000000000")
        self.assertEqual(dps.nfse10_serv.nfse10_cServ.nfse10_cTribNac, "010101")
