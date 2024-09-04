# Copyright 2019 KMEE
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
import logging
import sys
from io import StringIO

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SpecMixinExport(models.AbstractModel):
    _name = "spec.mixin_export"
    _description = "a mixin providing serialization features"

    @api.model
    def _get_binding_class(self, class_obj):
        binding_module = sys.modules[self._binding_module]
        for attr in class_obj._binding_type.split("."):
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
            if not c.startswith(f"{self._schema_name}."):
                continue
            # the following filter to fields to show
            # when several XSD class are injected in the same object
            if self._context.get("spec_class") and c != self._context["spec_class"]:
                continue
            spec_classes.append(c)
        return spec_classes

    @api.model
    def _print_xml(self, binding_instance):
        if not binding_instance:
            return
        output = StringIO()
        binding_instance.export(
            output,
            0,
            pretty_print=True,
        )
        output.close()

    def _export_fields(self, xsd_fields, class_obj, export_dict):
        """
        Iterate over the record fields and map them in an dict of values
        that will later be injected as **kwargs in the proper XML Python
        binding constructors. Hence the value can either be simple values or
        sub binding instances already properly instanciated.

        This method implements a dynamic dispatch checking if there is any
        method called _export_fields_CLASS_NAME to update the xsd_fields
        and export_dict variables, this way we allow controlling the
        flow of fields to export or injecting specific values ​​in the
        field export.
        """
        self.ensure_one()
        binding_class = self._get_binding_class(class_obj)
        binding_class_spec = binding_class.__dataclass_fields__

        class_name = class_obj._name.replace(".", "_")
        export_method_name = "_export_fields_%s" % class_name
        if hasattr(self, export_method_name):
            xsd_fields = [i for i in xsd_fields]
            export_method = getattr(self, export_method_name)
            export_method(xsd_fields, class_obj, export_dict)

        for xsd_field in xsd_fields:
            if not xsd_field:
                continue
            if (
                not self._fields.get(xsd_field)
            ) and xsd_field not in self._stacking_points.keys():
                continue
            field_spec_name = xsd_field.replace(class_obj._field_prefix, "")
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
            if xsd_field in self._stacking_points.keys():
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
        field = class_obj._fields.get(xsd_field, self._stacking_points.get(xsd_field))
        xsd_required = field.xsd_required if hasattr(field, "xsd_required") else None
        xsd_type = field.xsd_type if hasattr(field, "xsd_type") else None
        if field.type == "many2one":
            if (not self._stacking_points.get(xsd_field)) and (
                not self[xsd_field] and not xsd_required
            ):
                if field.comodel_name not in self._get_spec_classes():
                    return False
            if hasattr(field, "xsd_choice_required"):
                # NOTE generateds-odoo would abusively have xsd_required=True
                # already in the spec file in this case.
                # In xsdata-odoo we introduced xsd_choice_required.
                # Here we make the legacy code compatible with xsdata-odoo:
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
                xsd_required = True  # NOTE compat, see previous NOTE
            return self._export_float_monetary(
                xsd_field, xsd_type, class_obj, xsd_required, export_value
            )
        elif isinstance(self[xsd_field], str):
            return self[xsd_field].strip()
        else:
            return self[xsd_field]

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        self.ensure_one()
        if field_name in self._stacking_points.keys():
            return self._build_generateds(
                class_name=self._stacking_points[field_name].comodel_name
            )
        else:
            return (self[field_name] or self)._build_generateds(
                class_obj._fields[field_name].comodel_name
            )

    def _export_one2many(self, field_name, class_obj=None):
        self.ensure_one()
        relational_data = []
        for relational_field in self[field_name]:
            field_data = relational_field._build_generateds(
                class_obj._fields[field_name].comodel_name
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

    def _build_generateds(self, class_name=False):
        """
        Iterate over an Odoo record and its m2o and o2m sub-records
        using a pre-order tree traversal and maps the Odoo record values
        to  a dict of Python binding values.

        These values will later be injected as **kwargs in the proper XML Python
        binding constructors. Hence the value can either be simple values or
        sub binding instances already properly instanciated.
        """
        self.ensure_one()
        if not class_name:
            if hasattr(self, "_stacked"):
                class_name = self._stacked
            else:
                class_name = self._name

        class_obj = self.env[class_name]

        xsd_fields = (
            i
            for i in class_obj._fields
            if class_obj._fields[i].name.startswith(class_obj._field_prefix)
            and "_choice" not in class_obj._fields[i].name
        )

        kwargs = {}
        binding_class = self._get_binding_class(class_obj)
        self._export_fields(xsd_fields, class_obj, export_dict=kwargs)
        if kwargs:
            sliced_kwargs = {
                key: kwargs.get(key)
                for key in binding_class.__dataclass_fields__.keys()
                if kwargs.get(key)
            }
            binding_instance = binding_class(**sliced_kwargs)
            return binding_instance

    def export_xml(self, print_xml=True):
        self.ensure_one()
        result = []

        if hasattr(self, "_stacked"):
            binding_instance = self._build_generateds()
            if print_xml:
                self._print_xml(binding_instance)
            result.append(binding_instance)

        else:
            spec_classes = self._get_spec_classes()
            for class_name in spec_classes:
                binding_instance = self._build_generateds(class_name)
                if print:
                    self._print_xml(binding_instance)
                result.append(binding_instance)
        return result

    def export_ds(self):
        self.ensure_one()
        return self.export_xml(print_xml=False)
