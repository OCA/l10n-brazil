import logging

from odoo import SUPERUSER_ID, _, api, tools


_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """Import XML data to change core data"""
    env = api.Environment(cr, SUPERUSER_ID, {})

    files = [
        "data/l10n_br_cnab.structure.csv",
        "data/l10n_br_cnab.batch.csv",
        "data/l10n_br_cnab.line.csv",
        "data/l10n_br_cnab.line.field.csv",
    ]

    _logger.info(_("Loading l10n_br_cnab_structure data files..."))

    for file in files:
        tools.convert_file(
            cr,
            "l10n_br_cnab_structure",
            file,
            None,
            mode="init",
            noupdate=True,
            kind="init",
        )
