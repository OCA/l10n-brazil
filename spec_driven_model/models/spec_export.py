# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
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

    def _build_generateds(self, class_item=False):
        if not class_item:
            if hasattr(self, '_stacked'):
                class_item = self._stacked
            else:
                class_item = self._name

        class_obj = self.env[class_item]
        if not class_obj._generateds_type:
            return

        # Remember to replace with generators
        xml_required_fields = [
            i for i in self.env[class_item]._fields if
            self.env[class_item]._fields[i]._attrs.get('xsd_required')
        ]

        kwargs = {}
        #  FIXME: leiauteNFe hardcoded
        ds_class = getattr(leiauteNFe, class_obj._generateds_type)
        ds_class_sepc = {i.name:i for i in ds_class.member_data_items_}

        for xml_required_field in xml_required_fields:
            # print(self[xml_required_field])
            # print(xml_required_field)
            # print(self._fields[xml_required_field].type)

            # FIXME: xml_required_field.replace(class_obj._field_prefix, '')
            field_spec_name = xml_required_field.replace('nfe40_', '')
            member_spec = ds_class_sepc[field_spec_name]

            if self._fields[xml_required_field].type == 'many2one':
                if self._fields[xml_required_field]._attrs.get('original_spec_model'):
                    field_data = self[xml_required_field]._build_generateds(
                        class_item=self._fields[xml_required_field]._attrs.get('original_spec_model')
                    )
                else:
                    # continue
                    field_data = self[xml_required_field]._build_generateds()
            elif self._fields[xml_required_field].type == 'one2many':
                relational_data = []
                for relational_field in self[xml_required_field]:
                    relational_data.append(
                        relational_field._build_generateds()
                    )
                field_data = relational_data
            elif self._fields[xml_required_field].type == 'datetime' and self[xml_required_field]:
                field_data = fields.Datetime.context_timestamp(
                    self,
                    fields.Datetime.from_string(self[xml_required_field])
                ).isoformat('T')
            elif self._fields[xml_required_field].type == 'monetary' and self[xml_required_field]:
                if member_spec.data_type[0] == 'TDec_1302':
                    field_data = str("%.2f" % self[xml_required_field])
                else:
                    raise NotImplementedError
            else:
                field_data = self[xml_required_field]

            if not self[xml_required_field]:
                continue
            kwargs[field_spec_name] = field_data

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
        contents = output.getvalue()
        output.close()
        print(contents)

    def export_xml(self):
        if hasattr(self, '_stacked'):
            ds_object = self._build_generateds()
            self._print_xml(ds_object)
        else:
            spec_classes = self._get_spec_classes()
            ds_objects = []
            for class_item in spec_classes:
                ds_object = self._build_generateds(class_item)
                self._print_xml(ds_object)
                ds_objects.append(ds_object)
