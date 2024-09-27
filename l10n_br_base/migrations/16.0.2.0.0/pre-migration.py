# Copyright 2024 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # if cnpj_cpf is a CPF, then we will move it to the new
    # l10n_br_cpf_code field in the post-migration script,
    # but for now, copy both CNPJ and CPF to the vat column
    openupgrade.logged_query(
        env.cr, "UPDATE res_partner SET vat=cnpj_cpf where cnpj_cpf IS NOT NULL"
    )
