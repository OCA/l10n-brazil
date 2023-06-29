# Copyright 2020 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import re
from datetime import datetime

import nfelib
import pkg_resources
from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import TnfeProc

from odoo import api
from odoo.tests import SavepointCase

from ..models import spec_models

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
        if value is None:
            continue
        key = "%s%s" % (
            self._field_prefix,
            fspec.metadata.get("name", fname),
        )
        if (
            fspec.type == str or not any(["." in str(i) for i in fspec.type.__args__])
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
            else:
                clean_type = binding_type.lower()  # TODO double check
                comodel_name = "%s.%s.%s" % (
                    self._schema_name,
                    self._schema_version.replace(".", "")[0:2],
                    clean_type.split(".")[-1],
                )
            comodel = self.env.get(comodel_name)
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
                    lines.append((0, 0, line_vals))
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
    return comodel.new(new_value).id


spec_models.NfeSpecMixin.build_fake = build_fake
spec_models.NfeSpecMixin.build_attrs_fake = build_attrs_fake
spec_models.NfeSpecMixin.match_or_create_m2o_fake = match_or_create_m2o_fake


class NFeImportTest(SavepointCase):
    def test_import_nfe1(self):
        res_items = (
            "nfe",
            "samples",
            "v4_0",
            "leiauteNFe",
            "26180875335849000115550010000016871192213331-nfe.xml",
        )
        resource_path = "/".join(res_items)
        nfe_stream = pkg_resources.resource_stream(nfelib.__name__, resource_path)
        binding = TnfeProc.from_xml(nfe_stream.read().decode())
        nfe = (
            self.env["nfe.40.infnfe"]
            .with_context(tracking_disable=True, edoc_type="in", lang="pt_BR")
            .build_fake(binding.NFe.infNFe, create=False)
        )
        self.assertEqual(nfe.nfe40_emit.nfe40_CNPJ, "75335849000115")
        self.assertEqual(len(nfe.nfe40_det), 3)
        self.assertEqual(nfe.nfe40_det[0].nfe40_prod.nfe40_cProd, "880945")

    def test_import_nfe2(self):
        res_items = (
            "nfe",
            "samples",
            "v4_0",
            "leiauteNFe",
            "35180834128745000152550010000476491552806942-nfe.xml",
        )
        resource_path = "/".join(res_items)
        nfe_stream = pkg_resources.resource_stream(nfelib.__name__, resource_path)
        binding = TnfeProc.from_xml(nfe_stream.read().decode())
        nfe = (
            self.env["nfe.40.infnfe"]
            .with_context(tracking_disable=True, edoc_type="in", lang="pt_BR")
            .build_fake(binding.NFe.infNFe, create=False)
        )
        self.assertEqual(nfe.nfe40_emit.nfe40_CNPJ, "34128745000152")
        self.assertEqual(len(nfe.nfe40_det), 16)
        self.assertEqual(nfe.nfe40_det[0].nfe40_prod.nfe40_cProd, "1094")
