# Copyright 2025-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Backfill the ir.model.data entries of the fiscal data records lacking one.

Why this has to run BEFORE the module update (and not only after it)
=====================================================================

A database coming from an older series (v17 migrated to 18.0, or an 18.0
database whose records were entered by hand) holds fiscal data records
without any ``ir.model.data`` (xmlid) row. The ``data/*.csv`` files of
``l10n_br_fiscal`` are loaded *during* the module update, and the loader
only matches an existing record through its xmlid. Without one, Odoo tries
to INSERT a new row and dies on the model unique constraint, e.g.::

    duplicate key value violates unique constraint
    "l10n_br_fiscal_tax_fiscal_tax_code_uniq"
    Key (name)=(IRPJ RET 1%) already exists

A post-migration is too late: the crash happens while the data files are
loaded, which is before any post script runs. Hence this pre-migration,
written with plain SQL (the ORM cannot be trusted here: the columns of the
new series do not all exist yet) and idempotent by construction.

Two passes, in this order:

1. ``_backfill_from_data_files``: the module data files are parsed to learn
   the official xmlid of each record they ship, and that xmlid is attached
   to the pre-existing record carrying the same identity (the model unique
   key: ``name`` for a tax, ``code`` for a CFOP, ...). This is the pass that
   really saves the update: without it the loader would still insert a
   duplicate (the naming convention does not always match the data file, a
   tax named "IRPJ RET 1%" is ``tax_irpj_wh_1_percent`` in the CSV while the
   convention computes ``tax_irpj_wh_1``).

2. ``_backfill_from_conventions``: mirrors, in plain Python, the
   ``_get_xml_id_name()`` conventions of the editable data models so that a
   record entered by hand gets the very xmlid the mixin would have given it.
   This protects the records the data files do not ship.
"""

import csv
import logging
import os

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

MODULE = "l10n_br_fiscal"
# migrations/<version>/pre-migration.py -> <version>, migrations, l10n_br_fiscal
MODULE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

# model -> (table, columns that identify the record in the module data files)
DATA_FILE_IDENTITIES = {
    "l10n_br_fiscal.tax": ("l10n_br_fiscal_tax", ("name",)),
    "l10n_br_fiscal.tax.pis.cofins": ("l10n_br_fiscal_tax_pis_cofins", ("code",)),
    "l10n_br_fiscal.cst": ("l10n_br_fiscal_cst", ("code", "tax_group_id")),
    "l10n_br_fiscal.cfop": ("l10n_br_fiscal_cfop", ("code",)),
    "l10n_br_fiscal.cnae": ("l10n_br_fiscal_cnae", ("code",)),
    "l10n_br_fiscal.cest": ("l10n_br_fiscal_cest", ("code",)),
    "l10n_br_fiscal.nbm": ("l10n_br_fiscal_nbm", ("code",)),
    "l10n_br_fiscal.nbs": ("l10n_br_fiscal_nbs", ("code",)),
    "l10n_br_fiscal.ncm": ("l10n_br_fiscal_ncm", ("code", "exception")),
    "l10n_br_fiscal.service.type": ("l10n_br_fiscal_service_type", ("code",)),
    "l10n_br_fiscal.tax.classification": (
        "l10n_br_fiscal_tax_classification",
        ("code",),
    ),
    "l10n_br_fiscal.operation.indicator": (
        "l10n_br_fiscal_operation_indicator",
        ("code",),
    ),
}


def _strip(code, chars="."):
    code = code or ""
    for char in chars:
        code = code.replace(char, "")
    return code


def _fmt_amount(value):
    """Same formatting as Tax._get_xml_id_name's inner ``fmt`` helper."""
    value = float(value or 0.0)
    return f"{value:.4f}".rstrip("0").rstrip(".").replace(".", "_")


# --- plain SQL helpers -------------------------------------------------------


def _xmlid_to_res_id(cr, xmlid):
    """Resolve a module.xmlid reference of a data file to the record id."""
    if not xmlid:
        return None
    module, _, name = xmlid.partition(".")
    openupgrade.logged_query(
        cr,
        "SELECT res_id FROM ir_model_data WHERE module = %s AND name = %s",
        (module, name),
    )
    row = cr.fetchone()
    return row[0] if row else None


def _orphan_index(cr, table, model, columns):
    """Map the identity of every xmlid-less record of ``table`` to its id.

    Only the records without ir.model.data are fetched, so the index stays
    small whatever the size of the table.
    """
    cols = "".join(f', m."{column}"' for column in columns)
    openupgrade.logged_query(
        cr,
        f"""
        SELECT m.id{cols}
        FROM "{table}" m
        WHERE NOT EXISTS (
            SELECT 1 FROM ir_model_data d
            WHERE d.model = %s AND d.res_id = m.id
        )
        """,
        (model,),
    )
    index = {}
    for row in cr.fetchall():
        index.setdefault(tuple(row[1:]), []).append(row[0])
    return index


def _normalize(value):
    """NULL and empty strings identify the same record in the data files."""
    return "" if value in (None, False) else str(value)


def _insert_xmlid(cr, model, name, res_id, noupdate=True):
    """Attach ``name`` to ``res_id``, idempotently.

    ``ON CONFLICT DO NOTHING`` covers the unique index on
    (module, name) that Odoo creates on ir_model_data; the NOT EXISTS
    guard keeps the statement readable and skips the obvious case.
    """
    if not name:
        return False
    openupgrade.logged_query(
        cr,
        """
        INSERT INTO ir_model_data
            (module, name, model, res_id, noupdate,
             create_uid, create_date, write_uid, write_date)
        SELECT %s, %s, %s, %s, %s, 1, now(), 1, now()
        WHERE NOT EXISTS (
            SELECT 1 FROM ir_model_data d
            WHERE d.module = %s AND d.name = %s
        )
        ON CONFLICT DO NOTHING
        RETURNING id
        """,
        (MODULE, name, model, res_id, noupdate, MODULE, name),
    )
    return bool(cr.fetchone())


# --- pass 1: the official xmlids of the module data files -------------------


def _read_data_file(model):
    """Yield the rows of the CSV data file shipping ``model`` records."""
    path = os.path.join(MODULE_DIR, "data", f"{model}.csv")
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8", newline="") as csv_file:
        rows = []
        for row in csv.DictReader(csv_file):
            # data file headers look like "tax_group_id:id" / "uot_id:id"
            rows.append(
                {
                    key.split(":")[0]: value
                    for key, value in row.items()
                    if key is not None
                }
            )
        return rows


def _backfill_from_data_files(cr):
    """Give their data file xmlid to the records that already exist.

    Only the xmlid-less records are scanned, and an xmlid is attached only
    when the identity matches exactly one orphan record: a twice-created
    record must not be silently merged with the official one.
    """
    for model, (table, identity) in DATA_FILE_IDENTITIES.items():
        rows = _read_data_file(model)
        if not rows:
            continue
        index = _orphan_index(cr, table, model, identity)
        if not index:
            continue
        created = 0
        for row in rows:
            key = tuple(
                _normalize(_xmlid_to_res_id(cr, row.get(column)))
                if column.endswith("_id")
                else _normalize(row.get(column))
                for column in identity
            )
            record_ids = index.get(key)
            if not record_ids or len(record_ids) != 1:
                continue
            if _insert_xmlid(cr, model, row.get("id"), record_ids[0], noupdate=False):
                created += 1
        if created:
            _logger.info(
                "l10n_br_fiscal: %s data file xmlids attached to existing "
                "records of %s.",
                created,
                model,
            )


# --- pass 2: mirror of the _get_xml_id_name() conventions -------------------


def _cst_xml_id(row):
    _id, code, tax_domain = row
    if not tax_domain:
        return None
    return f"cst_{tax_domain}_{code}"


def _ncm_xml_id(row):
    _id, code, exception = row
    name = f"ncm_{_strip(code)}"
    if exception:
        name += f"_{exception}"
    return name


def _tax_xml_id(row):
    _id, name, tax_domain, value_amount, percent_amount, pdc, reduction = row
    if not tax_domain:
        return None
    name_lower = (name or "").lower()
    if tax_domain in ("pis", "cofins"):
        if "monofásico" in name_lower or "monofasico" in name_lower:
            if value_amount:
                return f"tax_{tax_domain}_value_{_fmt_amount(value_amount)}"
            return f"tax_{tax_domain}_monofasico_{_fmt_amount(percent_amount)}"
        if "aliq" in name_lower and "dif" in name_lower:
            return (
                f"tax_{tax_domain}_aliqdif_{_fmt_amount(pdc)}"
                f"_cred_{_fmt_amount(percent_amount)}"
            )
    res = f"tax_{tax_domain}_{_fmt_amount(percent_amount)}"
    if reduction:
        res += f"_red_{_fmt_amount(reduction)}"
    return res


def _piscofins_xml_id(row):
    _id, code, name, tax_pis_id, tax_cofins_id, pis_percent, cofins_percent = row
    code = (code or "").strip()
    name_lower = (name or "").lower()
    if "monofásico" in name_lower or "monofasico" in name_lower:
        return f"tax_piscofins_monofasico_{code}"
    if "substituição tributária" in name_lower or " st " in name_lower:
        return f"tax_pis_cofins_st_{code}"
    if "isenção" in name_lower or "isento" in name_lower:
        return f"tax_pis_cofins_isento_{code}"
    if "suspensão" in name_lower:
        return f"tax_pis_cofins_susp_{code}"
    if "sem incidência" in name_lower:
        return f"tax_pis_cofins_seminc_{code}"
    both_zero = tax_pis_id and not pis_percent and tax_cofins_id and not cofins_percent
    if both_zero:
        return f"tax_pis_cofins_0_{code}"
    if "r$" in name_lower:
        return f"tax_pis_cofins_value_{code}"
    if "cumulativo" in name_lower and "não" not in name_lower:
        return "tax_pis_cofins_columativo"
    if "não cumulativo" in name_lower:
        return "tax_pis_cofins_nao_columativo"
    if "simples nacional" in name_lower:
        return "tax_pis_cofins_simples_nacional"
    if "diferenciada" in name_lower:
        return "tax_pis_cofins_diferenciado"
    return f"tax_pis_cofins_{code}"


# model -> (table, sql selecting the columns after m.id, naming function)
CONVENTIONS = {
    "l10n_br_fiscal.cest": (
        "l10n_br_fiscal_cest",
        'm."code"',
        lambda row: f"cest_{_strip(row[1])}",
    ),
    "l10n_br_fiscal.cfop": (
        "l10n_br_fiscal_cfop",
        'm."code"',
        lambda row: f"cfop_{row[1]}",
    ),
    "l10n_br_fiscal.cnae": (
        "l10n_br_fiscal_cnae",
        'm."code"',
        lambda row: f"cnae_{_strip(row[1], './-')}",
    ),
    "l10n_br_fiscal.nbm": (
        "l10n_br_fiscal_nbm",
        'm."code"',
        lambda row: f"nbm_{_strip(row[1])}",
    ),
    "l10n_br_fiscal.nbs": (
        "l10n_br_fiscal_nbs",
        'm."code"',
        lambda row: f"nbs_{_strip(row[1])}",
    ),
    "l10n_br_fiscal.ncm": (
        "l10n_br_fiscal_ncm",
        'm."code", m."exception"',
        _ncm_xml_id,
    ),
    "l10n_br_fiscal.cst": (
        "l10n_br_fiscal_cst",
        'm."code", m."tax_domain"',
        _cst_xml_id,
    ),
    "l10n_br_fiscal.service.type": (
        "l10n_br_fiscal_service_type",
        'm."code"',
        lambda row: f"service_type_{_strip(row[1])}",
    ),
    "l10n_br_fiscal.tax.classification": (
        "l10n_br_fiscal_tax_classification",
        'm."code"',
        lambda row: f"tax_classification_{row[1]}",
    ),
    "l10n_br_fiscal.operation.indicator": (
        "l10n_br_fiscal_operation_indicator",
        'm."code"',
        lambda row: f"operation_indicator_{row[1]}",
    ),
    "l10n_br_fiscal.tax.pis.cofins": (
        "l10n_br_fiscal_tax_pis_cofins",
        'm."code", m."name", m."tax_pis_id", m."tax_cofins_id", '
        'pis."percent_amount", cofins."percent_amount"',
        _piscofins_xml_id,
    ),
    "l10n_br_fiscal.tax": (
        "l10n_br_fiscal_tax",
        'm."name", m."tax_domain", m."value_amount", m."percent_amount", '
        'm."percent_debit_credit", m."percent_reduction"',
        _tax_xml_id,
    ),
}

# the cst convention reads the tax domain of its tax group
# tax_domain is a stored related field, so it is read straight from the
# table: joining the tax group would silently drop the rows whose group is
# missing (legacy data) and those are exactly the ones to protect.
JOINS = {
    "l10n_br_fiscal_tax_pis_cofins": (
        'LEFT JOIN "l10n_br_fiscal_tax" pis ON pis.id = m."tax_pis_id" '
        'LEFT JOIN "l10n_br_fiscal_tax" cofins ON cofins.id = m."tax_cofins_id"'
    ),
}


def _backfill_from_conventions(cr):
    """Give the convention xmlid to the records left without any xmlid."""
    for model, (table, columns, name_fn) in CONVENTIONS.items():
        join = JOINS.get(table, "")
        openupgrade.logged_query(
            cr,
            f"""
            SELECT m.id, {columns}
            FROM "{table}" m
            {join}
            WHERE NOT EXISTS (
                SELECT 1 FROM ir_model_data d
                WHERE d.model = %s AND d.res_id = m.id
            )
            """,
            (model,),
        )
        created = 0
        for row in cr.fetchall():
            try:
                name = name_fn(row)
            except Exception:  # pragma: no cover - data driven, never fatal
                _logger.exception(
                    "l10n_br_fiscal: no xmlid convention for %s id %s.", model, row[0]
                )
                continue
            if _insert_xmlid(cr, model, name, row[0]):
                created += 1
        if created:
            _logger.info(
                "l10n_br_fiscal: %s conventional xmlids generated for %s.",
                created,
                model,
            )


@openupgrade.migrate()
def migrate(env, version):
    """Backfill the xmlids before the data files are loaded.

    Both passes only INSERT ir.model.data rows: no fiscal data is modified
    and the script can be re-run safely.
    """
    cr = env.cr
    _backfill_from_data_files(cr)
    _backfill_from_conventions(cr)
    cr.execute(
        """
        SELECT count(*) FROM ir_model_data
        WHERE module = %s AND noupdate
        """,
        (MODULE,),
    )
    _logger.info(
        "l10n_br_fiscal: %s noupdate xmlids known before the data file load.",
        cr.fetchone()[0],
    )
