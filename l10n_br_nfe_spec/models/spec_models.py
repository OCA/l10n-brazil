import re
from datetime import datetime
from odoo import models, fields, api


tz_datetime = re.compile(r'.*[-+]0[0-9]:00$')


class AbstractSpecMixin(models.AbstractModel):
    _description = "Abstract Model"
    _stack_path = ""
    _name = 'abstract.spec.mixin'

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moeda',
        compute='_compute_currency_id',
        default=lambda self: self.env.ref('base.BRL').id,
    )

    def _compute_currency_id(self):
        for item in self:
            item.currency_id = self.env.ref('base.BRL').id


    @api.model
    def build(self, node, defaults={}):
        attrs = self.build_attrs(node, create_m2o=True, defaults=defaults)
        #print(attrs)
        return self.new(attrs)

    @api.model
    def build_attrs(self, node, create_m2o=False, defaults={}):
        fields = self.fields_get()
        vals = self.default_get(fields.keys())
        for attr in node.member_data_items_:
            value = getattr(node, attr.get_name())
            if value is None:
                continue
            key = "nfe40_%s" % (attr.get_name(),) # TODO
            if attr.get_child_attrs().get('type') is None or attr.get_child_attrs().get('type') == 'xs:string':
                # SimpleType
                if False:#isinstance(value, str) and 'T' in value:
                    print('AAAAHHHH', value, key, fields[key]['type'])
                    m=k/0

                if fields[key]['type'] == 'datetime':
                    if 'T' in value:
                        if tz_datetime.match(value):
                            old_value = value
                            tz = old_value[19:]
                            value = old_value[:19]
                            # TODO https://github.com/aricaldeira/PySPED/blob/python3/pysped/xml_sped/base.py#L692
                        print('TTTTTTTTTT', value, key)
                        value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')

                vals[key] = value
            else:
                # ComplexType
                if fields.get(key) and fields[key].get('related'):
                    key = fields[key]['related'][0]
                    comodel_name = fields[key]['relation']
                else:
                    clean_type = attr.get_child_attrs()['type'].replace('Type', '').lower()
                    comodel_name = "nfe.40.%s" % (clean_type,)  # TODO clean

                comodel = self.get_field_comodel(comodel_name)

                if attr.get_container() == 0:
                    # m2o
                    new_value = comodel.build_attrs(value, create_m2o=create_m2o, defaults=defaults)
                    # print('-----', self._name, key, comodel_name, comodel, comodel._concrete_class)
                    if comodel._name == self._name:  # stacked m2o
                        vals.update(new_value)
                    else:
                        vals[key] = self.match_or_create_m2o(comodel, new_value, create_m2o)
                elif attr.get_container() == 1:
                    # o2m
                    lines = []
                    for line in [l for l in value if l]:
                        line_vals = comodel.build_attrs(line, create_m2o=create_m2o, defaults=defaults)
                        #line_vals.update({'name': 'TODO', 'price_unit': 0, 'display_type': 'line_section'})
                        lines.append((0, 0, line_vals))
                    vals[key] = lines

        for k, v in fields.items():
            #if k == 'nfe_qCom':
            #    print("WWWWWWWWWWWWWWWWWWWWWWWWWWW", self, node, v.get('related'), '=', vals.get(k), vals.get('nfe_qTrib'), vals.get('nfe_xProd'))
            if v.get('related') is not None\
                    and len(v['related']) == 1\
                    and vals.get(k) is not None:
                #if k == 'nfe_qCom':
                #    print("RRRRRRRRRRRRRRRRR", self, v['related'][0], '=', vals.get(k))
                vals[v['related'][0]] = vals.get(k)
        if defaults.get(self._name):
            vals.update(defaults[self._name])

        return vals

    @api.model
    def get_field_comodel(self, comodel_name):
        if hasattr(models.MetaModel, 'mixin_mappings') \
                and models.MetaModel.mixin_mappings.get(comodel_name) is not None:
            return self.env[models.MetaModel.mixin_mappings[comodel_name]]
        else:
            return self.env[comodel_name]

    @api.model
    def match_or_create_m2o(self, comodel, new_value, create_m2o=False):
        if comodel._name == 'res.company': # TODO no hardcode!!
            match_ids = self.search([('name', '=', new_value.get('name'))])
            if match_ids:
                return match_ids[0]
        elif create_m2o:
            if new_value.get(comodel._rec_name) is None:
                #ttype = comodel.fields_get()[comodel._rec_name]['ttype']
                #if ttype
                if 'nfe.' not in comodel._name: # TODO
                    new_value[comodel._rec_name] = 'TODO'
            rec = comodel.new(new_value)
            #rec.write(new_value) # trigger inverse fields
            return rec.id
        else:
            return new_value
