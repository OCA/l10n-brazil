# Copyright 2020 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import re
from datetime import datetime

import nfelib
import pkg_resources
from nfelib.v4_00 import leiauteNFe_sub as nfe_sub

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
    fields = self.fields_get()
    vals = self.default_get(fields.keys())
    for attr in node.member_data_items_:
        value = getattr(node, attr.get_name())
        if value is None:
            continue
        key = "nfe40_%s" % (attr.get_name(),)
        if (
            attr.get_child_attrs().get("type") is None
            or attr.get_child_attrs().get("type") == "xs:string"
        ):
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
            # ComplexType
            if fields.get(key) and fields[key].get("related"):
                key = fields[key]["related"][0]
                comodel_name = fields[key]["relation"]
            else:
                clean_type = attr.get_child_attrs()["type"].replace("Type", "").lower()
                comodel_name = "nfe.40.%s" % (clean_type,)
            comodel = self.env.get(comodel_name)
            if comodel is None:  # example skip ICMS100 class
                continue

            if attr.get_container() == 0:
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
            elif attr.get_container() == 1:
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
            "..",
            "tests",
            "nfe",
            "v4_00",
            "leiauteNFe",
            "26180812984794000154550010000016871192213339-nfe.xml",
        )
        resource_path = "/".join(res_items)
        nfe_stream = pkg_resources.resource_stream(nfelib.__name__, resource_path)
        nfe_binding = nfe_sub.parse(nfe_stream, silence=True)
        nfe = self.env["nfe.40.infnfe"].build_fake(nfe_binding.infNFe, create=False)
        self.assertEqual(nfe.nfe40_emit.nfe40_CNPJ, "75335849000115")
        self.assertEqual(len(nfe.nfe40_det), 3)
        self.assertEqual(nfe.nfe40_det[0].nfe40_prod.nfe40_cProd, "880945")

    def test_import_nfe2(self):
        res_items = (
            "..",
            "tests",
            "nfe",
            "v4_00",
            "leiauteNFe",
            "35180803102452000172550010000476491552806942-nfe.xml",
        )
        resource_path = "/".join(res_items)
        nfe_stream = pkg_resources.resource_stream(nfelib.__name__, resource_path)
        nfe_binding = nfe_sub.parse(nfe_stream, silence=True)
        nfe = self.env["nfe.40.infnfe"].build_fake(nfe_binding.infNFe, create=False)
        self.assertEqual(nfe.nfe40_emit.nfe40_CNPJ, "34128745000152")
        self.assertEqual(len(nfe.nfe40_det), 16)
        self.assertEqual(nfe.nfe40_det[0].nfe40_prod.nfe40_cProd, "1094")
