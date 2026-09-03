# Copyright 2019 KMEE
# Copyright 2021-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import logging
import sys
from importlib import import_module

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SpecMixinExport(models.AbstractModel):
    _name = "spec.mixin_export"
    _description = "A mixin providing serialization features."

    @api.model
    def _get_binding_class(self, odoo_class, field_name=None) -> type:
        """
        Use (_spec_prefix)_binding_type of odoo_class and its binding_module to get
        the Python binding type for export.
        """
        # importlib because the binding may not be imported yet: modules with
        # an optional external dependency cannot import it at load time (any
        # warning at loading fails the checklog), so nothing guarantees the
        # binding is in sys.modules before the first export.
        binding_module = import_module(self._get_spec_property("binding_module"))
        binding_type = odoo_class._get_spec_property("binding_type")
        if not binding_type and field_name:
            if field_name in odoo_class._fields and hasattr(
                odoo_class._fields[field_name], "xsd_type"
            ):
                binding_type = odoo_class._fields[field_name].xsd_type
                # Camel Case it:
                binding_type = self.fix_camel_case(binding_type)
            if not binding_type:
                # TODO fix these pathologic cases
                _logger.debug(
                    "TODO fix these cases %s %s %s", field_name, self, odoo_class
                )
                binding_type = odoo_class._get_spec_property(
                    f"binding_type_{field_name.split('_')[1]}"
                )
        if not binding_type:
            binding_types = set(
                map(
                    lambda clazz: clazz._binding_type,
                    list(
                        filter(
                            lambda clazz: hasattr(clazz, "_binding_type"),
                            type(odoo_class).mro(),
                        )
                    ),
                )
            )
            assert len(binding_types) == 1, (
                f"Found several (or no) _binding_type attributes in {odoo_class} "
                f"ancestors: {binding_types}. You can define a "
                f"_{self._spec_prefix()}_binding_type"
                f"{'_' + field_name.split('_')[1] if field_name else ''} "
                f"in {odoo_class} "
                "to avoid ambiguities."
            )
            binding_type = binding_types.pop()
        for attr in binding_type.split("."):  # this will dive into nested classes
            binding_module = getattr(binding_module, attr)
        return binding_module

    @api.model
    def fix_camel_case(self, word: str) -> str:
        if not word:
            return word

        # First character never changes case
        result = [word[0]]

        for i in range(1, len(word)):
            # If current char is uppercase AND the previous char is uppercase
            if word[i].isupper() and word[i - 1].isupper():
                result.append(word[i].lower())
            else:
                result.append(word[i])

        return "".join(result)

    @api.model
    def _get_model_classes(self):
        classes = [getattr(x, "_name", None) for x in type(self).mro()]
        return classes

    @api.model
    def _get_spec_classes(self, classes=False):
        if not classes:
            classes = self._get_model_classes()
        spec_classes = []
        for c in set(classes):
            if c is None:
                continue
            if not c.startswith(f"{self._context['spec_schema']}."):
                continue
            # the following filter to fields to show
            # when several XSD class are injected in the same object
            if self._context.get("spec_class") and c != self._context["spec_class"]:
                continue
            spec_classes.append(c)
        return spec_classes

    def _export_fields(self, xsd_fields, class_obj, export_dict, field_name=None):
        """
        Iterate over the record fields and map them in an dict of values
        that will later be injected as **kwargs in the proper XML Python
        binding constructors. Hence the value can either be simple values or
        sub binding instances already properly instanciated.

        This method implements a dynamic dispatch checking if there is any
        method called _export_fields_CLASS_NAME to update the xsd_fields
        and export_dict variables, this way we allow controlling the
        flow of fields to export or injecting specific values in the
        field export.
        """
        self.ensure_one()
        binding_class = self._get_binding_class(class_obj, field_name=field_name)
        binding_class_spec = binding_class.__dataclass_fields__

        xsd_fields = [i for i in xsd_fields]
        class_name = class_obj._name.replace(".", "_")
        export_method_name = f"_export_fields_{class_name}"
        if hasattr(self, export_method_name):
            export_method = getattr(self, export_method_name)
            export_method(xsd_fields, class_obj, export_dict)

        for xsd_field in xsd_fields:
            if not xsd_field:
                continue
            if (
                not self._fields.get(xsd_field)
            ) and xsd_field not in self._get_stacking_points().keys():
                continue
            field_spec_name = xsd_field.split("_")[1]  # remove schema prefix
            field_spec = False
            for fname, fspec in binding_class_spec.items():
                if fspec.metadata.get("name", {}) == field_spec_name:
                    field_spec_name = fname
                if field_spec_name == fname:
                    field_spec = fspec
            if field_spec and not field_spec.init:
                # case of xsd fixed values, we should not try to write them
                continue

            if not binding_class_spec.get(field_spec_name):
                # this can happen with a o2m generated foreign key for instance
                continue
            field_spec = binding_class_spec[field_spec_name]
            field_data = self._export_field(
                xsd_field, class_obj, field_spec, export_dict.get(field_spec_name)
            )
            if xsd_field in self._get_stacking_points().keys():
                if not field_data:
                    # stacked nested tags are skipped if empty
                    continue
            elif not self[xsd_field] and not field_data:
                continue

            export_dict[field_spec_name] = field_data

    def _get_tag_export_hook(self, xsd_field, parent_tag=None):
        """
        Return the per tag export hook for a field, if any.

        The hook is a method named _export_tag_SCHEMA_VERSION_TAG_NAME
        (e.g. _export_tag_nfe_40_ibscbs for the nfe40_IBSCBS field). The
        _export_tag_ prefix keeps this family apart from the per class
        _export_fields_CLASS_NAME hooks: tag names and spec class names
        share the same shape (the gMonoPadrao tag and the
        nfe.40.gmonopadrao class would both yield
        _export_fields_nfe_40_gmonopadrao), so a common prefix would make
        the two dispatches silently collide.

        When the same tag appears under different parent tags with different
        values (e.g. gRed inside both gIBSUF and gCBS), a hook qualified by
        the parent tag takes precedence over the generic one:
        _export_tag_nfe_40_gibsuf_gred and _export_tag_nfe_40_gcbs_gred
        are looked up before _export_tag_nfe_40_gred.

        Stacking points never get a per tag hook: they are exported through
        their own class and already get the _export_fields_CLASS_NAME
        dispatch.
        """
        schema, version = self._spec_prefix(split=True)
        if not schema or xsd_field in self._get_stacking_points():
            return None
        tag = xsd_field.split("_", 1)[-1].lower()
        if parent_tag:
            qualified_method = getattr(
                self,
                f"_export_tag_{schema}_{version}_{parent_tag.lower()}_{tag}",
                None,
            )
            if qualified_method is not None:
                return qualified_method
        return getattr(self, f"_export_tag_{schema}_{version}_{tag}", None)

    def _get_hook_binding_class(self, child_class, parent_binding_class=None):
        """
        Resolve the binding class of a spec model exported via per tag hooks.

        Falls back to the parent binding class module when the type is not
        reachable from the schema binding module (e.g. Tcibs lives in
        nfelib dfe_tipos_basicos, not in leiaute_nfe).
        """
        try:
            return self._get_binding_class(child_class)
        except AttributeError:
            if parent_binding_class is None:
                raise
            binding = sys.modules[parent_binding_class.__module__]
            for attr in child_class._binding_type.split("."):
                binding = getattr(binding, attr)
            return binding

    def _export_m2o_via_tag_hooks(
        self, xsd_field, class_obj, parent_binding_class=None, parent_tag=None
    ):
        """
        Build the binding of a many2one field through per tag export hooks.

        Used for fields whose comodel is a reusable schema type that is
        neither stacked in self nor mapped to a related record (e.g. the
        nfe40_IBSCBS field pointing to nfe.40.ttribnfe): the class name
        dispatch would not match the tag name and the field values are not
        denormalized in self. The hook of each (sub) tag only populates
        export_dict with simple values (numeric values are formatted here
        according to the field xsd_type); this method assembles the
        bindings, recursing into the child many2one fields that have their
        own hook (e.g. nfe40_gIBSUF -> _export_tag_nfe_40_gibsuf, and
        nfe40_gRed inside gIBSUF -> _export_tag_nfe_40_gibsuf_gred or
        _export_tag_nfe_40_gred, see _get_tag_export_hook).

        Returns False when the hook leaves export_dict empty, so the tag
        is omitted.
        """
        hook = self._get_tag_export_hook(xsd_field, parent_tag=parent_tag)
        if hook is None:
            return False
        # "is not None": an empty recordset is falsy but still holds _fields
        field = (
            class_obj._fields.get(xsd_field) if class_obj is not None else None
        ) or self._fields.get(xsd_field)
        child_class = self.env[field.comodel_name]
        binding_class = self._get_hook_binding_class(child_class, parent_binding_class)
        prefix = f"{self._spec_prefix()}_"
        xsd_fields = [
            f
            for f in child_class._fields
            if f.startswith(prefix) and "_choice" not in f
        ]
        export_dict = {}
        hook(xsd_fields, child_class, export_dict)
        if not export_dict:
            return False
        tag = xsd_field.split("_", 1)[-1]
        for child_field in xsd_fields:
            tag_name = child_field.split("_", 1)[-1]
            if child_class._fields[child_field].type == "many2one":
                if export_dict.get(tag_name) is None:
                    sub_data = self._export_m2o_via_tag_hooks(
                        child_field, child_class, binding_class, parent_tag=tag
                    )
                    if sub_data:
                        export_dict[tag_name] = sub_data
                continue
            # format the raw numeric values set by the hooks according
            # to the decimal places of the field xsd_type
            value = export_dict.get(tag_name)
            if isinstance(value, bool) or not isinstance(value, int | float):
                continue
            export_dict[tag_name] = self._format_float_xsd(
                value, getattr(child_class._fields[child_field], "xsd_type", None)
            )
        sliced_dict = {
            key: value
            for key, value in export_dict.items()
            if key in binding_class.__dataclass_fields__ and value is not None
        }
        return binding_class(**sliced_dict)

    def _export_field(self, xsd_field, class_obj, field_spec, export_value=None):
        """
        Map a single Odoo field to a python binding value according to the
        kind of field.
        """
        self.ensure_one()
        # TODO: Export number required fields with Zero.
        field = class_obj._fields.get(
            xsd_field, self._get_stacking_points().get(xsd_field)
        )
        xsd_required = field.xsd_required if hasattr(field, "xsd_required") else None
        xsd_type = field.xsd_type if hasattr(field, "xsd_type") else None
        if field.type == "many2one":
            if (not self._get_stacking_points().get(xsd_field)) and (
                not self[xsd_field] and not xsd_required
            ):
                # a per tag hook can export a field with no record behind
                # it, so let it reach _export_many2one, the single m2o
                # entry point, which dispatches to the hooks
                if (
                    field.comodel_name not in self._get_spec_classes()
                    and self._get_tag_export_hook(xsd_field) is None
                ):
                    return False
            if hasattr(field, "xsd_choice_required"):
                xsd_required = True
            return self._export_many2one(xsd_field, xsd_required, class_obj)
        elif self._fields[xsd_field].type == "one2many":
            return self._export_one2many(xsd_field, class_obj)
        elif self._fields[xsd_field].type == "datetime" and self[xsd_field]:
            return self._export_datetime(xsd_field)
        elif self._fields[xsd_field].type == "date" and self[xsd_field]:
            return self._export_date(xsd_field)
        elif (
            self._fields[xsd_field].type in ("float", "monetary")
            and self[xsd_field] is not False
        ):
            if hasattr(field, "xsd_choice_required"):
                xsd_required = True
            return self._export_float_monetary(
                xsd_field, xsd_type, class_obj, xsd_required, export_value
            )
        elif isinstance(self[xsd_field], str):
            return self[xsd_field].strip()
        else:
            return self[xsd_field]

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        self.ensure_one()
        if field_name in self._get_stacking_points().keys():
            return self._build_binding(
                class_name=self._get_stacking_points()[field_name].comodel_name
            )
        elif not self[field_name] and self._get_tag_export_hook(field_name):
            # no record behind the m2o: the tag is built from its hooks
            return self._export_m2o_via_tag_hooks(field_name, class_obj)
        else:
            return (self[field_name] or self)._build_binding(
                field_name=field_name,
                class_name=class_obj._fields[field_name].comodel_name,
            )

    def _export_one2many(self, field_name, class_obj=None):
        self.ensure_one()
        relational_data = []
        for relational_field in self[field_name]:
            field_data = relational_field._build_binding(
                class_name=class_obj._fields[field_name].comodel_name
            )
            relational_data.append(field_data)
        return relational_data

    @api.model
    def _format_float_xsd(self, value, xsd_type):
        """
        Format a float according to the decimal places of its xsd_type
        (e.g. TDec1302 -> 2 decimals, TDec_0302_04RTC -> 4 decimals).
        """
        if xsd_type and xsd_type.startswith("TDec"):
            tdec = "".join(filter(lambda x: x.isdigit(), xsd_type))[-2:]
        else:
            tdec = ""
        return str(f"%.{tdec}f" % value)

    def _export_float_monetary(
        self, field_name, xsd_type, class_obj, xsd_required, export_value=None
    ):
        self.ensure_one()
        field_data = export_value or self[field_name]
        # TODO check xsd_required for all fields to export?
        if not field_data and not xsd_required:
            return False
        return self._format_float_xsd(field_data, xsd_type)

    def _export_date(self, field_name):
        self.ensure_one()
        return str(self[field_name])

    def _export_datetime(self, field_name):
        self.ensure_one()
        return str(
            fields.Datetime.context_timestamp(
                self, fields.Datetime.from_string(self[field_name])
            ).isoformat("T")
        )

    def _build_binding(
        self, spec_schema=None, spec_version=None, class_name=None, field_name=None
    ):
        """
        Iterate over an Odoo record and its m2o and o2m sub-records
        using a pre-order tree traversal and map the Odoo record values
        to a dict of Python binding values.

        These values will later be injected as **kwargs in the proper XML Python
        binding constructors. Hence the value can either be simple values or
        sub binding instances already properly instanciated.
        """
        self.ensure_one()
        if spec_schema and spec_version:
            self = self.with_context(spec_schema=spec_schema, spec_version=spec_version)
            self.env[f"spec.mixin.{spec_schema}"]._register_hook()
        if not class_name:
            class_name = self._get_spec_property("stacking_mixin", self._name)

        class_obj = self.env[class_name]

        xsd_fields = (
            i
            for i in class_obj._fields
            if class_obj._fields[i].name.startswith(f"{self._spec_prefix()}_")
            and "_choice" not in class_obj._fields[i].name
        )

        kwargs = {}
        binding_class = self._get_binding_class(class_obj, field_name=field_name)
        self._export_fields(
            xsd_fields, class_obj, export_dict=kwargs, field_name=field_name
        )
        sliced_kwargs = {
            key: kwargs.get(key)
            for key in binding_class.__dataclass_fields__.keys()
            if kwargs.get(key) is not None
        }
        return binding_class(**sliced_kwargs)
