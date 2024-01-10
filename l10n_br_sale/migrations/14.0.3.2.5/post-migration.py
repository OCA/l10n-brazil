from openupgradelib import openupgrade

_field_renames = [
    ('res.company', 'res_company', 'delivery_costs', None),
]

@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(env.cr, 'res_company', 'delivery_costs'):
        openupgrade.drop_columns(env.cr, _field_renames)
