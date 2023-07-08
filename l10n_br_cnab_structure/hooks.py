import logging

from odoo import _, tools

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """Import XML data to change core data"""

    files = [
        "data/l10n_br_cnab.structure.csv",
        "data/l10n_br_cnab.batch.csv",
        "data/cnab.payment.way.csv",
        "data/l10n_br_cnab.line.csv",
        "data/cnab.line.field.group.csv",
        "data/l10n_br_cnab.line.field.csv",
        "data/cnab.line.group.field.condition.csv",
        "data/cnab.occurrence.csv",
        "data/cnab.pix.key.type.csv",
        "data/cnab.pix.transfer.type.csv",
    ]

    _logger.info(_("Loading l10n_br_cnab_structure data files."))

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

    cr.execute("select demo from ir_module_module where name='l10n_br_cnab_structure';")
    if cr.fetchone()[0]:
        demofiles = [
            "demo/account_account.xml",
            "demo/account_journal.xml",
            "demo/payment_mode.xml",
            "demo/res_partner_bank.xml",
            "demo/account_invoice.xml",
        ]

        _logger.info(_("Loading l10n_br_cnab_structure demo files."))

        for file in demofiles:
            tools.convert_file(
                cr,
                "l10n_br_cnab_structure",
                file,
                None,
                mode="init",
                noupdate=True,
                kind="demo",
            )
