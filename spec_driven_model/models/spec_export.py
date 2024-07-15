# Copyright 2019 KMEE
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
from io import StringIO
import logging
import sys
from odoo import models, fields


_logger = logging.getLogger(__name__)


class AbstractSpecMixin(models.AbstractModel):
    _inherit = 'spec.mixin'

    def _get_ds_class(self, class_obj):
        binding_module = sys.modules[self._binding_module]
        return getattr(binding_module, class_obj._generateds_type)

    def _export_fields(self, xsd_fields, class_obj, export_dict):
        ds_class = self._get_ds_class(class_obj)
        ds_class_spec = {i.name: i for i in ds_class.member_data_items_}

        for xsd_field in xsd_fields:
            if not xsd_field or not self._fields.get(xsd_field):
                continue
            field_spec_name = xsd_field.replace(class_obj._field_prefix, '')
            if not ds_class_spec.get(field_spec_name):
                # this can happen with a o2m generated foreign key for instance
                continue
            member_spec = ds_class_spec[field_spec_name]
            field_data = self._export_field(xsd_field, class_obj, member_spec)

            if not self[xsd_field] and not field_data:
                continue

            export_dict[field_spec_name] = field_data

    def _export_field(self, xsd_field, class_obj, member_spec):
        # TODO: Export number required fields with Zero.
        xsd_required = class_obj._fields[xsd_field]._attrs.get(
            'xsd_required')

        if self._fields[xsd_field].type == 'many2one':
            if not self[xsd_field] and not xsd_required:
                if class_obj._fields[xsd_field].comodel_name \
                        not in self._get_spec_classes():
                    return False
            return self._export_many2one(xsd_field, xsd_required,
                                         class_obj)
        elif self._fields[xsd_field].type == 'one2many':
            return self._export_one2many(xsd_field, class_obj)
        elif self._fields[xsd_field].type == 'datetime' and \
                self[xsd_field]:
            return self._export_datetime(xsd_field)
        elif self._fields[xsd_field].type == 'date' and self[xsd_field]:
            return self._export_date(xsd_field)
        elif self._fields[xsd_field].type in ('float', 'monetary') and \
                self[xsd_field] is not False:
            return self._export_float_monetary(
                xsd_field, member_spec, class_obj, xsd_required)
        else:
            return self[xsd_field]

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        if self._fields[field_name]._attrs.get('original_spec_model'):
            return self[field_name]._build_generateds(
                class_name=self._fields[field_name]._attrs.get(
                    'original_spec_model')
            )
        else:
            return (self[field_name] or self)._build_generateds(
                class_obj._fields[field_name].comodel_name)

    def _export_one2many(self, field_name, class_obj=None):
        relational_data = []
        for relational_field in self[field_name]:
            field_data = relational_field._build_generateds(
                class_obj._fields[field_name].comodel_name
            )
            relational_data.append(field_data)
        return relational_data

    def _export_float_monetary(self, field_name, member_spec, class_obj,
                               xsd_required):
        if member_spec.data_type[0]:
            TDec = ''.join(filter(lambda x: x.isdigit(),
                                  member_spec.data_type[0]))[-2:]
            my_format = "%.{0}f".format(TDec)
            return str(my_format % self[field_name])
        else:
            raise NotImplementedError

    def _export_date(self, field_name):
        return str(self[field_name])

    def _export_datetime(self, field_name):
        return str(fields.Datetime.context_timestamp(
            self,
            fields.Datetime.from_string(self[field_name])
        ).isoformat('T'))

    def _get_model_classes(self):
        classes = [getattr(x, '_name', None) for x in type(self).mro()]
        return classes

    def _get_spec_classes(self, classes=False):
        if not classes:
            classes = self._get_model_classes()
        spec_classes = []
        for c in set(classes):
            if c is None:
                continue
            if not c.startswith("%s." % (self._schema_name,)):
                continue
            # the following filter to fields to show
            # when several XSD class are injected in the same object
            if self._context.get('spec_class') and c != self._context[
                    'spec_class']:
                continue
            spec_classes.append(c)
        return spec_classes

    def _build_generateds(self, class_name=False):
        if not class_name:
            if hasattr(self, '_stacked'):
                class_name = self._stacked
            else:
                class_name = self._name

        class_obj = self.env[class_name]
        if not class_obj._generateds_type:
            return

        xsd_fields = (
            i for i in class_obj._fields if
            class_obj._fields[i].name.startswith(class_obj._field_prefix)
            and "_choice" not in class_obj._fields[i].name
        )

        kwargs = {}

        ds_class = self._get_ds_class(class_obj)
        self._export_fields(xsd_fields, class_obj, export_dict=kwargs)

        if kwargs:
            ds_object = ds_class(**kwargs)
            return ds_object

    def _print_xml(self, ds_object):
        if not ds_object:
            return
        output = StringIO()
        ds_object.export(
            output,
            0,
            pretty_print=True,
        )
        output.close()

    def export_xml(self, print_xml=True):
        result = []

        if hasattr(self, '_stacked'):
            ds_object = self._build_generateds()
            if print_xml:
                self._print_xml(ds_object)
            result.append(ds_object)

        else:
            spec_classes = self._get_spec_classes()
            for class_name in spec_classes:
                ds_object = self._build_generateds(class_name)
                if print:
                    self._print_xml(ds_object)
                result.append(ds_object)
        return result

    def export_ds(self):
        return self.export_xml(print_xml=False)
