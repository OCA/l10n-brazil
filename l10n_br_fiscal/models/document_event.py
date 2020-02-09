# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64
import os

from erpbrasil.base.misc import punctuation_rm
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config

CODIGO_NOME = {"55": "nf-e", "SE": "nfs-e", "65": "nfc-e"}


def caminho_empresa(company_id, document):
    db_name = company_id._cr.dbname
    cnpj = punctuation_rm(company_id.cnpj_cpf)

    filestore = config.filestore(db_name)
    path = "/".join([filestore, "edoc", document, cnpj])
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError:
            raise UserError(
                _(u"Erro!"),
                _(
                    u"""Verifique as permissões de escrita
                    e o caminho da pasta"""
                ),
            )
    return path


class DocumentEvent(models.Model):
    _name = "l10n_br_fiscal.document_event"

    type = fields.Selection(
        selection=[
            ("-1", u"Exception"),
            ("0", u"Envio Lote"),
            ("1", u"Consulta Recibo"),
            ("2", u"Cancelamento"),
            ("3", u"Inutilização"),
            ("4", u"Consulta NFE"),
            ("5", u"Consulta Situação"),
            ("6", u"Consulta Cadastro"),
            ("7", u"DPEC Recepção"),
            ("8", u"DPEC Consulta"),
            ("9", u"Recepção Evento"),
            ("10", u"Download"),
            ("11", u"Consulta Destinadas"),
            ("12", u"Distribuição DFe"),
            ("13", u"Manifestação"),
        ],
        string="Serviço",
    )

    response = fields.Char(string=u"Descrição", size=64, readonly=True)

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Empresa",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    origin = fields.Char(
        string=u"Documento de Origem",
        size=64,
        readonly=True,
        states={"draft": [("readonly", False)]},
        help=u"Referência ao documento que gerou o evento.",
    )

    file_sent = fields.Char(string="Envio", readonly=True)

    file_returned = fields.Char(string="Retorno", readonly=True)

    status = fields.Char(string=u"Código", readonly=True)

    message = fields.Char(string=u"Mensagem", readonly=True)

    create_date = fields.Datetime(string=u"Data Criação", readonly=True)

    write_date = fields.Datetime(string=u"Data Alteração", readonly=True)

    end_date = fields.Datetime(string=u"Data Finalização", readonly=True)

    state = fields.Selection(
        selection=[
            ("draft", "Rascunho"),
            ("send", "Enviado"),
            ("wait", "Aguardando Retorno"),
            ("done", "Recebido Retorno"),
        ],
        string=u"Status",
        index=True,
        readonly=True,
        default="draft",
    )

    fiscal_document_event_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document", string=u"Documentos"
    )

    cancel_document_event_id = fields.Many2one(
        comodel_name="l10n_br_account.invoice.cancel", string="Cancelamento"
    )

    invalid_number_document_event_id = fields.Many2one(
        comodel_name="l10n_br_account.invoice.invalid.number", string=u"Inutilização"
    )

    display_name = fields.Char(string="Nome", compute="_compute_display_name")

    _order = "write_date desc"

    @api.multi
    @api.depends("company_id.name", "origin")
    def _compute_display_name(self):
        self.ensure_one()
        names = ["Evento", self.company_id.name, self.origin]
        self.display_name = " / ".join(filter(None, names))

    xml_sent_id = fields.Many2one(
        comodel_name="ir.attachment", string="XML", copy=False, readony=True
    )
    xml_returned_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="XML de autorização",
        copy=False,
        readony=True,
    )

    @staticmethod
    def monta_caminho(ambiente, company_id, chave):
        caminho = caminho_empresa(company_id, chave[:2])

        if ambiente == 1:
            caminho = os.path.join(caminho, "producao/")
        else:
            caminho = os.path.join(caminho, "homologacao/")

        data = "20" + chave[2:4] + "-" + chave[4:6]
        serie = chave[22:25]
        numero = chave[25:34]

        caminho = os.path.join(caminho, data + "/")
        caminho = os.path.join(caminho, serie + "-" + numero + "/")

        try:
            os.makedirs(caminho)
        except:
            pass
        return caminho

    def _grava_arquivo_disco(self, arquivo, file_name):
        save_dir = self.monta_caminho(
            ambiente=int(self.company_id.nfe_environment),
            company_id=self.company_id,
            chave=(
                self.fiscal_document_event_id.key
                or self.fiscal_document_event_id.number,
            )  # FIXME:
        )
        file_path = os.path.join(save_dir, file_name)
        try:
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            f = open(file_path, "w")
        except IOError:
            raise UserError(
                _(u"Erro!"),
                _(
                    u"""Não foi possível salvar o arquivo
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
            self.fiscal_document_event_id.key or self.fiscal_document_event_id.number
        )  # FIXME:
        file_name += "-"
        if autorizacao:
            file_name += "proc-"
        if sequencia:
            file_name += str(sequencia) + "-"
        file_name += CODIGO_NOME[self.fiscal_document_event_id.document_type_id.code]
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
