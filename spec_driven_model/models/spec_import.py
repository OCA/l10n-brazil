import re
from datetime import datetime
from odoo import api, models


tz_datetime = re.compile(r'.*[-+]0[0-9]:00$')


class AbstractSpecMixin(models.AbstractModel):
    _inherit = 'spec.mixin'

    @api.model
    def build(self, node, defaults={}):
        # TODO new or create choice
        # TODO ability to match existing record here
        # TODO use SpecModel._get_concrete(...)
        model_name = models.MetaModel.mixin_mappings.get(self._name,
                                                         self._name)
        model = self.env[model_name]
        attrs = model.build_attrs(node, create_m2o=True, defaults=defaults)
        print(attrs)
        return model.create(attrs)

    @api.model
    def build_attrs(self, node, create_m2o=False, path='', defaults={}):
        """A recursive Odoo object builder that works along with the
        GenerateDS object builder from the parsed XML.
        Here we take into account the concrete Odoo objects where the schema
        mixins where injected and possible matcher or builder overrides."""
        print("\n\n %s BUILD_ATTRS %s %s " % (path, self, node,))
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
            value = getattr(node, attr.get_name())
            if value is None or value == []:
                continue
            key = "nfe40_%s" % (attr.get_name(),)  # TODO schema wise
            child_path = '%s.%s' % (path, key)

            if key.startswith('nfe40_ICMS') and key not in [
                    'nfe40_ICMS', 'nfe40_ICMSTot', 'nfe40_ICMSUFDest']:
                vals['nfe40_choice11'] = key

            if key.startswith('nfe40_IPI') and key != 'nfe40_IPI':
                vals['nfe40_choice3'] = key

            if key.startswith('nfe40_PIS') and key not in [
                    'nfe40_PIS', 'nfe40_PISST']:
                vals['nfe40_choice12'] = key

            if key.startswith('nfe40_COFINS') and key not in [
                    'nfe40_COFINS', 'nfe40_COFINSST']:
                vals['nfe40_choice15'] = key

            if attr.get_child_attrs().get('type') is None\
                    or attr.get_child_attrs().get('type') == 'xs:string':
                # SimpleType
                if fields[key]['type'] == 'datetime':
                    if 'T' in value:
                        if tz_datetime.match(value):
                            old_value = value
                            tz = old_value[19:]
                            value = old_value[:19]
                            # TODO see python3/pysped/xml_sped/base.py#L692
                        value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')

                if key not in ['nfe40_CST', 'nfe40_modBC', 'nfe40_CSOSN']:
                    vals[key] = value  # TODO avoid collision with cls prefix
                elif key == 'nfe40_CST':
                    if node.original_tagname_.startswith('ICMS'):
                        vals['icms_cst_id'] = \
                            self.env['l10n_br_fiscal.cst'].search(
                                [('code', '=', value),
                                 ('tax_domain', '=', 'icms')])[0].id
                    if node.original_tagname_.startswith('IPI'):
                        vals['ipi_cst_id'] = \
                            self.env['l10n_br_fiscal.cst'].search(
                                [('code', '=', value),
                                 ('tax_domain', '=', 'ipi')])[0].id
                    if node.original_tagname_.startswith('PIS'):
                        vals['pis_cst_id'] = \
                            self.env['l10n_br_fiscal.cst'].search(
                                [('code', '=', value),
                                 ('tax_domain', '=', 'pis')])[0].id
                    if node.original_tagname_.startswith('COFINS'):
                        vals['cofins_cst_id'] = \
                            self.env['l10n_br_fiscal.cst'].search(
                                [('code', '=', value),
                                 ('tax_domain', '=', 'cofins')])[0].id
                elif key == 'nfe40_modBC':
                    vals['icms_base_type'] = value

            else:
                # ComplexType
                print("\n\nNEW COMPLEX TYPE", key, value)
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
                    print("m2o or stacked", self, key, comodel_name,
                          comodel)
                    new_value = comodel.build_attrs(value,
                                                    create_m2o=create_m2o,
                                                    path=child_path,
                                                    defaults=defaults)
                    print("NEW_VALUE", self._name, key, comodel._name,
                          new_value)
                    child_defaults = self._extract_related_values(vals, key)

                    new_value.update(child_defaults)
#                    if key == 'nfe40_dest':
#                        print("KKKKKKK00", key, new_value, vals)
#                        x=a/0
                    if comodel._name == self._name\
                            or self._name == 'account.invoice.line'\
                            and comodel._name == 'l10n_br_fiscal.document.line'\
                            or self._name == 'account.invoice'\
                            and comodel._name == 'l10n_br_fiscal.document':
                        # TODO do not hardcode!!
                        # stacked m2o
                        vals.update(new_value)
                        print("(stacked)", self)
                    else:
                        vals[key] = comodel.match_or_create_m2o(new_value, vals,
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

        vals = self._prepare_import_dict(vals, defaults=defaults)
        return vals

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
                    and len(v['related']) == 2\
                    and v['related'][0] == key\
                    and vals.get(k) is not None:
                key_vals[v['related'][1]] = vals[k]
        if key_vals != {}:
            print("\nEXTRACT RELATED FROM PARENT:", self, key, key_vals)
        # TODO use inside match_or_create??
        return key_vals

    @api.model
    def _prepare_import_dict(self, vals, defaults={}):
        """NOTE: this is debatable if we could use an api multi with values in
        self instead of the vals dict. Then that would be like when new()
        is used in account_invoice or sale_order before playing some onchanges
        """
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
                    if not any(related_m2o == i[1]\
                               for i in self._inherits.items()):
                        key_vals = related_many2ones.get(related_m2o, {})
                        key_vals[v['related'][1]] = vals.get(k)
                        related_many2ones[related_m2o] = key_vals

        # now we deal with the related m2o with compound related
        for related_m2o, sub_val in related_many2ones.items():
            comodel_name = fields[related_m2o]['relation']
            comodel = self.get_concrete_model(comodel_name)
            if related_many2ones.get('product_id', {}).get('barcode') and \
                    related_many2ones['product_id']['barcode'] == 'SEM GTIN':
                del related_many2ones['product_id']['barcode']
            if hasattr(comodel, 'match_or_create_m2o'):
                vals[related_m2o] = comodel.match_or_create_m2o(sub_val, vals,
                                                                True)
            else:  # res.country for instance
                vals[related_m2o] = self.match_or_create_m2o(sub_val, vals,
                                                             True, comodel)
                print("related_m2o found", related_m2o, vals[related_m2o])
        return vals

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
        print("match_record", keys, rec_dict)
        if model._name == 'product.product' and rec_dict.get('barcode'):
            keys = ['barcode'] + keys
        for key in keys:
            if rec_dict.get(key):
                # TODO enable to build criteria using parent_dict
                # such as state_id when searching for a city
                if hasattr(model, '_nfe_extra_domain'):
                    domain = model._nfe_extra_domain + [(key, '=',
                                                         rec_dict.get(key))]
                else:
                    domain = [(key, '=', rec_dict.get(key))]
                print('domain', domain)
                match_ids = model.search(domain)
                print("\nSEARCH", model, key, rec_dict.get(key), match_ids)
                if match_ids:
                    if len(match_ids) > 1:
                        print("!! WARNING more than 1 record found!!")
                    return match_ids[0].id
        return False

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
        print("match or create", model, rec_dict, parent_dict)
        if hasattr(model, '_match_record'):
            rec_id = model.match_record(rec_dict, parent_dict, model)
        else:
            rec_id = self.match_record(rec_dict, parent_dict, model)
        if not rec_id:
            if create_m2o:
                r = model.create(rec_dict)
                print('r', r)
                rec_id = r.id
            else:  # do we use it?
                rec_id = model.new(rec_dict).id
        return rec_id
