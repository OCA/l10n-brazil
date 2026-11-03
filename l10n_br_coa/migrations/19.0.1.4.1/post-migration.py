# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Make the refund repartition of deductible and withholding taxes symmetric.

`_update_repartition_lines` gave the invoice tax line a factor of -100 but left
the refund one at +100 when the tax had no refund account. Core requires both
distributions to match (`_validate_repartition_lines`), and embedding the
Factur-X in the invoice PDF validates the taxes, so the download failed.

The refund tax line takes the factor of the invoice tax line. Only taxes whose
distributions disagree are written, so the script is idempotent.
"""

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    taxes = (
        env["account.tax"]
        .with_context(active_test=False)
        .search(["|", ("deductible", "=", True), ("withholdable", "=", True)])
    )
    fixed = 0
    for tax in taxes:
        invoice_lines = tax.invoice_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        ).sorted()
        refund_lines = tax.refund_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        ).sorted()
        if len(invoice_lines) != len(refund_lines):
            continue
        for invoice_line, refund_line in zip(invoice_lines, refund_lines, strict=True):
            if refund_line.factor_percent != invoice_line.factor_percent:
                refund_line.factor_percent = invoice_line.factor_percent
                fixed += 1
    _logger.info("l10n_br_coa: %s refund repartition lines made symmetric", fixed)
