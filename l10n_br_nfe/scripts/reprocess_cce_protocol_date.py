# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Optional, by hand: fix protocol_date of CC-e registered before the UTC fix.

Dry-run by default; CCE_APPLY=1 writes. Idempotent. Test on a copy first:

    CCE_APPLY=1 odoo shell -d <database> < \
        l10n_br_nfe/scripts/reprocess_cce_protocol_date.py
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
