# -*- coding: utf-8 -*-
# @ 2016 Akretion - www.akretion.com.br
# Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp.openupgrade import openupgrade


column_renames = {
    'crm_lead': [
        ('cnpj_cpf', 'cnpj'),
        ],
    }


@openupgrade.migrate()
def migrate(cr, version):
    openupgrade.rename_columns(
        cr, column_renames)
