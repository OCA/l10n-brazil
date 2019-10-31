# -*- coding: utf-8 -*-
# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import Warning as UserError
from odoo.osv.expression import *

from ..constantes import (SITUACAO_EDOC, SITUACAO_EDOC_A_ENVIAR,
                          SITUACAO_EDOC_AUTORIZADA, SITUACAO_EDOC_CANCELADA,
                          SITUACAO_EDOC_DENEGADA, SITUACAO_EDOC_EM_DIGITACAO,
                          SITUACAO_EDOC_ENVIADA, SITUACAO_EDOC_REJEITADA,
                          SITUACAO_FISCAL)


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
        count=False,
        access_rights_uid=None,
    ):
        result = super(IrAttachment, self)._search(
            args, offset, limit, order, count, access_rights_uid
        )
        data = {}
        for arg in args:
            if type(arg) == list:
                field, expression, values = arg
                if field in ("res_model", "res_id"):
                    data[field] = values

        if data.get("res_model") and data.get("res_model") == "account.invoice":
            res_id = data.get("res_id")
            if res_id:
                invoice_ids = self.env["account.invoice"].browse(res_id)
                result += (
                    invoice_ids.mapped("file_xml_autorizacao_id").ids
                    + invoice_ids.mapped("file_xml_autorizacao_cancelamento_id").ids
                    + invoice_ids.mapped("file_pdf_id").ids
                )
        return result


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def _avaliable_transition(self, old_state, new_state):
        allowed = [
            (SITUACAO_EDOC_EM_DIGITACAO, SITUACAO_EDOC_A_ENVIAR),
            (SITUACAO_EDOC_EM_DIGITACAO, SITUACAO_EDOC_ENVIADA),
            (SITUACAO_EDOC_EM_DIGITACAO, SITUACAO_EDOC_REJEITADA),
            (SITUACAO_EDOC_EM_DIGITACAO, SITUACAO_EDOC_AUTORIZADA),
            (SITUACAO_EDOC_EM_DIGITACAO, SITUACAO_EDOC_DENEGADA),
            (SITUACAO_EDOC_EM_DIGITACAO, SITUACAO_EDOC_CANCELADA),
            (SITUACAO_EDOC_A_ENVIAR, SITUACAO_EDOC_ENVIADA),
            (SITUACAO_EDOC_A_ENVIAR, SITUACAO_EDOC_REJEITADA),
            (SITUACAO_EDOC_A_ENVIAR, SITUACAO_EDOC_AUTORIZADA),
            (SITUACAO_EDOC_A_ENVIAR, SITUACAO_EDOC_DENEGADA),
            (SITUACAO_EDOC_A_ENVIAR, SITUACAO_EDOC_CANCELADA),
            (SITUACAO_EDOC_ENVIADA, SITUACAO_EDOC_REJEITADA),
            (SITUACAO_EDOC_ENVIADA, SITUACAO_EDOC_AUTORIZADA),
            (SITUACAO_EDOC_ENVIADA, SITUACAO_EDOC_DENEGADA),
            (SITUACAO_EDOC_AUTORIZADA, SITUACAO_EDOC_CANCELADA),
            (SITUACAO_EDOC_REJEITADA, SITUACAO_EDOC_AUTORIZADA),
            (SITUACAO_EDOC_REJEITADA, SITUACAO_EDOC_EM_DIGITACAO),
            (SITUACAO_EDOC_REJEITADA, SITUACAO_EDOC_REJEITADA),
        ]
        return (old_state, new_state) in allowed

    @api.multi
    def _change_state(self, new_state):
        for record in self:
            old_state = record.state_edoc
            if record._avaliable_transition(old_state, new_state):
                record.state_edoc = new_state
                # TODO: Create some hooks calleds after stage transition
                # TODO: Verificar a situação fiscal
                if new_state == SITUACAO_EDOC_AUTORIZADA:
                    record.invoice_validate()
                elif new_state == SITUACAO_EDOC_CANCELADA:
                    record.action_cancel()
                elif new_state == SITUACAO_EDOC_DENEGADA:
                    record.action_cancel()
            else:
                raise UserError(_("This state transition is not allowed"))

    state_edoc = fields.Selection(
        selection=SITUACAO_EDOC,
        string="Situação e-doc",
        default=SITUACAO_EDOC_EM_DIGITACAO,
        copy=False,
        required=True,
        index=True,
    )
    state_fiscal = fields.Selection(selection=SITUACAO_FISCAL, string="Situação Fiscal")
    # Sim isso esta duplicado
    # Todos os eventos
    account_document_event_ids = fields.One2many(
        comodel_name="l10n_br_account.document_event",
        inverse_name="document_event_ids",
        string=u"Eventos",
        copy=False,
    )
    # Eventos de envio
    autorizacao_event_id = fields.Many2one(
        comodel_name="l10n_br_account.document_event",
        string="Autorização",
        readonly=True,
        copy=False,
    )
    file_xml_id = fields.Many2one(
        comodel_name="ir.attachment",
        related="autorizacao_event_id.xml_sent_id",
        string="XML",
        ondelete="restrict",
        copy=False,
        readonly=True,
    )
    file_xml_autorizacao_id = fields.Many2one(
        comodel_name="ir.attachment",
        related="autorizacao_event_id.xml_returned_id",
        string="XML de autorização",
        ondelete="restrict",
        copy=False,
        readonly=True,
    )
    # Eventos de cancelamento
    cancel_document_event_id = fields.Many2one(
        comodel_name="l10n_br_account.invoice.cancel", string="Cancelamento"
    )
    # Eventos de carta de correção
    cce_document_ids = fields.One2many(
        comodel_name="l10n_br_account.invoice.cce",
        inverse_name="invoice_id",
        string=u"Carta de correção",
        copy=False,
    )

    is_edoc_printed = fields.Boolean(string="Danfe Impresso", readonly=True)

    file_xml_cancelamento_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="XML de cancelamento",
        ondelete="restrict",
        copy=False,
    )
    file_xml_autorizacao_cancelamento_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="XML de autorização de cancelamento",
        ondelete="restrict",
        copy=False,
    )
    file_pdf_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="PDF DANFE/DANFCE",
        ondelete="restrict",
        copy=False,
    )
    processador_edoc = fields.Selection(related="company_id.processador_edoc")

    # file_autorizacao_ids = fields.Many2many(
    #     comodel_name='ir.attachment',
    #     compute='_compute_files',
    # )
    #
    # file_ids = fields.Many2many(
    #     comodel_name='ir.attachment',
    #     compute='_compute_files',
    # )

    def _gerar_evento(self, arquivo_xml, type):
        event_obj = self.env["l10n_br_account.document_event"]

        vals = {
            "type": type,
            "company_id": self.company_id.id,
            "origin": self.fiscal_document_id.code + "/" + self.fiscal_number,
            "create_date": fields.Datetime.now(),
            "document_event_ids": self.id,
        }

        event_id = event_obj.create(vals)
        event_id._grava_anexo(arquivo_xml, "xml")
        return event_id

    def _edoc_export(self):
        pass

    def edoc_export(self):
        for record in self:
            my_file = record._edoc_export()
            if my_file:
                event_id = self._gerar_evento(my_file, type="0")
                record.autorizacao_event_id = event_id
            record._change_state(SITUACAO_EDOC_A_ENVIAR)

    def action_edoc_confirm(self):
        self.edoc_check()
        self.action_date_assign()
        self.action_number()
        self.action_move_create()
        self.edoc_export()
        return True

    def _edoc_send(self):
        self._change_state(SITUACAO_EDOC_AUTORIZADA)

    def action_edoc_send(self):
        for record in self:
            if not record.state_edoc in (
                SITUACAO_EDOC_A_ENVIAR,
                SITUACAO_EDOC_REJEITADA,
            ):
                record.action_edoc_confirm()
            record._edoc_send()

    def _edoc_cancel(self):
        self._change_state(SITUACAO_EDOC_CANCELADA)

    @api.multi
    def action_edoc_cancel(self):
        self.ensure_one()
        document_serie_id = self.document_serie_id
        fiscal_document_id = self.document_serie_id.fiscal_document_id
        electronic = self.document_serie_id.fiscal_document_id.electronic
        nfe_protocol = self.edoc_protocol_number
        emitente = self.issuer

        if (
            (document_serie_id and fiscal_document_id and not electronic)
            or not nfe_protocol
        ) or emitente == u"1":
            return self._edoc_cancel()
        else:
            result = self.env["ir.actions.act_window"].for_xml_id(
                "edoc_base", "edoc_cancel_wizard_act_window"
            )
            return result

    @api.multi
    def action_edoc_cce(self):
        self.ensure_one()
        document_serie_id = self.document_serie_id
        fiscal_document_id = self.document_serie_id.fiscal_document_id
        electronic = self.document_serie_id.fiscal_document_id.electronic
        nfe_protocol = self.edoc_protocol_number
        emitente = self.issuer

        if (
            (document_serie_id and fiscal_document_id and not electronic)
            or not nfe_protocol
        ) or emitente == u"1":
            raise UserError(
                _(
                    "Impossível enviar uma cartão de correção !!!\n"
                    "Para uma nota fiscal não emitida / não eletônica"
                )
            )
        else:
            result = self.env["ir.actions.act_window"].for_xml_id(
                "edoc_base", "edoc_cce_wizard_act_window"
            )
            return result

    @api.multi
    def action_invoice_draft(self):
        self._change_state(SITUACAO_EDOC_EM_DIGITACAO)
        return super(AccountInvoice, self).action_invoice_draft()
