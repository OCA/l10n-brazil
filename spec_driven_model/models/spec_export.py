# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from nfelib.v4_00 import leiauteNFe

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class AbstractSpecMixin(models.AbstractModel):
    _inherit = 'spec.mixin'

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
            if 'nfe.' not in c:  # make generic brittle
                continue
            # the following filter to fields to show
            # when several XSD class are injected in the same object
            if self._context.get('spec_class') and c != self._context[
                'spec_class']:
                continue
            spec_classes.append(c)
        return spec_classes

    def _build_generateds(self, class_item):
        class_obj = self.env[class_item]
        xml_required_fields = []
        for item in self.env[class_item]._fields:
            if self.env[class_item]._fields[item]._attrs.get('xsd_required'):
                xml_required_fields.append(item)
        kwargs = {}

        for xml_required_field in xml_required_fields:
            if self[xml_required_field]:  # FIXME: and class_obj._field_prefix:
                # if self._fields[xml_required_field]._fields[xml_required_field].relational:
                if self._fields[xml_required_field].type == 'many2one':
                    continue
                    self[xml_required_field]
                elif self._fields[xml_required_field].type == 'one2many':
                    continue
                    relational_data = []
                    for relational_field in self[xml_required_field]:
                        relational_data.append()
                    field_data = self[xml_required_field]
                else:
                    field_data = self[xml_required_field]
                kwargs[
                    # xml_required_field.replace(class_obj._field_prefix, '')
                    xml_required_field.replace('nfe40_', '')
                ] = field_data
        if class_obj._generateds_type and kwargs:
            #  FIXME: leiauteNFe hardcoded
            ds_class = getattr(leiauteNFe, class_obj._generateds_type)
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
        contents = output.getvalue()
        output.close()
        print(contents)

    def export_xml(self):
        spec_classes = self._get_spec_classes()
        ds_objects = []
        for class_item in spec_classes:
            ds_object = self._build_generateds(class_item)
            self._print_xml(ds_object)
            ds_objects.append(ds_object)
