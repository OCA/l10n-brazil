# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

import os
import base64
from erpbrasil.base import misc

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config

from ..constants.fiscal import (
    EVENT_ENVIRONMENT,
    EVENT_ENVIRONMENT_PROD,
    EVENT_ENVIRONMENT_HML,
)

_logger = logging.getLogger(__name__)

CODIGO_NOME = {"55": "nf-e", "SE": "nfs-e", "65": "nfc-e"}


def caminho_empresa(company_id):
    db_name = company_id._cr.dbname
    cnpj = misc.punctuation_rm(company_id.cnpj_cpf)

    filestore = config.filestore(db_name)
    path = "/".join([filestore, "edoc", cnpj])
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError:
            raise UserError(
                _("Erro!"),
                _(
                    """Verifique as permissões de escrita
                    e o caminho da pasta"""
                ),
            )
    return path


class DocumentEvent(models.Model):
    _name = "l10n_br_fiscal.document.event"
    _description = "Fiscal Document Event"
    _order = "write_date desc"

    type = fields.Selection(
        selection=[
            ("-1", "Exception"),
            ("0", "Envio Lote"),
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
        string="Service")

    response = fields.Char(
        string="Description",
        size=64,
        readonly=True)

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        readonly=True,
        states={"draft": [("readonly", False)]})

    origin = fields.Char(
        string="Source Document",
        size=64,
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Referência ao documento que gerou o evento.")

    file_sent = fields.Char(
        string="Dispatch File",
        readonly=True)

    file_returned = fields.Char(
        string="Return file",
        readonly=True)

    status = fields.Char(
        string="Status Code",
        readonly=True)

    message = fields.Char(
        string="Mensagem",
        readonly=True)

    create_date = fields.Datetime(
        string="Create Date",
        readonly=True)

    write_date = fields.Datetime(
        string="Write Date",
        readonly=True)

    end_date = fields.Datetime(
        string="Completion Date",
        readonly=True)

    state = fields.Selection(
        selection=[
            ("draft", "Rascunho"),
            ("send", "Enviado"),
            ("wait", "Aguardando Retorno"),
            ("done", "Recebido Retorno")],
        string="Status",
        index=True,
        readonly=True,
        default="draft")

    fiscal_document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
    )

    cancel_document_event_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.cancel",
        string="Cancelamento"
    )

    correction_document_event_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.correction",
        string="Carta de correção"
    )

    invalid_number_document_event_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.invalidate.number",
        string=u"Inutilização"
    )

    document_invalidate_number_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.invalidate.number",
        string="Invalidate Document"
    )

    display_name = fields.Char(
        string="Nome",
        compute="_compute_display_name")

    xml_sent_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="XML", copy=False,
        readony=True)

    xml_returned_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="XML de autorização",
        copy=False,
        readony=True)

    environment = fields.Selection(
        selection=EVENT_ENVIRONMENT,
    )

    @api.multi
    @api.depends("company_id.name", "origin")
    def _compute_display_name(self):
        for r in self:
            names = ["Evento", r.company_id.name, r.origin]
            r.display_name = " / ".join(filter(None, names))

    @staticmethod
    def monta_caminho(
            company_id, ambiente, tipo_documento, ano, mes, serie=False, numero=False):
        caminho = caminho_empresa(company_id)

        if ambiente not in (EVENT_ENVIRONMENT_PROD, EVENT_ENVIRONMENT_HML):
            _logger.error(
                'Ambiente não informado, salvando na pasta de Homologação!')

        if ambiente == EVENT_ENVIRONMENT_PROD:
            caminho = os.path.join(caminho, "producao/")
        else:
            caminho = os.path.join(caminho, "homologacao/")

        caminho = os.path.join(caminho, tipo_documento)
        caminho = os.path.join(caminho, ano + "-" + mes + "/")
        if serie and numero:
            caminho = os.path.join(caminho, serie + "-" + numero + "/")

        try:
            os.makedirs(caminho)
        except:
            pass
        return caminho

    def _grava_arquivo_disco(self, arquivo, file_name, tipo_documento, ano, mes, serie, numero):
        save_dir = self.monta_caminho(
            ambiente=self.environment,
            company_id=self.company_id,
            tipo_documento=tipo_documento,
            ano=ano,
            mes=mes,
            serie=serie,
            numero=numero,
            # tipo_documento=(
            #     self.fiscal_document_id.document_type_id.prefix or
            #     self.fiscal_document_id.document_type_id.code
            # ),
            # ano=self.fiscal_document_id.date.strftime("%Y").zfill(4),
            # mes=self.fiscal_document_id.date.strftime("%m").zfill(2),
            # serie=self.fiscal_document_id.document_serie,
            # numero=self.fiscal_document_id.number,
        )
        file_path = os.path.join(save_dir, file_name)
        try:
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            f = open(file_path, "w")
        except IOError:
            raise UserError(
                _("Erro!"),
                _(
                    """Não foi possível salvar o arquivo
                    em disco, verifique as permissões de escrita
                    e o caminho da pasta"""
                ),
            )
        else:
            f.write(arquivo)
            f.close()
        return file_path

    def _grava_anexo(
        self, arquivo, extensao_sem_ponto, autorizacao=False, sequencia=False
    ):
        self.ensure_one()

        file_name = ""
        file_name += (
            self.fiscal_document_id.key or self.fiscal_document_id.number
        )  # FIXME:
        file_name += "-"
        if autorizacao:
            file_name += "proc-"
        if sequencia:
            file_name += str(sequencia) + "-"
        file_name += CODIGO_NOME[
            self.fiscal_document_id.document_type_id.code]
        file_name += "." + extensao_sem_ponto

        file_path = self._grava_arquivo_disco(arquivo, file_name)

        ir_attachment_id = self.env["ir.attachment"].search(
            [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
                ("name", "=", file_name),
            ]
        )
        ir_attachment_id.unlink()

        attachment_id = ir_attachment_id.create(
            {
                "name": file_name,
                "datas_fname": file_name,
                "res_model": self._name,
                "res_id": self.id,
                "datas": base64.b64encode(arquivo.encode("utf-8")),
                "mimetype": "application/" + extensao_sem_ponto,
                "type": "binary",
            }
        )

        if autorizacao:
            vals = {"file_returned": file_path, "xml_returned_id": attachment_id.id}
        else:
            vals = {"file_sent": file_path, "xml_sent_id": attachment_id.id}
        self.write(vals)
        return attachment_id

    @api.multi
    def set_done(self, arquivo_xml):
        self._grava_anexo(arquivo_xml, "xml", autorizacao=True)
        self.write({"state": "done", "end_date": fields.Datetime.now()})
