# Copyright 2019-2020 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import logging
import re
from datetime import datetime
from odoo import api, models
from .spec_models import SpecModel

_logger = logging.getLogger(__name__)


tz_datetime = re.compile(r'.*[-+]0[0-9]:00$')


class AbstractSpecMixin(models.AbstractModel):
    """
    A recursive Odoo object builder that works along with the
    GenerateDS object builder from the parsed XML.
    Here we take into account the concrete Odoo objects where the schema
    mixins where injected and possible matcher or builder overrides.
    """
    _inherit = 'spec.mixin'

    @api.model
    def build(self, node, dry_run=False):
        """
        Builds an instance of an Odoo Model from a pre-populated
        Python binding object. Binding object such as the ones generated using
        generateDS can indeed be automatically populated from an XML file.
        This build method bridges the gap to build the Odoo object.

        It uses a pre-order tree traversal of the Python bindings and for each
        sub-binding (or node) it sees what is the corresponding Odoo model to map.

        Build can persist the object or just return a new instance
        depending on the dry_run parameter.

        Defaults values and control options are meant to be passed in the context.
        """
        # TODO new or create choice
        # TODO ability to match existing record here
        model_name = SpecModel._get_concrete(self._name) or self._name
        model = self.env[model_name]
        attrs = model.with_context(dry_run=dry_run).build_attrs(node)
        if dry_run:
            return model.new(attrs)
        else:
            return model.create(attrs)

    @api.model
    def build_attrs(self, node, path=''):
        """
        Builds a new odoo model instance from a Python binding element or
        sub-element. Iterates over the binding fields to populate the Odoo fields.
        """
        fields = self._fields
        # no default image for easier debugging
        vals = self.default_get([f for f, v in fields.items()
                                 if v.type not in ['binary', 'integer',
                                                   'float', 'monetary']])
        # TODO deal with default values but take them from self._context
        # if path == '':
        #    vals.update(defaults)
        # we sort attrs to be able to define m2o related values
        sorted_attrs = sorted(node.member_data_items_,
                              key=lambda a: a.get_container() in [0, 1],
                              reverse=True)
        for attr in sorted_attrs:
            self._build_attr(node, fields, vals, path, attr)

        vals = self._prepare_import_dict(vals)
        return vals

    @api.model
    def _build_attr(self, node, fields, vals, path, attr):
        """
        Builds an Odoo field from a binding attribute.
        """
        value = getattr(node, attr.get_name())
        if value is None or value == []:
            return False
        key = "%s%s" % (self._field_prefix, attr.get_name(),)
        child_path = '%s.%s' % (path, key)
        binding_type = attr.get_child_attrs().get('type')
        if binding_type is None or binding_type.startswith('xs:')\
                or binding_type.startswith('xsd:'):
            # SimpleType

            if fields.get(key) and fields[key].type == 'datetime':
                if 'T' in value:
                    if tz_datetime.match(value):
                        old_value = value
                        value = old_value[:19]
                        # TODO see python3/pysped/xml_sped/base.py#L692
                    value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')

            self._build_string_not_simple_type(key, vals, value, node)

        else:
            # ComplexType
            if fields.get(key) and fields[key].related:
                # example: company.nfe40_enderEmit related on partner_id
                # then we need to set partner_id, not nfe40_enderEmit
                key = fields[key].related[-1]  # -1 works with _inherits
                comodel_name = fields[key].comodel_name
            else:
                clean_type = attr.get_child_attrs()[
                    'type'].replace('Type', '').lower()
                comodel_name = "%s.%s.%s" % (
                    self._schema_name,
                    self._schema_version.replace('.', '')[0:2],
                    clean_type,
                )

            comodel = self.get_concrete_model(comodel_name)
            if comodel is None:  # example skip ICMS100 class
                return

            if attr.get_container() == 0:
                # m2o
                new_value = comodel.build_attrs(value,
                                                path=child_path)
                child_defaults = self._extract_related_values(vals, key)

                new_value.update(child_defaults)
                # FIXME comodel._build_many2one
                self._build_many2one(comodel, vals, new_value, key,
                                     value, child_path)
            elif attr.get_container() == 1:
                # o2m
                lines = []
                for line in [l for l in value if l]:
                    line_vals = comodel.build_attrs(line,
                                                    path=child_path)
                    lines.append((0, 0, line_vals))
                vals[key] = lines

    @api.model
    def _build_string_not_simple_type(self, key, vals, value, node):
        vals[key] = value

    @api.model
    def _build_many2one(self, comodel, vals, new_value, key, value, path):
        if comodel._name == self._name:
            # stacked m2o
            vals.update(new_value)
        else:
            vals[key] = comodel.match_or_create_m2o(new_value, vals)

    @api.model
    def get_concrete_model(self, comodel_name):
        "Lookup for concrete models where abstract schema mixins were injected"
        if hasattr(models.MetaModel, 'mixin_mappings') \
                and models.MetaModel.mixin_mappings.get(comodel_name)\
                is not None:
            return self.env[models.MetaModel.mixin_mappings[comodel_name]]
        else:
            return self.env.get(comodel_name)

    @api.model
    def _extract_related_values(self, vals, key):
        """
        Example: prepare nfe40_enderEmit partner legal_name and name
        by reading nfe40_xNome and nfe40_xFant on nfe40_emit
        """
        key_vals = {}
        for k, v in self._fields.items():
            if hasattr(v, 'related')\
                    and hasattr(v.related, '__len__')\
                    and len(v.related) == 2\
                    and v.related[0] == key\
                    and vals.get(k) is not None:
                key_vals[v.related[1]] = vals[k]
        # if key_vals != {}:
        #     _logger.info("\nEXTRACT RELATED FROM PARENT:", self, key, key_vals)
        # TODO use inside match_or_create??
        return key_vals

    @api.model
    def _prepare_import_dict(self, vals, model=None):
        """
        Set non computed field values based on XML values if required.
        NOTE: this is debatable if we could use an api multi with values in
        self instead of the vals dict. Then that would be like when new()
        is used in account_invoice or sale_order before playing some onchanges
        """
        if model is None:
            model = self
        related_many2ones = {}
        fields = model.fields_get()
        for k, v in fields.items():
            # select schema choices for a friendly UI:
            if k.startswith('%schoice' % (self._field_prefix,)):
                for item in v.get('selection', []):
                    if vals.get(item[0]) not in [None, []]:
                        vals[k] = item[0]
                        break

            # reverse map related fields as much as possible
            elif v.get('related') is not None and vals.get(k) is not None:
                if len(v['related']) == 1:
                    vals[v['related'][0]] = vals.get(k)
                elif len(v['related']) == 2 and k.startswith(self._field_prefix):
                    related_m2o = v['related'][0]
                    # don't mess with _inherits write system
                    if not any(related_m2o == i[1]
                               for i in model._inherits.items()):
                        key_vals = related_many2ones.get(related_m2o, {})
                        key_vals[v['related'][1]] = vals.get(k)
                        related_many2ones[related_m2o] = key_vals

        # now we deal with the related m2o with compound related
        # (example: create Nfe lines product)
        for related_m2o, sub_val in related_many2ones.items():
            comodel_name = fields[related_m2o]['relation']
            comodel = model.get_concrete_model(comodel_name)
            related_many2ones = \
                model._verify_related_many2ones(related_many2ones)
            if hasattr(comodel, 'match_or_create_m2o'):
                vals[related_m2o] = comodel.match_or_create_m2o(sub_val, vals)
            else:  # search res.country with Brasil for instance
                vals[related_m2o] = model.match_or_create_m2o(sub_val, vals,
                                                              comodel)
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
        default_key = [model._rec_name or model._concrete_rec_name or 'name']
        search_keys = "_%s_search_keys" % (self._schema_name)
        if hasattr(model, search_keys):
            keys = getattr(model, search_keys) + default_key
        else:
            keys = [model._rec_name or model._concrete_rec_name or 'name']
        keys = self._get_aditional_keys(model, rec_dict, keys)
        for key in keys:
            if rec_dict.get(key):
                # TODO enable to build criteria using parent_dict
                # such as state_id when searching for a city
                if hasattr(model, '_nfe_extra_domain'):
                    domain = model._nfe_extra_domain + [(key, '=',
                                                         rec_dict.get(key))]
                else:
                    domain = [(key, '=', rec_dict.get(key))]
                match_ids = model.search(domain)
                if match_ids:
                    if len(match_ids) > 1:
                        _logger.warning(
                            "!! WARNING more than 1 record found!!")
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
        if hasattr(model, '_match_record'):
            rec_id = model.match_record(rec_dict, parent_dict, model)
        else:
            rec_id = self.match_record(rec_dict, parent_dict, model)
        if not rec_id:
            rec_dict = self._prepare_import_dict(rec_dict, model)
            create_dict = {k: v for k, v in rec_dict.items()
                           if k in self._fields.keys()}
            if self._context.get('dry_run'):
                rec_id = model.new(create_dict).id
            else:
                rec_id = model.with_context(
                    parent_dict=parent_dict
                ).create(create_dict).id
        return rec_id
