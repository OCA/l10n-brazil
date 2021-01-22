# Copyright 2018 KMEE INFORMATICA LTDA - Gabriel Cardoso de Faria
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    openupgrade.logged_query(
        cr,
        '''INSERT INTO state_tax_numbers(id, inscr_est, partner_id, state_id)
        SELECT nextval('state_tax_numbers_id_seq'), inscr_est, partner_id,
        state_id FROM other_inscricoes_estaduais;
        '''
    )
    openupgrade.logged_query(
        cr,
        '''UPDATE res_partner rp SET city_id=(
        SELECT id FROM res_city WHERE ibge_code=(
        SELECT ibge_code FROM l10n_br_base_city WHERE id=rp.l10n_br_city_id)
        LIMIT 1)
        '''
    )
