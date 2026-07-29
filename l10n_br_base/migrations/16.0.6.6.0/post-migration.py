# Copyright (C) 2026 - Felipe Motter Pereira - Trento Química
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

MODELS = ("res.partner", "res.company")


def recompute_cnpj_cpf_stripped(env):
    """Repopulate ``cnpj_cpf_stripped`` where it got out of sync with ``vat``.

    ``cnpj_cpf_stripped`` is a stored computed field depending on ``vat``, but
    the 16.0.2.0.0 pre-migration copied the legacy ``cnpj_cpf`` column into
    ``vat`` with a raw UPDATE:

        UPDATE res_partner SET vat = cnpj_cpf
         WHERE vat IS NULL AND cnpj_cpf IS NOT NULL;

    Raw SQL does not trigger a recompute, so every record it touched kept
    ``vat`` filled and ``cnpj_cpf_stripped`` NULL. Until now that was harmless
    because the duplicate check was dead code; it started reporting unrelated
    partners as duplicates once the check was revived.

    Recompute through the ORM rather than a SQL regexp: the compute uses
    ``str.isalnum()``, which keeps the alphanumeric CNPJ of NT 2025.001.
    """
    for model_name in MODELS:
        model = env[model_name].with_context(active_test=False)
        # Both fields are Char, so "empty" may be NULL or an empty string --
        # and ("vat", "!=", False) alone only maps to `vat IS NOT NULL`, which
        # would wrongly pick up records whose vat is '' (empty stripped is
        # correct for those).
        records = model.search(
            [
                ("vat", "not in", [False, ""]),
                "|",
                ("cnpj_cpf_stripped", "=", False),
                ("cnpj_cpf_stripped", "=", ""),
            ]
        )
        if not records:
            continue

        records.modified(["vat"])
        records._compute_cnpj_cpf_stripped()
        records.flush_recordset()
        _logger.info(
            "%s: recomputed cnpj_cpf_stripped on %d record(s)",
            model_name,
            len(records),
        )


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return
    recompute_cnpj_cpf_stripped(env)
