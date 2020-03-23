import logging

import re
from datetime import datetime
from odoo import api, models
from .spec_models import SpecModel

_logger = logging.getLogger(__name__)


tz_datetime = re.compile(r'.*[-+]0[0-9]:00$')


class AbstractSpecMixin(models.AbstractModel):
    _inherit = 'spec.mixin'

    @api.model
    def build(self, node, defaults=False):

        if not defaults:
            defaults = dict()

        # TODO new or create choice
        # TODO ability to match existing record here
        model_name = SpecModel._get_concrete(self._name) or self._name
        model = self.env[model_name]
        attrs = model.build_attrs(node, create_m2o=True, defaults=defaults)
        return model.create(attrs)

    @api.model
    def build_attrs(self, node, create_m2o=False, path='', defaults=False):
        """A recursive Odoo object builder that works along with the
        GenerateDS object builder from the parsed XML.
        Here we take into account the concrete Odoo objects where the schema
        mixins where injected and possible matcher or builder overrides."""

        if not defaults:
            defaults = dict()

        fields = self.fields_get()
        # no default image for easier debugging
        vals = self.default_get([f for f, v in fields.items()
                                 if v['type'] != 'binary'])
        if path == '':
            vals.update(defaults)
        # we sort attrs to be able to define m2o related values
        sorted_attrs = sorted(node.member_data_items_,
                              key=lambda a: a.get_container() in [0, 1],
                              reverse=True)
        for attr in sorted_attrs:
            self._build_attr(node, fields, vals, path, attr, create_m2o,
                             defaults)

        vals = self._prepare_import_dict(vals, defaults=defaults)
        return vals

    def _build_attr(self, node, fields, vals, path, attr, create_m2o,
                    defaults):
        value = getattr(node, attr.get_name())
        if value is None or value == []:
            return False
        key = "nfe40_%s" % (attr.get_name(),)  # TODO schema wise
        child_path = '%s.%s' % (path, key)

        if attr.get_child_attrs().get('type') is None\
                or attr.get_child_attrs().get('type') == 'xs:string':
            # SimpleType
            if fields[key]['type'] == 'datetime':
                if 'T' in value:
                    if tz_datetime.match(value):
                        old_value = value
                        value = old_value[:19]
                        # TODO see python3/pysped/xml_sped/base.py#L692
                    value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')

            self._build_string_not_simple_type(key, vals, value, node)

        else:
            # ComplexType
            if fields.get(key) and fields[key].get('related'):
                # example: company.nfe40_enderEmit related on partner_id
                # then we need to set partner_id, not nfe40_enderEmit
                key = fields[key]['related'][-1]  # -1 works with _inherits
                comodel_name = fields[key]['relation']
            else:
                clean_type = attr.get_child_attrs()[
                    'type'].replace('Type', '').lower()
                comodel_name = "nfe.40.%s" % (clean_type,)  # TODO clean

            comodel = self.get_concrete_model(comodel_name)

            if attr.get_container() == 0:
                # m2o
                new_value = comodel.build_attrs(value,
                                                create_m2o=create_m2o,
                                                path=child_path,
                                                defaults=defaults)
                child_defaults = self._extract_related_values(vals, key)

                new_value.update(child_defaults)
                self._build_many2one(comodel, vals, new_value, key,
                                     create_m2o)
            elif attr.get_container() == 1:
                # o2m
                lines = []
                for line in [l for l in value if l]:
                    line_vals = comodel.build_attrs(line,
                                                    create_m2o=create_m2o,
                                                    path=child_path,
                                                    defaults=defaults)
                    lines.append((0, 0, line_vals))
                vals[key] = lines

    def _build_string_not_simple_type(self, key, vals, value, node):
        vals[key] = value

    def _build_many2one(self, comodel, vals, new_value, key, create_m2o):
        if comodel._name == self._name:
            # stacked m2o
            vals.update(new_value)
        else:
            vals[key] = comodel.match_or_create_m2o(
                new_value, vals, create_m2o)

    @api.model
    def get_concrete_model(self, comodel_name):
        "Lookup for concrete models where abstract schema mixins were injected"
        if comodel_name == 'nfe.40.tenderemi':  # TODO not a related field
            comodel_name = 'res.partner'
        if hasattr(models.MetaModel, 'mixin_mappings') \
                and models.MetaModel.mixin_mappings.get(comodel_name)\
                is not None:
            return self.env[models.MetaModel.mixin_mappings[comodel_name]]
        else:
            return self.env[comodel_name]

    @api.model
    def _extract_related_values(self, vals, key):
        """Example: prepare nfe40_enderEmit partner legal_name and name
        by reading nfe40_xNome and nfe40_xFant on nfe40_emit"""
        key_vals = {}
        for k, v in self.fields_get().items():
            if v.get('related') is not None\
                    and hasattr(v['related'], '__len__')\
                    and len(v['related']) == 2\
                    and v['related'][0] == key\
                    and vals.get(k) is not None:
                key_vals[v['related'][1]] = vals[k]
        # if key_vals != {}:
        #     _logger.info("\nEXTRACT RELATED FROM PARENT:", self, key, key_vals)
        # TODO use inside match_or_create??
        return key_vals

    @api.model
    def _prepare_import_dict(self, vals, defaults=False):
        """NOTE: this is debatable if we could use an api multi with values in
        self instead of the vals dict. Then that would be like when new()
        is used in account_invoice or sale_order before playing some onchanges
        """

        if not defaults:
            defaults = dict()  # FIXME: default not used

        related_many2ones = {}
        fields = self.fields_get()
        for k, v in fields.items():
            # select schema choices for a friendly UI:
            if k.startswith('nfe40_choice'):  # TODO schema wise
                for item in v.get('selection', []):
                    if vals.get(item[0]) not in [None, []]:
                        vals[k] = item[0]
                        break

            # reverse map related fields as much as possible
            elif v.get('related') is not None and vals.get(k) is not None:
                if len(v['related']) == 1:
                    vals[v['related'][0]] = vals.get(k)
                elif len(v['related']) == 2 and k.startswith('nfe40_'):  # TODO
                    related_m2o = v['related'][0]
                    # don't mess with _inherits write system
                    if not any(related_m2o == i[1]
                               for i in self._inherits.items()):
                        key_vals = related_many2ones.get(related_m2o, {})
                        key_vals[v['related'][1]] = vals.get(k)
                        related_many2ones[related_m2o] = key_vals

        # now we deal with the related m2o with compound related
        for related_m2o, sub_val in related_many2ones.items():
            comodel_name = fields[related_m2o]['relation']
            comodel = self.get_concrete_model(comodel_name)
            related_many2ones = \
                self._verify_related_many2ones(related_many2ones)
            if hasattr(comodel, 'match_or_create_m2o'):
                vals[related_m2o] = comodel.match_or_create_m2o(sub_val, vals,
                                                                True)
            else:  # res.country for instance
                vals[related_m2o] = self.match_or_create_m2o(sub_val, vals,
                                                             True, comodel)
        return vals

    def _verify_related_many2ones(self, related_many2ones):
        return related_many2ones

    @api.model
    def match_record(self, rec_dict, parent_dict, model=None):
        """ inpsired from match_* methods from
        https://github.com/OCA/edi/blob/11.0/base_business_document_import
        /models/business_document_import.py"""
        if model is None:
            model = self
        default_key = [model._rec_name or model._concrete_rec_name or 'name']
        if hasattr(model, '_nfe_search_keys'):  # TODO make schema wise
            keys = model._nfe_search_keys + default_key
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

    def _get_aditional_keys(self, model, rec_dict, keys):
        return keys

    @api.model
    def match_or_create_m2o(self, rec_dict, parent_dict,
                            create_m2o=False, model=None):
        """Often the parent_dict can be used to refine the search.
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
            if create_m2o:
                r = model.create(rec_dict)
                # _logger.info('r %s', r)
                rec_id = r.id
            else:  # do we use it?
                rec_id = model.new(rec_dict).id
        return rec_id
