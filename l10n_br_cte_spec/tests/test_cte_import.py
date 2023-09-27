# Copyright 2020 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import re
from datetime import datetime

import nfelib
import pkg_resources
from nfelib.cte.bindings.v4_0.cte_v4_00 import Cte
from xsdata.formats.dataclass.parsers import XmlParser

from odoo import api
from odoo.tests import TransactionCase

from ..models import spec_models

tz_datetime = re.compile(r".*[-+]0[0-9]:00$")


@api.model
def build_fake(self, node, create=False):
    attrs = self.build_attrs_fake(node, create_m2o=True)
    return self.new(attrs)


# flake8: noqa: C901
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
        key = "%s%s" % (
            self._field_prefix,
            fname,
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


# spec_models.CteSpecMixin._update_cache = _update_cache
spec_models.CteSpecMixin.build_fake = build_fake
spec_models.CteSpecMixin.build_attrs_fake = build_attrs_fake
spec_models.CteSpecMixin.match_or_create_m2o_fake = match_or_create_m2o_fake


class CTeImportTest(TransactionCase):
    def test_import_cte(self):
        res_items = (
            "cte",
            "samples",
            "v4_0",
            "43120178408960000182570010000000041000000047-cte.xml",
        )
        resource_path = "/".join(res_items)
        nfe_stream = pkg_resources.resource_stream(nfelib.__name__, resource_path)
        parser = XmlParser()
        binding = parser.from_string(nfe_stream.read().decode(), Cte)
        cte = self.env["cte.40.tcte"].build_fake(binding, create=False)
        self.assertEqual(cte.cte40_infCte.cte40_emit.cte40_CNPJ, "78408960000182")
