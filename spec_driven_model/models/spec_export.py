# Copyright 2019 KMEE
# Copyright 2021-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import logging
import sys

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SpecMixinExport(models.AbstractModel):
    _name = "spec.mixin_export"
    _description = "A mixin providing serialization features."

    @api.model
    def _get_binding_class(self, odoo_class) -> type:
        """
        Use (_spec_prefix)_binding_type of odoo_class and its binding_module to get
        the Python binding type for export.
        """
        binding_module = sys.modules[self._get_spec_property("binding_module")]
        binding_type = odoo_class._get_spec_property("binding_type")
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
                f"_{self._spec_prefix()}_binding_type in {odoo_class} "
                "to avoid ambiguities."
            )
            binding_type = binding_types.pop()
        for attr in binding_type.split("."):  # this will dive into nested classes
            binding_module = getattr(binding_module, attr)
        return binding_module

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

    def _export_fields(self, xsd_fields, class_obj, export_dict):
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
        binding_class = self._get_binding_class(class_obj)
        binding_class_spec = binding_class.__dataclass_fields__

        class_name = class_obj._name.replace(".", "_")
        export_method_name = f"_export_fields_{class_name}"
        if hasattr(self, export_method_name):
            xsd_fields = [i for i in xsd_fields]
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
                if field.comodel_name not in self._get_spec_classes():
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
        else:
            return (self[field_name] or self)._build_binding(
                class_name=class_obj._fields[field_name].comodel_name
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

    def _export_float_monetary(
        self, field_name, xsd_type, class_obj, xsd_required, export_value=None
    ):
        self.ensure_one()
        field_data = export_value or self[field_name]
        # TODO check xsd_required for all fields to export?
        if not field_data and not xsd_required:
            return False
        if xsd_type and xsd_type.startswith("TDec"):
            tdec = "".join(filter(lambda x: x.isdigit(), xsd_type))[-2:]
        else:
            tdec = ""
        my_format = f"%.{tdec}f"
        return str(my_format % field_data)

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

    def _build_binding(self, spec_schema=None, spec_version=None, class_name=None):
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
        binding_class = self._get_binding_class(class_obj)
        self._export_fields(xsd_fields, class_obj, export_dict=kwargs)
        sliced_kwargs = {
            key: kwargs.get(key)
            for key in binding_class.__dataclass_fields__.keys()
            if kwargs.get(key) is not None
        }
        return binding_class(**sliced_kwargs)
