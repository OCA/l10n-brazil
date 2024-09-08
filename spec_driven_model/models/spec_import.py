# Copyright 2019-2020 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import dataclasses
import inspect
import logging
import re
from datetime import datetime
from enum import Enum
from typing import ForwardRef

from odoo import api, models

_logger = logging.getLogger(__name__)


tz_datetime = re.compile(r".*[-+]0[0-9]:00$")


class SpecMixinImport(models.AbstractModel):
    _name = "spec.mixin_import"
    _description = """
    A recursive Odoo object builder that works along with the
    GenerateDS object builder from the parsed XML.
    Here we take into account the concrete Odoo objects where the schema
    mixins where injected and possible matcher or builder overrides.
    """

    @api.model
    def build_from_binding(self, node, dry_run=False):
        """
        Build an instance of an Odoo Model from a pre-populated
        Python binding object. Binding object such as the ones generated using
        generateDS can indeed be automatically populated from an XML file.
        This build method bridges the gap to build the Odoo object.

        It uses a pre-order tree traversal of the Python bindings and for each
        sub-binding (or node) it sees what is the corresponding Odoo model to map.

        Build can persist the object or just return a new instance
        depending on the dry_run parameter.

        Defaults values and control options are meant to be passed in the context.
        """
        model = self._get_concrete_model(self._name)
        attrs = model.with_context(dry_run=dry_run).build_attrs(node)
        if dry_run:
            return model.new(attrs)
        else:
            return model.create(attrs)

    @api.model
    def build_attrs(self, node, path="", defaults_model=None):
        """
        Build a new odoo model instance from a Python binding element or
        sub-element. Iterates over the binding fields to populate the Odoo fields.
        """
        vals = {}
        for fname, fspec in node.__dataclass_fields__.items():
            self._build_attr(node, self._fields, vals, path, (fname, fspec))
        vals = self._prepare_import_dict(vals, defaults_model=defaults_model)
        return vals

    @api.model
    def _build_attr(self, node, fields, vals, path, attr):
        """
        Build an Odoo field from a binding attribute.
        """
        value = getattr(node, attr[0])
        if value is None or value == []:
            return False
        key = "{}{}".format(
            self._field_prefix,
            attr[1].metadata.get("name", attr[0]),
        )
        child_path = f"{path}.{key}"

        # Is attr a xsd SimpleType or a ComplexType?
        # with xsdata a ComplexType can have a type like:
        # typing.Union[nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00.TinfRespTec, NoneType]
        # or typing.Union[ForwardRef('Tnfe.InfNfe.Det.Imposto'), NoneType]
        # that's why we test if the 1st Union type is a dataclass or a ForwardRef
        if attr[1].type == str or (
            not isinstance(attr[1].type.__args__[0], ForwardRef)
            and not dataclasses.is_dataclass(attr[1].type.__args__[0])
        ):
            # SimpleType
            if isinstance(value, Enum):
                value = value.value
            if fields.get(key) and fields[key].type == "datetime":
                if "T" in value:
                    if tz_datetime.match(value):
                        old_value = value
                        value = old_value[:19]
                        # TODO see python3/pysped/xml_sped/base.py#L692
                    value = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")

            self._build_string_not_simple_type(key, vals, value, node)

        else:
            if str(attr[1].type).startswith("typing.List") or "ForwardRef" in str(
                attr[1].type
            ):  # o2m
                binding_type = attr[1].type.__args__[0].__forward_arg__
            else:
                binding_type = attr[1].type.__args__[0].__name__

            # ComplexType
            if fields.get(key) and fields[key].related:
                if fields[key].readonly and fields[key].type == "many2one":
                    return False  # ex: don't import NFe infRespTec
                # example: company.nfe40_enderEmit related on partner_id
                # then we need to set partner_id, not nfe40_enderEmit
                key = fields[key].related[-1]  # -1 works with _inherits
                comodel_name = fields[key].comodel_name
            else:
                clean_type = binding_type.lower()
                comodel_name = "{}.{}.{}".format(
                    self._schema_name,
                    self._schema_version.replace(".", "")[0:2],
                    clean_type.split(".")[-1],
                )

            comodel = self._get_concrete_model(comodel_name)
            if comodel is None:  # example skip ICMS100 class
                return
            if str(attr[1].type).startswith("typing.List"):
                # o2m
                lines = []
                for line in [li for li in value if li]:
                    line_vals = comodel.build_attrs(
                        line, path=child_path, defaults_model=comodel
                    )
                    lines.append((0, 0, line_vals))
                vals[key] = lines
            else:
                # m2o
                comodel_vals = comodel.build_attrs(value, path=child_path)
                child_defaults = self._extract_related_values(vals, key)

                comodel_vals.update(child_defaults)
                # FIXME comodel._build_many2one
                self._build_many2one(
                    comodel, vals, comodel_vals, key, value, child_path
                )

    @api.model
    def _build_string_not_simple_type(self, key, vals, value, node):
        vals[key] = value

    @api.model
    def _build_many2one(self, comodel, vals, comodel_vals, key, value, path):
        if comodel._name == self._name:
            # stacked m2o
            vals.update(comodel_vals)
        else:
            vals[key] = comodel.match_or_create_m2o(comodel_vals, vals)

    @api.model
    def _extract_related_values(self, vals, key):
        """
        Example: prepare nfe40_enderEmit partner legal_name and name
        by reading nfe40_xNome and nfe40_xFant on nfe40_emit
        """
        key_vals = {}
        for k, v in self._fields.items():
            if (
                hasattr(v, "related")
                and hasattr(v.related, "__len__")
                and len(v.related) == 2
                and v.related[0] == key
                and vals.get(k) is not None
            ):
                key_vals[v.related[1]] = vals[k]
        return key_vals

    @api.model
    def _prepare_import_dict(
        self, vals, model=None, parent_dict=None, defaults_model=False
    ):
        """
        Set non computed field values based on XML values if required.
        NOTE: this is debatable if we could use an api multi with values in
        self instead of the vals dict. Then that would be like when new()
        is used in account_invoice or sale_order before playing some onchanges
        """
        if model is None:
            model = self

        vals = {k: v for k, v in vals.items() if k in self._fields.keys()}

        related_many2ones = {}
        fields = model._fields
        for k, v in fields.items():
            # select schema choices for a friendly UI:
            if k.startswith(f"{self._field_prefix}choice"):
                for item in v.selection or []:
                    if vals.get(item[0]) not in [None, []]:
                        vals[k] = item[0]
                        break

            # reverse map related fields as much as possible
            elif v.related is not None and vals.get(k) is not None:
                if len(v.related) == 1:
                    vals[v.related[0]] = vals.get(k)
                elif len(v.related) == 2 and k.startswith(self._field_prefix):
                    related_m2o = v.related[0]
                    # don't mess with _inherits write system
                    if not any(related_m2o == i[1] for i in model._inherits.items()):
                        key_vals = related_many2ones.get(related_m2o, {})
                        key_vals[v.related[1]] = vals.get(k)
                        related_many2ones[related_m2o] = key_vals

        # now we deal with the related m2o with compound related
        # (example: create Nfe lines product)
        for related_m2o, sub_val in related_many2ones.items():
            comodel_name = fields[related_m2o].comodel_name
            comodel = model._get_concrete_model(comodel_name)
            related_many2ones = model._verify_related_many2ones(related_many2ones)
            if hasattr(comodel, "match_or_create_m2o"):
                vals[related_m2o] = comodel.match_or_create_m2o(sub_val, vals)
            else:  # search res.country with Brasil for instance
                vals[related_m2o] = model.match_or_create_m2o(sub_val, vals, comodel)

        if defaults_model is not None:
            defaults = defaults_model.with_context(
                record_dict=vals,
                parent_dict=parent_dict,
            ).default_get(
                [
                    f
                    for f, v in defaults_model._fields.items()
                    if v.type not in ["binary", "integer", "float", "monetary"]
                    and v.name not in vals.keys()
                ]
            )
            vals.update(defaults)
            # NOTE: also eventually load default values from the context?
        return vals

    @api.model
    def _verify_related_many2ones(self, related_many2ones):
        return related_many2ones

    @api.model
    def match_record(self, rec_dict, parent_dict, model=None):
        """
        Inspired from match_* methods from
        https://github.com/OCA/edi/blob/11.0/base_business_document_import
        /models/business_document_import.py
        """
        if model is None:
            model = self
        default_key = [model._rec_name or "name"]
        search_keys = "_%s_search_keys" % (self._schema_name)
        if hasattr(model, search_keys):
            keys = getattr(model, search_keys) + default_key
        else:
            keys = [model._rec_name or "name"]
        keys = self._get_aditional_keys(model, rec_dict, keys)
        for key in keys:
            if rec_dict.get(key):
                # TODO enable to build criteria using parent_dict
                # such as state_id when searching for a city
                if hasattr(model, "_nfe_extra_domain"):  # FIXME make generic
                    domain = model._nfe_extra_domain + [(key, "=", rec_dict.get(key))]
                else:
                    domain = [(key, "=", rec_dict.get(key))]
                match_ids = model.search(domain)
                if match_ids:
                    if len(match_ids) > 1:
                        _logger.warning(
                            f"!! WARNING more than 1 record found!! model: {model},"
                            f" domain:{domain}"
                        )
                    return match_ids[0].id
        return False

    @api.model
    def _get_aditional_keys(self, model, rec_dict, keys):
        return keys

    @api.model
    def match_or_create_m2o(self, rec_dict, parent_dict, model=None):
        """
        Often the parent_dict can be used to refine the search.
        Passing the model makes it possible to override without inheriting
        from this mixin.
        """
        # TODO log things in chatter like in base_business_document_import
        if model is None:
            model = self
        if hasattr(model, "_match_record"):
            rec_id = model.match_record(rec_dict, parent_dict, model)
        else:
            rec_id = self.match_record(rec_dict, parent_dict, model)
        if not rec_id:
            vals = self._prepare_import_dict(
                rec_dict, model=model, parent_dict=parent_dict, defaults_model=model
            )
            if self._context.get("dry_run"):
                rec = model.new(vals)
                rec_id = rec.id
                # at this point for NewId records, some fields
                # may need to be set calling the inverse field functions:
                for fname in vals:
                    field = model._fields.get(fname)
                    if isinstance(field.inverse, str):
                        getattr(rec, field.inverse)()
                        rec.write(vals)  # ensure vals values aren't overriden
                    elif (
                        field.inverse
                        and len(inspect.getfullargspec(field.inverse).args) < 2
                    ):
                        field.inverse()
                        rec.write(vals)
            else:
                rec_id = (
                    model.with_context(
                        parent_dict=parent_dict,
                        lang="en_US",
                    )
                    .create(vals)
                    .id
                )
        return rec_id
