# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA - Gabriel Cardoso de Faria
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

_model_renames = [
    ('l10n_br_base.city', 'res.city'),
]

_table_renames = [
    ('l10n_br_base_city', 'res_city'),
]


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    openupgrade.rename_models(cr, _model_renames)
    openupgrade.rename_tables(cr, _table_renames)
    cr.execute(
        '''INSERT INTO state_tax_numbers(id, inscr_est, partner_id, state_id)
        SELECT nextval('state_tax_numbers_id_seq'), inscr_est, partner_id,
        state_id FROM other_inscricoes_estaduais;
        ''')
    cr.execute(
        '''UPDATE res_partner rp SET city_id=(
        SELECT id FROM res_city WHERE ibge_code=(
        SELECT ibge_code FROM l10n_br_base_city WHERE id=rp.l10n_br_city_id))
        ''')
