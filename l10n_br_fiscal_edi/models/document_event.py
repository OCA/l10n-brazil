# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64
import logging
import os

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import EVENT_ENVIRONMENT
from odoo.addons.l10n_br_fiscal.tools import build_edoc_path

_logger = logging.getLogger(__name__)

FILE_SUFIX_EVENT = {
    "0": "env",
    "1": "con-rec",
    "2": "can",
    "3": "inu",
    "4": "con-edoc",
    "5": "con-status",
    "6": "con-cad",
    "7": "dpec-rec",
    "8": "dpec-con",
    "9": "rec-eve",
    "10": "dow",
    "11": "con-dest",
    "12": "dist-dfe",
    "13": "man",
    "14": "cce",
}


class Event(models.Model):
    _name = "l10n_br_fiscal.event"
    _description = "Fiscal Event"

    @api.depends("document_id.name", "invalidate_number_id.name")
    def _compute_display_name(self):
        for record in self:
            if record.document_id:
                names = [
                    _("Fiscal Document"),
                    record.document_id.name,
                ]
                record.display_name = " / ".join(filter(None, names))
            elif record.invalidate_number_id:
                names = [
                    _("Invalidate Number"),
                    record.invalidate_number_id.name,
                ]
                record.display_name = " / ".join(filter(None, names))
            else:
                record.display_name = ""

    create_date = fields.Datetime(
        readonly=True,
        index=True,
        default=fields.Datetime.now,
    )

    write_date = fields.Datetime(
        readonly=True,
        index=True,
    )

    type = fields.Selection(
        selection=[
            ("-1", "Exception"),
            ("0", "Autorização de Uso"),
            ("1", "Consulta Recibo"),
            ("2", "Cancelamento"),
            ("3", "Inutilização"),
            ("4", "Consulta NFE"),
            ("5", "Consulta Situação"),
            ("6", "Consulta Cadastro"),
            ("7", "DPEC Recepção"),
            ("8", "DPEC Consulta"),
            ("9", "Recepção Evento"),
            ("10", "Download"),
            ("11", "Consulta Destinadas"),
            ("12", "Distribuição DFe"),
            ("13", "Manifestação"),
            ("14", "Carta de Correção"),
        ],
        string="Service",
    )

    origin = fields.Char(
        string="Source Document",
        readonly=True,
        help="Document reference that generated this event.",
    )

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
        index=True,
    )

    document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
        string="Fiscal Document Type",
        index=True,
        required=True,
    )

    document_serie_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.serie",
        required=True,
    )

    document_number = fields.Char(
        required=True,
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        index=True,
    )

    invalidate_number_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.invalidate.number",
        string="Invalidate Number",
        index=True,
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        index=True,
        required=True,
    )

    sequence = fields.Char(
        help="Fiscal Document Event Sequence",
    )

    justification = fields.Char()

    display_name = fields.Char(
        string="name",
        compute="_compute_display_name",
        store=True,
    )

    file_request_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="XML",
        copy=False,
        readonly=True,
    )

    file_response_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="XML Response",
        copy=False,
        readonly=True,
    )

    file_path = fields.Char(
        readonly=True,
    )

    status_code = fields.Char(
        readonly=True,
    )

    response = fields.Char(
        string="Response Message",
        readonly=True,
    )

    message = fields.Char(
        readonly=True,
    )

    protocol_date = fields.Datetime(
        readonly=True,
        index=True,
    )

    protocol_number = fields.Char()

    lot_receipt_number = fields.Char(
        help=(
            "In asynchronous processing, a lot receipt number is generated, "
            "which is used for later consultation."
        ),
    )

    state = fields.Selection(
        selection=[
            ("draft", _("Draft")),
            ("send", _("Sending")),
            ("wait", _("Waiting Response")),
            ("done", _("Response received")),
        ],
        string="Status",
        readonly=True,
        index=True,
        default="draft",
    )

    environment = fields.Selection(
        selection=EVENT_ENVIRONMENT,
    )

    @api.constrains("justification")
    def _check_justification(self):
        if len(self.justification) < 15:
            raise UserError(_("Justification must be at least 15 characters."))
        return True

    def _save_event_2disk(self, arquivo, file_name):
        self.ensure_one()
        tipo_documento = self.document_type_id.prefix
        serie = self.document_serie_id.code
        numero = self.document_number

        if self.document_id:
            document_date = (
                self.document_id.document_date or self.document_id.create_date
            )
            ano = document_date.strftime("%Y")
            mes = document_date.strftime("%m")
        elif self.invalidate_number_id:
            ano = self.invalidate_number_id.date.strftime("%Y")
            mes = self.invalidate_number_id.date.strftime("%m")

        save_dir = build_edoc_path(
            ambiente=self.environment,
            company_id=self.company_id,
            tipo_documento=tipo_documento,
            ano=ano,
            mes=mes,
            serie=serie,
            numero=numero,
        )
        file_path = os.path.join(save_dir, file_name)
        try:
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            f = open(file_path, "w")
        except OSError as e:
            raise UserError(
                _("Erro!"),
                _(
                    """Não foi possível salvar o arquivo
                    em disco, verifique as permissões de escrita
                    e o caminho da pasta"""
                ),
            ) from e
        else:
            f.write(arquivo)
            f.close()
        return save_dir

    def _compute_file_name(self):
        self.ensure_one()
        if (
            self.document_id
            and self.document_id.document_key
            and self.document_id.document_electronic
            and self.document_id.document_type_id
            and self.document_id.document_type_id.prefix
        ):
            file_name = (
                self.document_id.document_type_id.prefix + self.document_id.document_key
            )
        else:
            file_name = self.document_number
        return file_name

    def _save_event_file(
        self, file, file_extension, authorization=False, rejected=False
    ):
        self.ensure_one()
        file_name = self._compute_file_name()

        if authorization:
            file_name += "-proc"
        if rejected:
            file_name += "-rej"

        if self.type:
            file_name += "-" + FILE_SUFIX_EVENT[self.type]

        if self.sequence:
            file_name += "-" + str(self.sequence)
        if file_extension:
            file_name += "." + file_extension

        if self.company_id.document_save_disk:
            file_path = self._save_event_2disk(file, file_name)
            self.file_path = file_path

        attachment_id = self.env["ir.attachment"].create(
            {
                "name": file_name,
                "res_model": self._name,
                "res_id": self.id,
                "datas": base64.b64encode(file.encode("utf-8")),
                "mimetype": "application/" + file_extension,
                "type": "binary",
            }
        )

        if authorization:
            # Não deletamos um aquivo de autorização já
            # Existente por segurança
            self.file_response_id = False
            self.file_response_id = attachment_id
        else:
            self.file_request_id.unlink()
            self.file_request_id = attachment_id
        return attachment_id

    def set_done(
        self, status_code, response, protocol_date, protocol_number, file_response_xml
    ):
        if file_response_xml:
            self._save_event_file(file_response_xml, "xml", authorization=True)
        self.write(
            {
                "state": "done",
                "status_code": status_code,
                "response": response,
                "protocol_date": protocol_date,
                "protocol_number": protocol_number,
            }
        )

    def create_event_save_xml(
        self,
        company_id,
        environment,
        event_type,
        xml_file,
        document_id=False,
        invalidate_number_id=False,
        sequence=False,
        justification=False,
    ):
        vals = {
            "company_id": company_id.id,
            "environment": environment,
            "type": event_type,
        }
        if sequence:
            vals["sequence"] = sequence
        if document_id:
            #
            #  Aplicado para envio, cancelamento, carta de correcao
            # e outras operações em que o documento esta presente.
            #
            vals["document_id"] = document_id.id
            vals["document_type_id"] = document_id.document_type_id.id
            vals["document_serie_id"] = document_id.document_serie_id.id

            if document_id.rps_number:
                vals["document_number"] = document_id.rps_number
                if document_id.document_number:
                    vals["document_number"] += "-" + document_id.document_number
            else:
                vals["document_number"] = document_id.document_number

        if invalidate_number_id:
            #
            #  Aplicado para inutilização
            #
            vals["invalidate_number_id"] = invalidate_number_id.id
            vals["document_type_id"] = invalidate_number_id.document_type_id.id
            vals["document_serie_id"] = invalidate_number_id.document_serie_id.id
            if invalidate_number_id.number_end != invalidate_number_id.number_start:
                vals["document_number"] = (
                    str(invalidate_number_id.number_start)
                    + "-"
                    + str(invalidate_number_id.number_end)
                )
            else:
                vals["document_number"] = invalidate_number_id.number_start
        if justification:
            vals["justification"] = justification
        event_id = self.create(vals)
        event_id._save_event_file(xml_file, "xml")
        return event_id

    def print_document_event(self):
        return self.env.ref(
            "l10n_br_fiscal_edi.action_report_document_event"
        ).report_action(self)
