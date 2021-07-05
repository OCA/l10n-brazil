# Copyright 2018 KMEE INFORMATICA LTDA
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# Copyright (C) 2020 Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import base64
import calendar
import io
import logging
import os
import tempfile
import zipfile
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import RedirectWarning

from ..constants.fiscal import (
    MODELO_FISCAL_CFE,
    MODELO_FISCAL_CUPOM_FISCAL_ECF,
    MODELO_FISCAL_EMISSAO_PRODUTO,
    MODELO_FISCAL_EMISSAO_SERVICO,
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_NFSE,
    MODELO_FISCAL_RL,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_INUTILIZADA,
)

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base import misc
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")

PATH_MODELO = {
    MODELO_FISCAL_NFE: "nfe",
    MODELO_FISCAL_NFCE: "nfce",
    MODELO_FISCAL_CFE: "cfe",
    MODELO_FISCAL_CUPOM_FISCAL_ECF: "cfe_ecf",
    MODELO_FISCAL_NFSE: "nfse",
    MODELO_FISCAL_RL: "rl",
}

SITUACAO_EDOC = [
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_INUTILIZADA,
]


class FiscalClosing(models.Model):
    _name = "l10n_br_fiscal.closing"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Fiscal Closing Period"

    @api.depends("month", "year", "export_type")
    def _compute_name(self):
        for record in self:
            if record.export_type == "period":
                record.name = "{}/{}".format(record.month, record.year)
                record.file_name = "{}-{}.{}".format(record.month, record.year, "zip")
            else:
                now = fields.Datetime.now().strftime("%d/%m/%Y")
                record.name = now
                record.file_name = now + ".zip"

    state = fields.Selection(
        selection=[("draft", "Draft"), ("open", "Open"), ("closed", "Closed")],
        string="state",
        default="draft",
        readonly=True,
    )

    name = fields.Char(
        string="Name", compute="_compute_name", store=True, size=7, index=True
    )

    file_name = fields.Char(
        string="File Name", compute="_compute_name", store=True, size=11, index=True
    )

    year = fields.Char(string="Year", index=True)

    month = fields.Char(string="Month", size=2, index=True)

    zip_file = fields.Binary(string="Zip Files", readonly=True)

    export_type = fields.Selection(
        selection=[("period", "Por período"), ("all", "Tudo")],
        string="Export",
        default="period",
        required=True,
    )

    group_folder = fields.Boolean(string="Group documents")

    include_pdf_file = fields.Boolean(string="Include PDF files")

    raiz = fields.Char(string="Folder structure path", default=False)

    document_nfe_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        string=" NFe Documents",
        inverse_name="close_id",
        domain=[("document_type", "=", MODELO_FISCAL_NFE)],
    )

    document_nfce_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        string="NFCe Documents",
        inverse_name="close_id",
        domain=[("document_type", "=", MODELO_FISCAL_NFCE)],
    )

    document_cfe_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        string="CFe Documents",
        inverse_name="close_id",
        domain=[("document_type", "=", MODELO_FISCAL_CFE)],
    )

    document_cfeecf_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        string="CFe ECF Documents",
        inverse_name="close_id",
        domain=[("document_type", "=", MODELO_FISCAL_CUPOM_FISCAL_ECF)],
    )

    document_nfse_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        string="NFSe Documents",
        inverse_name="close_id",
        domain=[("document_type", "=", MODELO_FISCAL_NFSE)],
    )

    document_rl_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        string="RL Documents",
        inverse_name="close_id",
        domain=[("document_type", "=", MODELO_FISCAL_RL)],
    )

    attachment_ids = fields.Many2many(
        comodel_name="ir.attachment", string="Other accountant files"
    )

    company_id = fields.Many2one(comodel_name="res.company", string="Company")

    file_icms = fields.Binary(string="ICMS")

    file_icms_st = fields.Binary(string="ICMS ST")

    file_ipi = fields.Binary(string="IPI")

    file_iss = fields.Binary(string="ISS")

    file_pis = fields.Binary(string="PIS")

    file_cofins = fields.Binary(string="COFINS")

    file_csll = fields.Binary(string="CSLL")

    file_irpj = fields.Binary(string="IRPJ")

    file_simples = fields.Binary(string="Simples")

    file_honorarios = fields.Binary(string="Accountant Fee")

    block = fields.Boolean(string="Block period", help="Avoid new fiscal moves")

    notes = fields.Text(string="Accountant notes")

    _sql_constraints = [
        (
            "fiscal_closing_unique",
            "unique (company_id, month, year, export_type)",
            "The closing must be unique for the company in a period of time.",
        )
    ]

    def _create_tempfile_path(self, document):
        fsc_op_type = {"out": "Saída", "in": "Entrada", "all": "Todos"}
        document_path = "/".join(
            [
                misc.punctuation_rm(document.company_cnpj_cpf),
                document.document_date.strftime("%m-%Y"),
                PATH_MODELO[document.document_type_id.code],
                fsc_op_type.get(document.fiscal_operation_type),
                (document.document_serie or "").zfill(3)
                + (
                    "-" + misc.punctuation_rm(str(document.document_number)).zfill(9)
                    if self.group_folder
                    else ""
                ),
            ]
        )
        return document_path

    def _date_range(self):
        date_range = calendar.monthrange(int(self.year), int(self.month))
        date_min = "-".join((self.year, self.month, "01"))
        date_min = datetime.strptime(date_min, "%Y-%m-%d")

        date_max = "-".join((self.year, self.month, str(date_range[1])))
        date_max = datetime.strptime(date_max, "%Y-%m-%d")
        date_max = datetime.combine(date_max, date_max.time().max)
        return date_min, date_max

    def _save_tempfile(self, document_path, anexo, temp_dir):
        filename = os.path.join(temp_dir.name, document_path, anexo.name)
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        with open(filename, "wb") as file:
            file.write(base64.b64decode(anexo.datas))

    def _document_domain(self):
        domain = [
            (
                "document_type",
                "in",
                MODELO_FISCAL_EMISSAO_PRODUTO + MODELO_FISCAL_EMISSAO_SERVICO,
            ),
            ("state_edoc", "in", SITUACAO_EDOC),
        ]

        if self.export_type == "period":
            domain += [("close_id", "=", False)]

        domain += [("company_id", "in", self.company_id.ids)] if self.company_id else []

        if self.export_type == "period":
            date_min, date_max = self._date_range()

            domain += [
                ("date_in_out", ">=", date_min),
                ("date_in_out", "<=", date_max),
            ]

        return domain

    def _prepare_files(self, temp_dir):
        domain = self._document_domain()
        documents = self.env["l10n_br_fiscal.document"].search(domain)

        attachment_ids = self.env["ir.attachment"]

        attachment_ids |= documents.mapped("invalidate_event_id").mapped(
            "file_response_id"
        )

        if attachment_ids:
            try:
                path = "/".join(
                    [
                        misc.punctuation_rm(self.company_id.cnpj_cpf),
                        "invalidate_numbers",
                    ]
                )
                for attachment in attachment_ids:
                    self._save_tempfile(path, attachment, temp_dir)
            except OSError:
                raise RedirectWarning(_("Error!"), _("I/O Error"))
            except PermissionError:
                raise RedirectWarning(
                    _("Error!"), _("Check write permissions in your system temp folder")
                )

        for document in documents:
            attachment_ids = document.authorization_event_id.mapped("file_response_id")
            attachment_ids |= document.cancel_event_id.mapped("file_response_id")
            attachment_ids |= document.correction_event_ids.mapped("file_response_id")
            if self.include_pdf_file:
                attachment_ids |= document.file_report_id

            if self.export_type == "period":
                document.close_id = self.id

            try:
                document_path = self._create_tempfile_path(document)

                for attachment in attachment_ids:
                    self._save_tempfile(document_path, attachment, temp_dir)
            except OSError:
                raise RedirectWarning(_("Error!"), _("I/O Error"))
            except PermissionError:
                raise RedirectWarning(
                    _("Error!"), _("Check write permissions in your system temp folder")
                )
            except Exception:
                _logger.error(
                    _(
                        "Replication failed: document attachments "
                        "[id =% s] is not present in the database." % document.id
                    )
                )
        return temp_dir.name

    def action_export(self):
        temp_dir = tempfile.TemporaryDirectory()
        files_dir = self._prepare_files(temp_dir)
        archive = io.BytesIO()

        with zipfile.ZipFile(archive, "w") as zip_archive:
            for dirname, subdirs, _files in os.walk(files_dir):
                for subdir in subdirs:
                    path_subdir = files_dir + "/" + subdir
                    for cnpj_dirname, _cnpj_subdirs, cnpj_files in os.walk(path_subdir):
                        for filename in cnpj_files:
                            zip_archive.write(
                                os.path.join(cnpj_dirname, filename),
                                arcname=cnpj_dirname.replace(dirname, "")
                                + "/"
                                + filename,
                            )

        temp_dir.cleanup()

        self.write({"zip_file": base64.b64encode(archive.getbuffer()), "state": "open"})

    def action_close(self):
        """Sobrescrever este método para, notificar seguidores,
        processar documentos anexos, criar contas a pagar"""
        self.state = "closed"
