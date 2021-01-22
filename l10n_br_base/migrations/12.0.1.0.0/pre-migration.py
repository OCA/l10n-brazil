# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA - Gabriel Cardoso de Faria
# Copyright (C) 2020 - TODAY Magno Costa - Akretion
# Copyright (C) 2021 - TODAY Raphaël Valyi - Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    cr = env.cr

    # banks:
    cr.execute('''select b.id, b.code_bc, m.name from res_bank as b
    JOIN ir_model_data as m on m.res_id=b.id and m.model='res.bank'
    WHERE b.code_bc IS NOT NULL;''')
    banks = cr.fetchall()
    xml_ids_banks_renames_fake = []
    xml_ids_banks_renames = []
    for row in banks:
        print("row", row)
        xml_ids_banks_renames_fake.append(
            ("l10n_br_base.%s" % (row[2],),
             "l10n_br_base.res_bank_fake_%s" % (row[1],)))
        xml_ids_banks_renames.append(
            ("l10n_br_base.res_bank_fake_%s" % (row[1],),
             "l10n_br_base.res_bank_%s" % (row[1],)))
    openupgrade.rename_xmlids(env.cr, xml_ids_banks_renames_fake)
    openupgrade.rename_xmlids(env.cr, xml_ids_banks_renames)

    # cities:
    openupgrade.add_fields(
        env,
        [
            ('ibge_code', 'res.city', False, 'char', False, False)
        ]
    )
    brasil_id = env.ref('base.br').id
    openupgrade.logged_query(
        cr,
        """
        INSERT INTO res_city(id, name, ibge_code, state_id, country_id)
        SELECT id, name, ibge_code, state_id, %s FROM l10n_br_base_city;
        """ % (brasil_id,)
    )

    openupgrade.logged_query(
        cr,
        """
        UPDATE ir_model_data SET model='res.city'
        WHERE model='l10n_br_base.city' AND name ilike 'city_%';
        """
    )
    openupgrade.logged_query(
        cr,
        '''
        UPDATE ir_ui_view set active=False WHERE id IN (
        SELECT res_id FROM ir_model_data WHERE name IN (
        'view_l10n_br_base_partner_form', 'view_company_form_inherited'));
        '''
    )
    openupgrade.logged_query(
        cr,
        """
        update res_country set address_format=NULL
        WHERE code='BR'
        """
    )
