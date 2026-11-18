#!/usr/bin/env python3
# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Generate the l10n_br_fiscal_rtc data files from the official Receita Federal
Calculadora de Tributos (regime regular) repository.

The official project keeps every tax rule in a SQLite database built by Flyway
migrations.  This script replays those migrations into a throw-away SQLite
database and exports the tables we need as reviewable Odoo CSV data files.

Usage (from anywhere; the module paths are resolved from this file)::

    python3 l10n_br_fiscal_rtc/tools/sync_rtc_tables.py \\
        --src ~/DEV/rtc-receita/calculadora-rtc-regime-regular

    # CI / pre-commit: fail when the committed files are stale
    python3 l10n_br_fiscal_rtc/tools/sync_rtc_tables.py --src ... --check

The output is deterministic: same source, same bytes.  Every CSV is sorted and
every generated value comes from the source database, so a sync shows up as a
minimal diff.
"""

import argparse
import csv
import glob
import hashlib
import os
import shutil
import sqlite3
import sys
import tempfile

# Official TRIBUTO ids -> l10n_br_fiscal_rtc tax selection
TRIBUTO_MAP = {
    1: "is",
    2: "cbs",
    3: "ibs_uf",
    4: "ibs_mun",
}

# Official CLTR_TIPO_ALIQUOTA -> l10n_br_fiscal TAX_RATE_TYPE selection
RATE_TYPE_MAP = {
    "Fixa": "1",
    "Padrão": "2",
    "Sem alíquota": "3",
    "Uniforme nacional (referência)": "4",
    "Uniforme setorial": "5",
    "Alíquotas Combinadas (Ad Valorem e Ad Rem)": "1",
}

# Official CLTR_NOMENCLATURA -> selection value
NOMENCLATURE_MAP = {
    "NCM": "ncm",
    "NBS": "nbs",
    "NBS ou NCM": "nbs_ncm",
    "CIB": "cib",
    "CIB ou NCM": "cib_ncm",
    "Não possui": "none",
}

# Official CLTR_CREDITO_OPERACAO_ANTECEDENTE -> selection value
PRIOR_CREDIT_MAP = {
    "Manutenção": "maintain",
    "Anulação": "reverse",
}

CLASSIFICATION_UPDATE_FIELDS = [
    "id",
    # the ":id" suffix tells the Odoo CSV loader to resolve an xmlid
    "rtc_treatment_id:id",
    "rtc_reduction_cbs",
    "rtc_reduction_ibs_uf",
    "rtc_reduction_ibs_mun",
    "rtc_credit_acquirer_cbs",
    "rtc_credit_acquirer_ibs",
    "rtc_presumed_credit_supplier",
    "rtc_presumed_credit_acquirer",
    "rtc_prior_credit",
    "rtc_nomenclature",
    "rtc_legal_basis_id:id",
    "rtc_sn_revenue_type",
]

CLASSIFICATION_NEW_FIELDS = [
    "id",
    "code",
    "name",
    "rate_type",
    "date_start",
    "date_end",
] + CLASSIFICATION_UPDATE_FIELDS[1:]


def build_database(src, db_path):
    """Replay the official Flyway migrations into db_path."""
    sql_dir = os.path.join(src, "flyway", "sql")
    creation = os.path.join(sql_dir, "criacao")
    maintenance = os.path.join(sql_dir, "manutencao")
    if not os.path.isdir(creation):
        raise SystemExit(f"cannot find {creation}: is --src a calculadora clone?")

    files = []
    before = os.path.join(creation, "beforeMigrate.sql")
    if os.path.exists(before):
        files.append(before)
    files.extend(sorted(glob.glob(os.path.join(creation, "B*.sql"))))
    files.extend(sorted(glob.glob(os.path.join(maintenance, "V*.sql"))))

    con = sqlite3.connect(db_path)
    # The official baseline has known FK problems (see the header of B0001);
    # the project itself runs the maintenance scripts with FK checks relaxed.
    con.execute("PRAGMA foreign_keys = OFF")
    for path in files:
        with open(path, encoding="utf-8") as sql:
            con.executescript(sql.read())
        con.commit()
        con.execute("PRAGMA foreign_keys = OFF")
    return con, files


def q1(con, query, params=()):
    cur = con.execute(query, params)
    return cur.fetchone()


def rows(con, query, params=()):
    cur = con.execute(query, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r, strict=False)) for r in cur.fetchall()]


def fmt_date(value):
    """Official dates are 'YYYY-MM-DD' or full ISO timestamps."""
    if not value:
        return ""
    return str(value)[:10]


def fmt_bool(value):
    return "True" if value else "False"


def num(value):
    """Format a Decimal-ish value without exponents and without float noise."""
    if value is None:
        return ""
    text = f"{float(value):.10f}".rstrip("0").rstrip(".")
    return text or "0"


def write_xml_records(path, model, records, field_order, ref_fields=()):
    """Write records as Odoo XML so partial rows stay possible."""

    def escape(value):
        return (
            str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    lines = [
        '<?xml version="1.0" encoding="utf-8" ?>',
        '<odoo noupdate="1">',
    ]
    for record in records:
        lines.append(f'  <record id="{record["id"]}" model="{model}">')
        for field in field_order:
            value = record.get(field)
            if value in (None, ""):
                continue
            if field in ref_fields:
                lines.append(f'    <field name="{field}" ref="{value}"/>')
            else:
                lines.append(f'    <field name="{field}">{escape(value)}</field>')
        lines.append("    </record>")
    lines.extend(["</odoo>", ""])
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines))


def write_csv(path, fieldnames, records):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def sync_treatments(con):
    out = []
    for row in rows(con, "SELECT * FROM TRATAMENTO_TRIBUTARIO ORDER BY TRTR_ID"):
        out.append(
            {
                "id": f"rtc_treatment_{row['TRTR_ID']}",
                "code": row["TRTR_ID"],
                "name": row["TRTR_DESCRICAO"],
                "expr_rate": row["TRTR_EXPRESSAO_ALIQUOTA"] or "",
                "expr_effective_rate": row["TRTR_EXPRESSAO_ALIQUOTA_EFETIVA"] or "",
                "expr_base": row["TRTR_EXPRESSAO_BASE_CALCULO"] or "",
                "expr_tax_computed": row["TRTR_EXPRESSAO_TRIBUTO_CALCULADO"] or "",
                "expr_tax_due": row["TRTR_EXPRESSAO_TRIBUTO_DEVIDO"] or "",
                "expr_deferral_percent": row["TRTR_EXPRESSAO_PERCENTUAL_DIFERIMENTO"]
                or "",
                "expr_deferral_value": row["TRTR_EXPRESSAO_VALOR_DIFERIMENTO"] or "",
                "has_rate_reduction": fmt_bool(
                    row["TRTR_IN_POSSUI_PERCENTUAL_REDUCAO"]
                ),
                "has_reducer": fmt_bool(row["TRTR_IN_POSSUI_REDUTOR"]),
                "has_monophase": fmt_bool(row.get("TRTR_IN_POSSUI_MONOFASIA")),
                "has_adjustment": fmt_bool(row["TRTR_IN_POSSUI_AJUSTE"]),
                "incompatible_with_suspension": fmt_bool(
                    row["TRTR_IN_INCOMPATIVEL_COM_SUSPENSAO"]
                ),
                "requires_desoneration_group": fmt_bool(
                    row["TRTR_IN_EXIGE_GRUPO_DESONERACAO"]
                ),
                "date_start": fmt_date(row["TRTR_INICIO_VIGENCIA"]),
                "date_end": fmt_date(row["TRTR_FIM_VIGENCIA"]),
            }
        )
    return out


def sync_legal_basis(con):
    out = []
    for row in rows(con, "SELECT * FROM FUNDAMENTACAO_LEGAL ORDER BY FDLG_ID"):
        out.append(
            {
                "id": f"rtc_legal_basis_{row['FDLG_ID']}",
                "name": (row["FDLG_TEXTO_CURTO"] or "")[:128],
                "text": row["FDLG_TEXTO"] or "",
                "normative_reference": row["FDLG_REFERENCIA_NORMATIVA"] or "",
                "date_start": fmt_date(row["FDLG_INICIO_VIGENCIA"]),
                "date_end": fmt_date(row["FDLG_FIM_VIGENCIA"]),
            }
        )
    return out


def sync_rates(con):
    """Official reference rates, one row per tax and validity period."""
    out = []
    for row in rows(con, "SELECT * FROM ALIQUOTA_REFERENCIA ORDER BY ALRE_ID"):
        tax = TRIBUTO_MAP.get(row["ALRE_TBTO_ID"])
        if not tax:
            continue
        start = fmt_date(row["ALRE_INICIO_VIGENCIA"])
        out.append(
            {
                "id": f"rtc_rate_{tax}_{start.replace('-', '')}",
                "tax": tax,
                "rate": num(row["ALRE_VALOR"]),
                "date_start": start,
                "date_end": fmt_date(row["ALRE_FIM_VIGENCIA"]),
            }
        )
    return out


def sync_classifications(con, fiscal_ids, reference_date):
    """Current row per cClassTrib, with treatment, reductions and indicators.

    ``reference_date`` is the date of the official database version
    (``VERSAO_BASE_DADO.VRBD_DATA``), never the day the script runs: the
    output must be reproducible on any machine at any time.
    """
    current = rows(
        con,
        """
        SELECT c.* FROM CLASSIFICACAO_TRIBUTARIA c
        WHERE (c.CLTR_FIM_VIGENCIA IS NULL OR c.CLTR_FIM_VIGENCIA >= :ref)
          -- A code may have a CBS/IBS row and an Imposto Seletivo row (same
          -- cClassTrib, different situação tributária).  The IBS/CBS engine
          -- only cares about the row whose situação is bound to CBS/IBS.
          AND EXISTS (
            SELECT 1 FROM TRIBUTO_SITUACAO_TRIBUTARIA ts
            WHERE ts.TRST_SITR_ID = c.CLTR_SITR_ID
              AND ts.TRST_TBTO_ID IN (2, 3, 4)
          )
        ORDER BY c.CLTR_CD, c.CLTR_INICIO_VIGENCIA DESC
        """,
        {"ref": reference_date},
    )
    by_code = {}
    for row in current:
        by_code.setdefault(row["CLTR_CD"], row)

    reductions = {}
    for row in rows(con, "SELECT * FROM PERCENTUAL_REDUCAO"):
        reductions.setdefault(row["PERE_CLTR_ID"], {})[row["PERE_TBTO_ID"]] = row[
            "PERE_VALOR"
        ]
    treatment = {}
    for row in rows(
        con,
        "SELECT * FROM TRATAMENTO_CLASSIFICACAO"
        " WHERE TRCL_FIM_VIGENCIA IS NULL OR TRCL_FIM_VIGENCIA >= :ref"
        " ORDER BY TRCL_INICIO_VIGENCIA",
        {"ref": reference_date},
    ):
        treatment[row["TRCL_CLTR_ID"]] = row["TRCL_TRTR_ID"]
    legal = {}
    for row in rows(
        con,
        "SELECT * FROM FUNDAMENTACAO_CLASSIFICACAO"
        " WHERE FDCL_FIM_VIGENCIA IS NULL OR FDCL_FIM_VIGENCIA >= :ref"
        " ORDER BY FDCL_INICIO_VIGENCIA",
        {"ref": reference_date},
    ):
        legal[row["FDCL_CLTR_ID"]] = row["FDCL_FDLG_ID"]

    out = []
    new = []
    for code in sorted(by_code):
        row = by_code[code]
        cltr_id = row["CLTR_ID"]
        red = reductions.get(cltr_id, {})
        treatment_id = treatment.get(cltr_id)
        basis_id = legal.get(cltr_id)
        values = {
            "rtc_treatment_id:id": f"rtc_treatment_{treatment_id}"
            if treatment_id
            else "",
            "rtc_reduction_cbs": num(red.get(2)),
            "rtc_reduction_ibs_uf": num(red.get(3)),
            "rtc_reduction_ibs_mun": num(red.get(4)),
            "rtc_credit_acquirer_cbs": fmt_bool(
                row["CLTR_IN_APROPRIACAO_CREDITOS_ADQUIRENTES_CBS"]
            ),
            "rtc_credit_acquirer_ibs": fmt_bool(
                row["CLTR_IN_APROPRIACAO_CREDITOS_ADQUIRENTES_IBS"]
            ),
            "rtc_presumed_credit_supplier": fmt_bool(
                row["CLTR_IN_CREDITO_PRESUMIDO_FORNECEDOR"]
            ),
            "rtc_presumed_credit_acquirer": fmt_bool(
                row["CLTR_IN_CREDITO_PRESUMIDO_ADQUIRENTE"]
            ),
            "rtc_prior_credit": PRIOR_CREDIT_MAP.get(
                row["CLTR_CREDITO_OPERACAO_ANTECEDENTE"], ""
            ),
            "rtc_nomenclature": NOMENCLATURE_MAP.get(row["CLTR_NOMENCLATURA"], ""),
            "rtc_legal_basis_id:id": f"rtc_legal_basis_{basis_id}" if basis_id else "",
            "rtc_sn_revenue_type": row["CLTR_TPRBSN"]
            if row["CLTR_TPRBSN"] is not None
            else "",
        }
        if code in fiscal_ids:
            # Enrich the record already shipped by l10n_br_fiscal: never
            # rewrite its own fields (code, name, rate_type, dates, taxes).
            out.append(dict(values, id=f"l10n_br_fiscal.tax_classification_{code}"))
        else:
            new.append(
                dict(
                    values,
                    id=f"rtc_classification_{code}",
                    code=code,
                    name=row["CLTR_DESCRICAO"],
                    rate_type=RATE_TYPE_MAP.get(row["CLTR_TIPO_ALIQUOTA"], "2"),
                    date_start=fmt_date(row["CLTR_INICIO_VIGENCIA"]),
                    date_end=fmt_date(row["CLTR_FIM_VIGENCIA"]),
                )
            )
    return out, new, set(by_code)


def sync_nomenclature(con, kind):
    table = "NCM_APLICAVEL" if kind == "ncm" else "NBS_APLICAVEL"
    code_col = "NCMA_NCM_CD" if kind == "ncm" else "NBSA_NBS_CD"
    cltr_col = "NCMA_CLTR_ID" if kind == "ncm" else "NBSA_CLTR_ID"
    annex_col = "NCMA_ANXO_ID" if kind == "ncm" else "NBSA_ANXO_ID"
    start_col = "NCMA_INICIO_VIGENCIA" if kind == "ncm" else "NBSA_INICIO_VIGENCIA"
    end_col = "NCMA_FIM_VIGENCIA" if kind == "ncm" else "NBSA_FIM_VIGENCIA"

    cltr_codes = {
        row["CLTR_ID"]: row["CLTR_CD"]
        for row in rows(con, "SELECT CLTR_ID, CLTR_CD FROM CLASSIFICACAO_TRIBUTARIA")
    }
    annex = {
        row["ANXO_ID"]: row["ANXO_NUMERO"]
        for row in rows(con, "SELECT ANXO_ID, ANXO_NUMERO FROM ANEXO")
    }

    out = []
    seen = set()
    for row in rows(
        con,
        f"SELECT * FROM {table} ORDER BY {code_col}, {cltr_col}, {start_col}",
    ):
        classification = cltr_codes.get(row[cltr_col], "")
        start = fmt_date(row[start_col])
        record_id = (
            f"rtc_{kind}_{classification}_{row[code_col]}_{start.replace('-', '')}"
        )
        # The official base contains exact duplicate rows; keep one.
        if record_id in seen:
            continue
        seen.add(record_id)
        out.append(
            {
                "id": record_id,
                "classification_code": classification,
                "nomenclature_type": kind,
                "code": row[code_col],
                "annex": annex.get(row[annex_col]) or "",
                "date_start": start,
                "date_end": fmt_date(row[end_col]),
            }
        )
    return out


def sync_sn_activities(con):
    """Simples Nacional activities (cAtivSN) with their annex."""
    out = []
    for row in rows(
        con, "SELECT * FROM ATIVIDADE_SIMPLES_NACIONAL ORDER BY ATSN_ORDEM"
    ):
        out.append(
            {
                "id": f"rtc_sn_activity_{row['ATSN_ID']}",
                "code": f"{int(row['ATSN_CATIVSN']):02d}"
                if row["ATSN_CATIVSN"] is not None
                else "",
                "name": row["ATSN_DESCRICAO"] or "",
                "annex": row["ATSN_ANEXO_SEM_FATOR_R"] or "",
                "annex_with_factor_r": row["ATSN_ANEXO_COM_FATOR_R"] or "",
                "label": row["ATSN_ROTULO"] or "",
                "short_label": row["ATSN_ROTULO_CURTO"] or "",
                "not_taxable": fmt_bool(row["ATSN_IN_NAO_TRIBUTAVEL"]),
                "date_start": fmt_date(row["ATSN_INICIO_VIGENCIA"]),
                "date_end": fmt_date(row["ATSN_FIM_VIGENCIA"]),
            }
        )
    return out


def sync_sn_regimes(con):
    """Simples Nacional apuration matrix, by CRT."""
    out = []
    for row in rows(
        con, "SELECT * FROM REGIME_APURACAO_SIMPLES_NACIONAL ORDER BY RASN_CRT"
    ):
        out.append(
            {
                "id": f"rtc_sn_regime_{row['RASN_CRT']}",
                "crt": f"{row['RASN_CRT']}",
                "name": row["RASN_DESCRICAO"] or "",
                "generates_ibs": fmt_bool(row["RASN_IN_GERA_IBS"]),
                "destination_due": row["RASN_DESTINO_DEVIDO"] or "",
                "destination_pending": row["RASN_DESTINO_PENDENTE_SUSPENSO"] or "",
                "date_start": fmt_date(row["RASN_INICIO_VIGENCIA"]),
                "date_end": fmt_date(row["RASN_FIM_VIGENCIA"]),
            }
        )
    return out


def sync_sn_revenue_types(con):
    """Effect of the type of gross revenue (tpRBSN) on the Simples calculation."""
    out = []
    for row in rows(
        con, "SELECT * FROM TIPO_RECEITA_BRUTA_SIMPLES_NACIONAL ORDER BY TRBS_CD"
    ):
        out.append(
            {
                "id": f"rtc_sn_revenue_type_{row['TRBS_CD']}",
                "code": f"{row['TRBS_CD']}",
                "name": row["TRBS_DESCRICAO"] or "",
                "composes_revenue": fmt_bool(row["TRBS_IN_COMPOE_RECEITA"]),
                "is_composes_revenue": fmt_bool(row["TRBS_IN_IS_COMPOE_RECEITA"]),
                "revenue_factor": num(row["TRBS_FATOR_RECEITA"]),
                "pending": fmt_bool(row["TRBS_IN_PENDENTE_SUSPENSO"]),
                "requires_rate": fmt_bool(row["TRBS_IN_EXIGE_ALIQUOTA"]),
                "forbids_not_taxable": fmt_bool(row["TRBS_IN_VEDADO_NAO_TRIBUTAVEL"]),
                "date_start": fmt_date(row["TRBS_INICIO_VIGENCIA"]),
                "date_end": fmt_date(row["TRBS_FIM_VIGENCIA"]),
            }
        )
    return out


def sync_sn_transitions(con):
    """CBS->IBS shift factor on public purchases, per period."""
    out = []
    for row in rows(
        con,
        "SELECT * FROM TRANSICAO_ALIQUOTA_COMPRA_GOV_SIMPLES_NACIONAL"
        " ORDER BY TACG_INICIO_VIGENCIA",
    ):
        start = fmt_date(row["TACG_INICIO_VIGENCIA"])
        out.append(
            {
                "id": f"rtc_sn_transition_{start.replace('-', '')}",
                "factor": num(row["TACG_FATOR"]),
                "date_start": start,
                "date_end": fmt_date(row["TACG_FIM_VIGENCIA"]),
            }
        )
    return out


def read_fiscal_ids(path):
    """cClassTrib codes already shipped by l10n_br_fiscal."""
    if not os.path.exists(path):
        raise SystemExit(f"cannot find {path}: pass --fiscal-csv")
    with open(path, encoding="utf-8") as handle:
        return {row["code"] for row in csv.DictReader(handle) if row.get("code")}


# pylint: disable=print-used  # command line tool, stdout is the report
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--src", required=True, help="calculadora-rtc-regime-regular clone"
    )
    module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser.add_argument(
        "--out",
        default=os.path.join(module_dir, "data"),
        help="module data directory (default: data/ of this module)",
    )
    parser.add_argument(
        "--fiscal-csv",
        default=os.path.join(
            os.path.dirname(module_dir),
            "l10n_br_fiscal",
            "data",
            "l10n_br_fiscal.tax.classification.csv",
        ),
        help="cClassTrib CSV of l10n_br_fiscal (default: sibling module)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write: exit 1 when the committed files are stale",
    )
    args = parser.parse_args()

    src = os.path.abspath(os.path.expanduser(args.src))
    out = os.path.abspath(os.path.expanduser(args.out))
    fiscal_ids = read_fiscal_ids(args.fiscal_csv)

    tmpdir = tempfile.mkdtemp(prefix="rtc-sync-")
    try:
        db_path = os.path.join(tmpdir, "calc.db")
        con, sql_files = build_database(src, db_path)

        version = q1(
            con,
            "SELECT VRBD_VERSAO_BASE_DADO, VRBD_DATA FROM VERSAO_BASE_DADO"
            " ORDER BY VRBD_ID DESC LIMIT 1",
        )
        treatments = sync_treatments(con)
        legal = sync_legal_basis(con)
        rates = sync_rates(con)
        reference_date = fmt_date(version[1])
        if not reference_date:
            raise SystemExit("VERSAO_BASE_DADO has no date: cannot pin the reference")
        classifications, new_classifications, official_codes = sync_classifications(
            con, fiscal_ids, reference_date
        )
        ncm = sync_nomenclature(con, "ncm")
        nbs = sync_nomenclature(con, "nbs")
        sn_activities = sync_sn_activities(con)
        sn_regimes = sync_sn_regimes(con)
        sn_revenue_types = sync_sn_revenue_types(con)
        sn_transitions = sync_sn_transitions(con)

        files = {
            "l10n_br_fiscal.rtc.treatment.csv": (
                [
                    "id",
                    "code",
                    "name",
                    "expr_rate",
                    "expr_effective_rate",
                    "expr_base",
                    "expr_tax_computed",
                    "expr_tax_due",
                    "expr_deferral_percent",
                    "expr_deferral_value",
                    "has_rate_reduction",
                    "has_reducer",
                    "has_monophase",
                    "has_adjustment",
                    "incompatible_with_suspension",
                    "requires_desoneration_group",
                    "date_start",
                    "date_end",
                ],
                treatments,
            ),
            "l10n_br_fiscal.rtc.legal.basis.csv": (
                [
                    "id",
                    "name",
                    "text",
                    "normative_reference",
                    "date_start",
                    "date_end",
                ],
                legal,
            ),
            "l10n_br_fiscal.rtc.rate.csv": (
                ["id", "tax", "rate", "date_start", "date_end"],
                rates,
            ),
            "l10n_br_fiscal.tax.classification.csv": (
                CLASSIFICATION_UPDATE_FIELDS,
                classifications,
            ),
            "l10n_br_fiscal.rtc.sn.activity.csv": (
                [
                    "id",
                    "code",
                    "name",
                    "annex",
                    "annex_with_factor_r",
                    "label",
                    "short_label",
                    "not_taxable",
                    "date_start",
                    "date_end",
                ],
                sn_activities,
            ),
            "l10n_br_fiscal.rtc.sn.regime.csv": (
                [
                    "id",
                    "crt",
                    "name",
                    "generates_ibs",
                    "destination_due",
                    "destination_pending",
                    "date_start",
                    "date_end",
                ],
                sn_regimes,
            ),
            "l10n_br_fiscal.rtc.sn.revenue.type.csv": (
                [
                    "id",
                    "code",
                    "name",
                    "composes_revenue",
                    "is_composes_revenue",
                    "revenue_factor",
                    "pending",
                    "requires_rate",
                    "forbids_not_taxable",
                    "date_start",
                    "date_end",
                ],
                sn_revenue_types,
            ),
            "l10n_br_fiscal.rtc.sn.transition.csv": (
                ["id", "factor", "date_start", "date_end"],
                sn_transitions,
            ),
            "l10n_br_fiscal.rtc.nomenclature.csv": (
                [
                    "id",
                    "classification_code",
                    "nomenclature_type",
                    "code",
                    "annex",
                    "date_start",
                    "date_end",
                ],
                ncm + nbs,
            ),
        }

        os.makedirs(tmpdir, exist_ok=True)
        staged = os.path.join(tmpdir, "out")
        os.makedirs(staged, exist_ok=True)
        for name, (fields, records) in files.items():
            write_csv(os.path.join(staged, name), fields, records)
        write_xml_records(
            os.path.join(staged, "l10n_br_fiscal.tax.classification.rtc.xml"),
            "l10n_br_fiscal.tax.classification",
            new_classifications,
            CLASSIFICATION_NEW_FIELDS[1:],
            ref_fields=("rtc_treatment_id", "rtc_legal_basis_id"),
        )
        files["l10n_br_fiscal.tax.classification.rtc.xml"] = (None, None)

        missing = sorted(fiscal_ids - official_codes)
        extra = sorted(official_codes - fiscal_ids)

        report = [
            "# RTC tables sync report",
            "",
            f"- source: `{os.path.basename(src)}`",
            f"- database version: `{version[0]}` ({fmt_date(version[1])})",
            f"- flyway scripts applied: {len(sql_files)}",
            f"- treatments: {len(treatments)}",
            f"- legal basis: {len(legal)}",
            f"- rates: {len(rates)}",
            "- classifications (current): "
            f"{len(classifications) + len(new_classifications)}"
            f" ({len(classifications)} enrich, {len(new_classifications)} create)",
            f"- nomenclature rows: ncm={len(ncm)}, nbs={len(nbs)}",
            f"- Simples Nacional: activities={len(sn_activities)},"
            f" regimes={len(sn_regimes)}, revenue types={len(sn_revenue_types)},"
            f" transition factors={len(sn_transitions)}",
            "",
            "## cClassTrib already in l10n_br_fiscal",
            "",
            "- in l10n_br_fiscal and still official: "
            f"{len(fiscal_ids & official_codes)}",
            f"- in l10n_br_fiscal, absent from the official base ({len(missing)}): "
            + (", ".join(f"`{c}`" for c in missing) or "none"),
            f"- official, not in l10n_br_fiscal yet ({len(extra)}): "
            + (", ".join(f"`{c}`" for c in extra) or "none"),
            "",
        ]
        report_text = "\n".join(report)
        with open(os.path.join(staged, "SYNC_REPORT.md"), "w", encoding="utf-8") as gh:
            gh.write(report_text)

        digest = hashlib.sha256(
            "".join(
                open(os.path.join(staged, name), "rb").read().decode("utf-8", "replace")
                for name in sorted(files)
            ).encode()
        ).hexdigest()

        if args.check:
            stale = []
            for name in list(files) + ["SYNC_REPORT.md"]:
                target = os.path.join(out, name)
                new = os.path.join(staged, name)
                if (
                    not os.path.exists(target)
                    or open(target, "rb").read() != open(new, "rb").read()
                ):
                    stale.append(name)
            if stale:
                print("stale data files: " + ", ".join(stale), file=sys.stderr)
                return 1
            print(f"data files up to date (digest {digest[:12]})")
            return 0

        os.makedirs(out, exist_ok=True)
        for name in list(files) + ["SYNC_REPORT.md"]:
            shutil.copyfile(os.path.join(staged, name), os.path.join(out, name))
        print(report_text)
        print(f"written to {out} (digest {digest[:12]})")
        return 0
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
