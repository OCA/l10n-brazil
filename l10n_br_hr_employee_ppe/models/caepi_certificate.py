# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models

from ..lib.client import CAEPIError, download_and_parse, normalize_ca

_logger = logging.getLogger(__name__)

SITUACAO_SELECTION = [
    ("valid", "Valid"),
    ("expired", "Expired"),
    ("suspended", "Suspended"),
    ("cancelled", "Cancelled"),
]

PARAM_FTP_URL = "l10n_br_hr_employee_ppe.caepi_ftp_url"


class CAEPICertificate(models.Model):
    _name = "caepi.certificate"
    _description = "Certificate of Approval (MTE/CAEPI)"
    _order = "numero_ca"
    _rec_name = "numero_ca"

    numero_ca = fields.Char(required=True, index=True, string="CA Number")
    situacao = fields.Selection(SITUACAO_SELECTION, string="Status")
    data_validade = fields.Date(string="CA Expiry Date")
    equipamento = fields.Char(string="Equipment")
    fabricante = fields.Char(string="Manufacturer")
    cnpj_fabricante = fields.Char(string="Manufacturer CNPJ", size=20)
    natureza = fields.Char(string="Origin", size=64)
    norma = fields.Char(string="Technical Standard")
    aprovado_para = fields.Char(string="Approved For")
    last_sync = fields.Datetime(readonly=True)

    _sql_constraints = [
        ("numero_ca_uniq", "UNIQUE(numero_ca)", "CA already registered."),
    ]

    @api.model
    def lookup(self, ca_number):
        """Return the certificate record for a CA number, or empty recordset."""
        normalized = normalize_ca(ca_number)
        if not normalized or normalized == "0":
            return self.browse()
        return self.search([("numero_ca", "=", normalized)], limit=1)

    def _get_ftp_url(self):
        return self.env["ir.config_parameter"].sudo().get_param(PARAM_FTP_URL)

    @api.model
    def _cron_refresh(self):
        """Download the MTE export and upsert local certificates.

        Uses raw SQL for the staging upsert (~42 k rows via ORM would exceed
        ``limit_time_real_cron``).  Product updates go through the ORM because
        only a handful of products carry a CA.
        """
        url = self._get_ftp_url()
        kwargs = {"url": url} if url else {}
        try:
            rows = download_and_parse(**kwargs)
        except CAEPIError:
            _logger.exception("CAEPI: download failed, cron aborted")
            return

        if not rows:
            _logger.warning("CAEPI: no records in MTE file")
            return

        self.env.flush_all()
        cr = self.env.cr
        now = fields.Datetime.now()
        uid = self.env.uid

        cr.execute("DROP TABLE IF EXISTS _caepi_stage")
        cr.execute(
            """
            CREATE TEMP TABLE _caepi_stage (
                numero_ca VARCHAR NOT NULL,
                situacao VARCHAR,
                data_validade DATE,
                equipamento VARCHAR,
                fabricante VARCHAR,
                cnpj_fabricante VARCHAR(20),
                natureza VARCHAR(64),
                norma VARCHAR,
                aprovado_para VARCHAR
            ) ON COMMIT DROP
            """
        )

        from psycopg2.extras import execute_values

        batch = [
            (
                row["numero_ca"],
                row["situacao"] or None,
                row["data_validade"],
                row["equipamento"] or None,
                row["fabricante"] or None,
                row["cnpj_fabricante"] or None,
                row["natureza"] or None,
                row["norma"] or None,
                row["aprovado_para"] or None,
            )
            for row in rows
        ]

        execute_values(
            cr._obj,
            """INSERT INTO _caepi_stage
               (numero_ca, situacao, data_validade, equipamento,
                fabricante, cnpj_fabricante, natureza, norma, aprovado_para)
               VALUES %s""",
            batch,
            page_size=5000,
        )

        cr.execute(
            """
            INSERT INTO caepi_certificate
                   (numero_ca, situacao, data_validade, equipamento,
                    fabricante, cnpj_fabricante, natureza, norma,
                    aprovado_para, last_sync,
                    create_uid, write_uid, create_date, write_date)
            SELECT s.numero_ca, s.situacao, s.data_validade, s.equipamento,
                   s.fabricante, s.cnpj_fabricante, s.natureza, s.norma,
                   s.aprovado_para, %(now)s,
                   %(uid)s, %(uid)s, %(now)s, %(now)s
            FROM   _caepi_stage s
            ON CONFLICT (numero_ca)
            DO UPDATE SET
                   situacao     = EXCLUDED.situacao,
                   data_validade = EXCLUDED.data_validade,
                   equipamento  = EXCLUDED.equipamento,
                   fabricante   = EXCLUDED.fabricante,
                   cnpj_fabricante = EXCLUDED.cnpj_fabricante,
                   natureza     = EXCLUDED.natureza,
                   norma        = EXCLUDED.norma,
                   aprovado_para = EXCLUDED.aprovado_para,
                   last_sync    = EXCLUDED.last_sync,
                   write_uid    = %(uid)s,
                   write_date   = %(now)s
            WHERE  caepi_certificate.situacao IS DISTINCT FROM EXCLUDED.situacao
               OR  caepi_certificate.data_validade
                   IS DISTINCT FROM EXCLUDED.data_validade
               OR  caepi_certificate.equipamento IS DISTINCT FROM EXCLUDED.equipamento
               OR  caepi_certificate.fabricante IS DISTINCT FROM EXCLUDED.fabricante
            """,
            {"now": now, "uid": uid},
        )
        upserted = cr.rowcount
        self.invalidate_model()

        self._update_product_dates()

        _logger.info(
            "CAEPI: sync done — %d CAs loaded, %d updated",
            len(rows),
            upserted,
        )

    @api.model
    def _update_product_dates(self):
        """Update products whose CA expiry date changed.

        Only a few hundred products carry a CA, so ORM writes are fine here
        and keep other modules' ``write()`` and tracking working.
        """
        Product = self.env["product.template"]
        products = Product.search(
            [("ppe_certification", "!=", False), ("ppe_certification", "!=", "")]
        )
        for product in products:
            cert = self.lookup(product.ppe_certification)
            if cert and product.ppe_certification_expiry_date != cert.data_validade:
                product.ppe_certification_expiry_date = cert.data_validade

    def action_manual_refresh(self):
        """Button action: force a refresh from the MTE FTP."""
        self._cron_refresh()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("CAEPI"),
                "message": _("CA database updated successfully."),
                "sticky": False,
                "type": "success",
            },
        }
