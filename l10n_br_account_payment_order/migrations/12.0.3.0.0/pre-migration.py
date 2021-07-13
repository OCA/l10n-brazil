# @ 2020 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openupgradelib import openupgrade

_table_renames = [
    ("cnab_return_move_code", "l10n_br_cnab_return_move_code"),
]

_model_renames = [
    ("cnab.return.move.code", "l10n_br_cnab.return.move.code"),
    ("cnab.return.log", "l10n_br_cnab.return.log"),
    ("cnab.return.event", "l10n_br_cnab.return.event"),
    ("cnab.return.lot", "l10n_br_cnab.return.lot"),
]


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    openupgrade.rename_tables(env.cr, _table_renames)
    openupgrade.rename_models(env.cr, _model_renames)
