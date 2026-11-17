# Copyright (C) 2026 - Antônio S. Pereira Neto - Engenere <neto@engenere.one>
# Copyright (C) 2026 - Felipe Motter - Engenere <felipe@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

MODELS = ("res.partner", "res.company")


def _expected_stripped(vat):
    # Same rule as _compute_cnpj_cpf_stripped (str.isalnum keeps the
    # alphanumeric CNPJ of NT 2025.001, which a SQL regexp would not).
    return "".join(char for char in vat if char.isalnum()) if vat else False


def recompute_cnpj_cpf_stripped(env):
    """Recompute ``cnpj_cpf_stripped`` where it got out of sync with ``vat``.

    Up to 15.0 the field was computed from ``cnpj_cpf``; 0f43819c moved the
    dependency to ``vat`` without recomputing the existing rows. Records whose
    ``vat`` and ``cnpj_cpf`` differed kept the old value -- typically contacts
    that got ``vat`` from their parent (a commercial field) but never had a
    ``cnpj_cpf``, left with ``vat`` filled and an empty stripped value.
    """
    for model_name in MODELS:
        model = env[model_name].with_context(active_test=False)
        records = model.search([])
        stale = records.filtered(
            lambda rec: (rec.cnpj_cpf_stripped or False)
            != (_expected_stripped(rec.vat) or False)
        )
        if not stale:
            continue
        env.add_to_compute(model._fields["cnpj_cpf_stripped"], stale)
        stale.flush_recordset(["cnpj_cpf_stripped"])
        _logger.info(
            "%s: recomputed cnpj_cpf_stripped on %d record(s)",
            model_name,
            len(stale),
        )


@openupgrade.migrate()
def migrate(env, version):
    recompute_cnpj_cpf_stripped(env)
