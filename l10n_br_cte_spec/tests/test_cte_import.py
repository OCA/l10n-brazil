# Copyright 2020 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# flake8: noqa: C901

import re
from datetime import datetime

import nfelib
import pkg_resources
from nfelib.cte.bindings.v4_0.cte_v4_00 import Tcte

from odoo import api, fields, models
from odoo.fields import Command
from odoo.models import BaseModel, NewId
from odoo.tests import TransactionCase
from odoo.tools import OrderedSet

from ..models import spec_mixin

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
    return comodel.new(new_value)._ids[0]


# spec_mixin.CteSpecMixin._update_cache = _update_cache
spec_mixin.CteSpecMixin.build_fake = build_fake
spec_mixin.CteSpecMixin.build_attrs_fake = build_attrs_fake
spec_mixin.CteSpecMixin.match_or_create_m2o_fake = match_or_create_m2o_fake


# in version 12, 13 and 14, the code above would properly allow loading NFe XMLs
# as an Odoo AbstractModel structure for minimal testing of these structures.
# However in version Odoo 15 and 16 (at least), the ORM has trouble when
# doing env["some.model"].new(vals) if some.model is an AbstractModel like the
# models in this module. This is strange as new is available for AbstractModel...
# Anyway, only 2 methods are problematic for what we want to test here so
# a workaround is to monkey patch them as done in the next lines.
# Note that we only want test loading the XML data structure here,
# we remove the monkey patch after the tests and even if it's a dirty
# workaround it doesn't matter much because in the more completes tests in l10n_br_nfe
# we the models are made concrete so this problem does not occur anymore.
def fields_convert_to_cache(self, value, record, validate=True):
    """
    A monkey patched version of convert_to_cache that works with
    new instances of AbstractModel. Look at the lines after
    # THE NEXT LINE WAS PATCHED:
    and # THE NEXT 4 LINES WERE PATCHED:
    to see the change.
    """
    # cache format: tuple(ids)
    if isinstance(value, BaseModel):
        if validate and value._name != self.comodel_name:
            raise ValueError("Wrong value for %s: %s" % (self, value))
        ids = value._ids
        if record and not record.id:
            # x2many field value of new record is new records
            ids = tuple(it and NewId(it) for it in ids)
        return ids
    elif isinstance(value, (list, tuple)):
        # value is a list/tuple of commands, dicts or record ids
        comodel = record.env[self.comodel_name]
        # if record is new, the field's value is new records
        # THE NEXT LINE WAS PATCHED:
        if record and hasattr(record, "id") and not record.id:
            browse = lambda it: comodel.browse([it and NewId(it)])
        else:
            browse = comodel.browse
        # determine the value ids
        ids = OrderedSet(record[self.name]._ids if validate else ())
        # modify ids with the commands
        for command in value:
            if isinstance(command, (tuple, list)):
                if command[0] == Command.CREATE:
                    # THE NEXT 4 LINES WERE PATCHED:
                    if hasattr(comodel.new(command[2], ref=command[1]), "id"):
                        ids.add(comodel.new(command[2], ref=command[1]).id)
                    else:
                        ids.add(comodel.new(command[2], ref=command[1])._ids[0])
                elif command[0] == Command.UPDATE:
                    line = browse(command[1])
                    if validate:
                        line.update(command[2])
                    else:
                        line._update_cache(command[2], validate=False)
                    ids.add(line.id)
                elif command[0] in (Command.DELETE, Command.UNLINK):
                    ids.discard(browse(command[1]).id)
                elif command[0] == Command.LINK:
                    ids.add(browse(command[1]).id)
                elif command[0] == Command.CLEAR:
                    ids.clear()
                elif command[0] == Command.SET:
                    ids = OrderedSet(browse(it).id for it in command[2])
            elif isinstance(command, dict):
                ids.add(comodel.new(command).id)
            else:
                ids.add(browse(command).id)
        # return result as a tuple
        return tuple(ids)
    elif not value:
        return ()
    raise ValueError("Wrong value for %s: %s" % (self, value))


fields_convert_to_cache._original_method = fields._RelationalMulti.convert_to_cache
fields._RelationalMulti.convert_to_cache = fields_convert_to_cache


def models_update_cache(self, values, validate=True):
    """
    A monkey patched version of _update_cache that works with
    new instances of AbstractModel. Look at the lines after
    # THE NEXT LINE WAS PATCHED:
    to see the change.
    """
    self.ensure_one()
    cache = self.env.cache
    fields = self._fields
    try:
        field_values = [(fields[name], value) for name, value in values.items()]
    except KeyError as e:
        raise ValueError("Invalid field %r on model %r" % (e.args[0], self._name))
    # convert monetary fields after other columns for correct value rounding
    for field, value in sorted(field_values, key=lambda item: item[0].write_sequence):
        cache.set(self, field, field.convert_to_cache(value, self, validate))
        # set inverse fields on new records in the comodel
        if field.relational:
            # THE NEXT LINE WAS PATCHED:
            inv_recs = self[field.name].filtered(
                lambda r: hasattr(r, "id") and not r.id
            )
            if not inv_recs:
                continue
            for invf in self.pool.field_inverses[field]:
                # DLE P98: `test_40_new_fields`
                # /home/dle/src/odoo/master-nochange-fp/odoo/addons/test_new_api/tests/test_new_fields.py
                # Be careful to not break `test_onchange_taxes_1`, `test_onchange_taxes_2`, `test_onchange_taxes_3`
                # If you attempt to find a better solution
                for inv_rec in inv_recs:
                    if not cache.contains(inv_rec, invf):
                        val = invf.convert_to_cache(self, inv_rec, validate=False)
                        cache.set(inv_rec, invf, val)
                    else:
                        invf._update(inv_rec, self)


models_update_cache._original_method = models.BaseModel._update_cache
models.BaseModel._update_cache = models_update_cache


class NFeImportTest(TransactionCase):
    @classmethod
    def tearDownClass(cls):
        fields._RelationalMulti.convert_to_cache = (
            fields_convert_to_cache._original_method
        )
        models.BaseModel._update_cache = models_update_cache._original_method
        super().tearDownClass()

    def test_import_cte(self):
        res_items = (
            "cte",
            "samples",
            "v4_0",
            "43120178408960000182570010000000041000000047-cte.xml",
        )
        resource_path = "/".join(res_items)
        cte_stream = pkg_resources.resource_stream(nfelib.__name__, resource_path)
        binding = Tcte.from_xml(cte_stream.read().decode())
        cte = (
            self.env["cte.40.tcte_infcte"]
            .with_context(tracking_disable=True, edoc_type="in", lang="pt_BR")
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
