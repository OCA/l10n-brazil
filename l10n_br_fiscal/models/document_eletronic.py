# Copyright (C) 2019  Renato Lima - Akretion
# Copyright (C) 2019  KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.exceptions import Warning as UserError

from ..constants.edoc import (
    SITUACAO_EDOC, SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_AUTORIZADA, SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA, SITUACAO_EDOC_EM_DIGITACAO,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_FISCAL_SPED_CONSIDERA_CANCELADO,
    SITUACAO_FISCAL, WORKFLOW_EDOC, PROCESSADOR, PROCESSADOR_NENHUM
)

import logging

_logger = logging.getLogger(__name__)


def fiter_processador_edoc_base(record):
    if record.processador_edoc == PROCESSADOR_NENHUM:
        return True
    return False


class EletronicDocument(models.AbstractModel):
    _name = "l10n_br_fiscal.document.eletronic"
    _description = "Fiscal Document"

    """ Implementação base dos documentos fiscais, acoplado ao account.invoice

    Devemos sempre ter em mente que o account.invoice tem diversos metodos
    importantes e que a intenção que os módulos da OCA que extendem este
    modelo, funcionem se possível sem a necessidade de codificação extra.

    Para tanto devemos evitar alterar a sequência / cadeia de chamadas de
    métodos e o próprio wokflow do account.invoice.

    É preciso também estar atento que o documento fiscal tem dois estados:

    - Estado do documento eletrônico / não eletônico: state_edoc
    - Estado FISCAL: state_fiscal

    O estado fiscal é um campo que é alterado apenas algumas vezes pelo código
    e é de responsabilidade do responsável fiscal pela empresa de manter a
    integridade do mesmo, pois ele não tem um fluxo realmente definido e
    interfere no lançamento do registro no arquivo do SPED FISCAL.

    """
    @api.model
    def _avaliable_transition(self, old_state, new_state):
        """ Verifica as transições disponiveis, para não permitir alterações
         de estado desconhecidas. Para mais detalhes verificar a variável
          WORKFLOW_EDOC

           (old_state, new_state) in (SITUACAO_EDOC_EM_DIGITACAO,
                                      SITUACAO_EDOC_A_ENVIAR)

        :param old_state: estado antigo
        :param new_state: novo estado
        :return:
        """
        return (old_state, new_state) in WORKFLOW_EDOC

    def _before_change_state(self, old_state, new_state):
        """ Hook para realizar alterações antes da alteração do estado do edoc.

        A variável self.state_edoc já estará com o estado antigo neste momento.

        :param old_state:
        :param new_state:
        :return:
        """
        self.ensure_one()

    def _after_change_state(self, old_state, new_state):
        """ Hook para realizar alterações depois da alteração do estado do edoc.

        A variável self.state_edoc já estará com o novo estado neste momento.

        :param old_state:
        :param new_state:
        :return:
        """
        self.ensure_one()
        if new_state == SITUACAO_EDOC_AUTORIZADA:
            #
            # O lançamento contábil só deve ser gerado depois da fatura ser
            # autorizada no sefaz
            self.action_move_create()
            #
            # Método do core para validar a fatura
            #
            self.invoice_validate()

        elif new_state == SITUACAO_EDOC_CANCELADA:
            self.action_cancel()
        elif new_state == SITUACAO_EDOC_DENEGADA:
            self.action_cancel()
        elif new_state == SITUACAO_EDOC_EM_DIGITACAO:
            if self.state_fiscal in SITUACAO_FISCAL_SPED_CONSIDERA_CANCELADO:
                raise (_(
                    "Não é possível retornar o documento para em \n"
                    "digitação, quando o mesmo esta na situação: \n"
                    "{0}, {1]".format(
                        old_state, self.state_fiscal,
                    ))
                )

    @api.multi
    def _change_state(self, new_state):
        """ Método para alterar o estado do documento fiscal, mantendo a
        integridade do workflow da invoice.

        Tenha muito cuidado ao alterar o workflow da invoice manualmente,
        prefira alterar o estado do documento fiscal e ele se encarregar de
        alterar o estado da invoice.

        :param new_state: Novo estado
        :return:
        """

        for record in self:
            old_state = record.state_edoc

            if not record._avaliable_transition(old_state, new_state):
                raise UserError(_(
                    "Não é possível realizar esta operação,\n"
                    "esta transição não é permitida:\n\n"
                    "De: {old_state}\n\n Para: {new_state}".format(
                        old_state=old_state, new_state=new_state
                    )
                ))

            record._before_change_state(old_state, new_state)
            record.state_edoc = new_state
            record._after_change_state(old_state, new_state)

    state_edoc = fields.Selection(
        selection=SITUACAO_EDOC,
        string="Situação e-doc",
        default=SITUACAO_EDOC_EM_DIGITACAO,
        copy=False,
        required=True,
        index=True,
    )
    state_fiscal = fields.Selection(
        selection=SITUACAO_FISCAL, string="Situação Fiscal")

    # Eventos de envio
    autorizacao_event_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document_event",
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

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
    )

    processador_edoc = fields.Selection(
        string="Processador",
        selection=PROCESSADOR,
    )

    # file_autorizacao_ids = fields.Many2many(
    #     comodel_name='ir.attachment',
    #     compute='_compute_files',
    # )
    #
    # file_ids = fields.Many2many(
    #     comodel_name='ir.attachment',
    #     compute='_compute_files',
    # )

    def action_invoice_open(self):
        """ Estamos quebrando a cadei de chamadas pois este método não deve
         ser chamado manualmente no Brasil. Caso você instale algum módulo
         que esteja chamando ele fique atento.
        :return:
        """
        _logger.warning('ALGUM MODULO ESTA CHAMANDO O action_invoice_open')
        return self.action_edoc_confirm()

    def action_invoice_cancel(self):
        """ Estamos quebrando a cadei de chamadas pois este método não deve
         ser chamado manualmente no Brasil. Caso você instale algum módulo
         que esteja chamando ele fique atento.
        :return:
        """
        _logger.warning('ALGUM MODULO ESTA CHAMANDO O action_invoice_cancel')
        return self.action_edoc_cancel()

    def _gerar_evento(self, arquivo_xml, type):
        event_obj = self.env["l10n_br_fiscal.document_event"]

        vals = {
            "type": type,
            "company_id": self.company_id.id,
            "origin": self.document_type_id.code + "/" + self.number,
            "create_date": fields.Datetime.now(),
            "fiscal_document_event_id": self.id,
        }
        event_id = event_obj.create(vals)
        event_id._grava_anexo(arquivo_xml, "xml")
        return event_id

    def _edoc_export(self):
        for record in self.filtered(fiter_processador_edoc_base):
            record._change_state(SITUACAO_EDOC_A_ENVIAR)

    def _edoc_send(self):
        for record in self.filtered(fiter_processador_edoc_base):
            record._change_state(SITUACAO_EDOC_AUTORIZADA)

    def _edoc_cancel(self):
        for record in self.filtered(fiter_processador_edoc_base):
            record._change_state(SITUACAO_EDOC_AUTORIZADA)

    def edoc_export(self):
        self._edoc_export()

    @api.multi
    def edoc_check(self):
        return True

    def action_number(self):
        for record in self:
            if not record.number:
                record.number = record._create_serie_number(
                    record.document_serie_id.id, record.date
                )
            if not record.key:
                record.gera_nova_chave()

    def action_edoc_confirm(self):
        to_confirm = self.filtered(
            lambda inv: inv.state_edoc != SITUACAO_EDOC_A_ENVIAR
        )
        # Este lambda acima evita erros quando o usuário clica várias vezes
        # to_confirm.action_date_assign()
        to_confirm.action_number()
        to_confirm.edoc_check()
        return to_confirm.edoc_export()

    def action_edoc_send(self):
        to_confirm = self.filtered(
            lambda inv: inv.state_edoc in (SITUACAO_EDOC_EM_DIGITACAO,
                                           SITUACAO_EDOC_REJEITADA))
        to_confirm.action_edoc_confirm()
        to_send = self.filtered(
            lambda inv: inv.state_edoc == SITUACAO_EDOC_A_ENVIAR
        )
        return to_send._edoc_send()

    @api.multi
    def action_invoice_draft(self):
        for record in self.filtered(fiter_processador_edoc_base):
            record._change_state(SITUACAO_EDOC_EM_DIGITACAO)
        return super(EletronicDocument, self).action_invoice_draft()

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
    def cancel_invoice_online(self, justificative):
        pass

    @api.multi
    def cce_invoice_online(self, justificative):
        pass

    def serialize(self):
        edocs = []
        self._serialize(edocs)
        return edocs

    def _serialize(self, edocs):
        return edocs

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            self.processador_edoc = self.company_id.processador_edoc
