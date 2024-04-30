# Copyright 2024 - TODAY KMEE - Diego Paradeda <diego.paradeda@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

naturalidade_rename = [
    (
        "hr.employee",
        "hr_employee",
        "naturalidade",
        "birth_city_id",
    ),
]

tipo_rename = [
    (
        "hr.employee",
        "hr_employee",
        "tipo",
        "employee_relationship_type",
    ),
]


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not openupgrade.column_exists(env.cr, "hr_employee", "birth_city_id"):
        openupgrade.rename_fields(env, naturalidade_rename)
    if not openupgrade.column_exists(
        env.cr, "hr_employee", "employee_relationship_type"
    ):
        openupgrade.rename_fields(env, tipo_rename)
