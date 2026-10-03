# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Fix the protocol_date of the correction letters (CC-e) already registered.

OPTIONAL and NEVER run by the module (not in post_init_hook, not in a
migration). Until the dhRegEvento was converted to UTC, protocol_date kept the
local time of Brasilia (UTC-03:00), three hours behind the UTC that the field
holds. This script reads dhRegEvento again from the XML that is stored in the
event and corrects the letters whose date differs. It is idempotent.

Dry-run is the default: it only prints what would change.

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
