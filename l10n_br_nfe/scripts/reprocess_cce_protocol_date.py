# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Optional: fix protocol_date of CC-e stored with the local time instead of UTC.

Never run by the module. It reads dhRegEvento again from the stored XML, is
idempotent and is a dry-run by default.

    odoo shell -d <database> < l10n_br_nfe/scripts/reprocess_cce_protocol_date.py

To write the changes (and commit):

    CCE_APPLY=1 odoo shell -d <database> < \
        l10n_br_nfe/scripts/reprocess_cce_protocol_date.py

Test it in a copy of the database first.
"""

import logging
import os
from collections import Counter

_logger = logging.getLogger("reprocess_cce_protocol_date")

apply = os.environ.get("CCE_APPLY") == "1"
report = env["l10n_br_fiscal.event"]._reprocess_cce_protocol_date(  # noqa: F821
    apply=apply
)
_logger.info("CC-e protocol_date (%s)", "APPLY" if apply else "DRY-RUN")
for line in report:
    _logger.info(
        "event %(event_id)s seq %(sequence)s key %(document_key)s: "
        "%(current)s -> %(expected)s: %(action)s",
        line,
    )
counts = Counter(line["action"].split(" ")[0] for line in report)
_logger.info(
    "%s to fix, %s fixed, %s ok, %s skipped",
    counts["fix"],
    counts["fixed"],
    counts["ok"],
    counts["skipped"],
)
if apply:
    env.cr.commit()  # noqa: F821
