# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA - Luis Felipe Mileo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


_xmlid_renames = [
    ('l10n_br_base.br_ac', 'base.state_br_ac'),
    ('l10n_br_base.br_al', 'base.state_br_al'),
    ('l10n_br_base.br_am', 'base.state_br_am'),
    ('l10n_br_base.br_ap', 'base.state_br_ap'),
    ('l10n_br_base.br_ba', 'base.state_br_ba'),
    ('l10n_br_base.br_ce', 'base.state_br_ce'),
    ('l10n_br_base.br_df', 'base.state_br_df'),
    ('l10n_br_base.br_es', 'base.state_br_es'),
    ('l10n_br_base.br_go', 'base.state_br_go'),
    ('l10n_br_base.br_ma', 'base.state_br_ma'),
    ('l10n_br_base.br_mg', 'base.state_br_mg'),
    ('l10n_br_base.br_ms', 'base.state_br_ms'),
    ('l10n_br_base.br_mt', 'base.state_br_mt'),
    ('l10n_br_base.br_pa', 'base.state_br_pa'),
    ('l10n_br_base.br_pb', 'base.state_br_pb'),
    ('l10n_br_base.br_pe', 'base.state_br_pe'),
    ('l10n_br_base.br_pi', 'base.state_br_pi'),
    ('l10n_br_base.br_pr', 'base.state_br_pr'),
    ('l10n_br_base.br_rj', 'base.state_br_rj'),
    ('l10n_br_base.br_rn', 'base.state_br_rn'),
    ('l10n_br_base.br_ro', 'base.state_br_ro'),
    ('l10n_br_base.br_rr', 'base.state_br_rr'),
    ('l10n_br_base.br_rs', 'base.state_br_rs'),
    ('l10n_br_base.br_sc', 'base.state_br_sc'),
    ('l10n_br_base.br_se', 'base.state_br_se'),
    ('l10n_br_base.br_sp', 'base.state_br_sp'),
    ('l10n_br_base.br_to', 'base.state_br_to'),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_xmlids(env.cr, _xmlid_renames)
