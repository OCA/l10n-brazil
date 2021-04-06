# Copyright (C) 2019  KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo.exceptions import UserError

from odoo import _, api, fields, models
from ..constants.fiscal import (
    SITUACAO_EDOC,
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_EM_DIGITACAO,
    SITUACAO_EDOC_ENVIADA,
    SITUACAO_EDOC_INUTILIZADA,
    SITUACAO_EDOC_REJEITADA, SITUACAO_FISCAL,
    SITUACAO_FISCAL_SPED_CONSIDERA_CANCELADO,
    WORKFLOW_DOCUMENTO_NAO_ELETRONICO,
    WORKFLOW_EDOC,
    PROCESSADOR_NENHUM,
    PROCESSADOR,
    DOCUMENT_ISSUER_COMPANY,
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_CTE,
)

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base.fiscal.edoc import ChaveEdoc
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")


class DocumentWorkflow(models.AbstractModel):
    _name = 'l10n_br_fiscal.document.workflow'
    _description = 'Fiscal Document Workflow'

    state_edoc = fields.Selection(
        selection=SITUACAO_EDOC,
        string='Situação e-doc',
        default=SITUACAO_EDOC_EM_DIGITACAO,
        copy=False,
        required=True,
        track_visibility='onchange',
        index=True,
    )

    state_fiscal = fields.Selection(
        selection=SITUACAO_FISCAL,
        string='Situação Fiscal',
        copy=False,
        track_visibility='onchange',
        index=True,
    )

    cancel_reason = fields.Char(
        string='Cancel Reason',
    )

    correction_reason = fields.Char(
        string='Correction Reason',
    )

    processador_edoc = fields.Selection(
        string='Processador',
        selection=PROCESSADOR,
        default=PROCESSADOR_NENHUM,
    )

    def _direct_draft_send(self):
        return False

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
        if self.document_electronic:
            return (old_state, new_state) in WORKFLOW_EDOC
        else:
            return (old_state, new_state) in WORKFLOW_DOCUMENTO_NAO_ELETRONICO

    def _exec_before_SITUACAO_EDOC_EM_DIGITACAO(self, old_state, new_state):
        return True

    def _exec_before_SITUACAO_EDOC_A_ENVIAR(self, old_state, new_state):
        self.document_date()
        self.document_number()
        self.document_check()
        return True

    def _exec_before_SITUACAO_EDOC_ENVIADA(self, old_state, new_state):
        return True

    def _exec_before_SITUACAO_EDOC_REJEITADA(self, old_state, new_state):
        return True

    def _exec_before_SITUACAO_EDOC_AUTORIZADA(self, old_state, new_state):
        return True

    def _exec_before_SITUACAO_EDOC_CANCELADA(self, old_state, new_state):
        return True

    def _exec_before_SITUACAO_EDOC_DENEGADA(self, old_state, new_state):
        return True

    def _exec_before_SITUACAO_EDOC_INUTILIZADA(self, old_state, new_state):
        return True

    def _before_change_state(self, old_state, new_state):
        """ Hook para realizar alterações depois da alteração do estado do doc.

        A variável self.state_edoc já estará com o novo estado neste momento.

        :param old_state:
        :param new_state:
        :return:
        """
        self.ensure_one()
        if new_state == SITUACAO_EDOC_EM_DIGITACAO:
            return self._exec_before_SITUACAO_EDOC_EM_DIGITACAO(
                old_state, new_state)
        elif new_state == SITUACAO_EDOC_A_ENVIAR:
            return self._exec_before_SITUACAO_EDOC_A_ENVIAR(
                old_state, new_state)
        elif new_state == SITUACAO_EDOC_ENVIADA:
            return self._exec_before_SITUACAO_EDOC_ENVIADA(
                old_state, new_state)
        elif new_state == SITUACAO_EDOC_REJEITADA:
            return self._exec_before_SITUACAO_EDOC_REJEITADA(
                old_state, new_state)
        elif new_state == SITUACAO_EDOC_AUTORIZADA:
            return self._exec_before_SITUACAO_EDOC_AUTORIZADA(
                old_state, new_state)
        elif new_state == SITUACAO_EDOC_CANCELADA:
            return self._exec_before_SITUACAO_EDOC_CANCELADA(
                old_state, new_state)
        elif new_state == SITUACAO_EDOC_DENEGADA:
            return self._exec_before_SITUACAO_EDOC_DENEGADA(
                old_state, new_state)
        elif new_state == SITUACAO_EDOC_INUTILIZADA:
            return self._exec_before_SITUACAO_EDOC_INUTILIZADA(
                old_state, new_state)

    def _exec_after_SITUACAO_EDOC_EM_DIGITACAO(self, old_state, new_state):
        if self.state_fiscal in SITUACAO_FISCAL_SPED_CONSIDERA_CANCELADO:
            raise (
                _(
                    "Não é possível retornar o documento para em \n"
                    "digitação, quando o mesmo esta na situação: \n"
                    "{0}, {1]".format(old_state, self.state_fiscal)
                )
            )

    def _exec_after_SITUACAO_EDOC_A_ENVIAR(self, old_state, new_state):
        if self._direct_draft_send():
            self.action_document_send()

    def _exec_after_SITUACAO_EDOC_ENVIADA(self, old_state, new_state):
        pass

    def _exec_after_SITUACAO_EDOC_REJEITADA(self, old_state, new_state):
        pass

    def _exec_after_SITUACAO_EDOC_AUTORIZADA(self, old_state, new_state):
        pass

    def _exec_after_SITUACAO_EDOC_CANCELADA(self, old_state, new_state):
        pass

    def _exec_after_SITUACAO_EDOC_DENEGADA(self, old_state, new_state):
        pass

    def _exec_after_SITUACAO_EDOC_INUTILIZADA(self, old_state, new_state):
        pass

    def _after_change_state(self, old_state, new_state):
        """ Hook para realizar alterações depois da alteração do estado do doc.

        A variável self.state_edoc já estará com o novo estado neste momento.

        :param old_state:
        :param new_state:
        :return:
        """
        self.ensure_one()
        if new_state == SITUACAO_EDOC_EM_DIGITACAO:
            self._exec_after_SITUACAO_EDOC_EM_DIGITACAO(old_state, new_state)
        elif new_state == SITUACAO_EDOC_A_ENVIAR:
            self._exec_after_SITUACAO_EDOC_A_ENVIAR(old_state, new_state)
        elif new_state == SITUACAO_EDOC_ENVIADA:
            self._exec_after_SITUACAO_EDOC_ENVIADA(old_state, new_state)
        elif new_state == SITUACAO_EDOC_REJEITADA:
            self._exec_after_SITUACAO_EDOC_REJEITADA(old_state, new_state)
        elif new_state == SITUACAO_EDOC_AUTORIZADA:
            self._exec_after_SITUACAO_EDOC_AUTORIZADA(old_state, new_state)
        elif new_state == SITUACAO_EDOC_CANCELADA:
            self._exec_after_SITUACAO_EDOC_CANCELADA(old_state, new_state)
        elif new_state == SITUACAO_EDOC_DENEGADA:
            self._exec_after_SITUACAO_EDOC_DENEGADA(old_state, new_state)
        elif new_state == SITUACAO_EDOC_INUTILIZADA:
            self._exec_after_SITUACAO_EDOC_INUTILIZADA(old_state, new_state)

    @api.multi
    def _change_state(self, new_state):
        """ Método para alterar o estado do documento fiscal, mantendo a
        integridade do workflow da invoice.

        Tenha muito cuidado ao alterar o workflow da invoice manualmente,
        prefira alterar o estado do documento fiscal e ele se encarregar de
        alterar o estado da invoice.

        :param new_state: Novo estado
        :return: status: Status da conclusão da mudança de estado
        """

        status = False
        for record in self:
            old_state = record.state_edoc

            if not record._avaliable_transition(old_state, new_state):
                raise UserError(
                    _(
                        "Não é possível realizar esta operação,\n"
                        "esta transição não é permitida:\n\n"
                        "De: {old_state}\n\n Para: {new_state}".format(
                            old_state=old_state, new_state=new_state
                        )
                    )
                )

            if record._before_change_state(old_state, new_state):
                record.state_edoc = new_state
                record._after_change_state(old_state, new_state)
                status = True

        return status

    def document_date(self):
        if not self.date:
            self.date = self._date_server_format()

    def document_check(self):
        return True

    def _generate_key(self):
        for record in self:
            if record.document_type_id.code in (
                    MODELO_FISCAL_NFE,
                    MODELO_FISCAL_NFCE,
                    MODELO_FISCAL_CTE):
                chave_edoc = ChaveEdoc(
                    ano_mes=record.date.strftime("%y%m").zfill(4),
                    cnpj_emitente=record.company_cnpj_cpf,
                    codigo_uf=(
                        record.company_state_id and
                        record.company_state_id.ibge_code or ""
                    ),
                    forma_emissao=1,  # TODO: Implementar campo no Odoo
                    modelo_documento=record.document_type_id.code or "",
                    numero_documento=record.number or "",
                    numero_serie=record.document_serie or "",
                    validar=True,
                )
                # TODO: Implementar campos no Odoo
                # record.key_number = chave_edoc.campos
                # record.key_formated = ' '.joint(chave_edoc.partes())
                record.key = chave_edoc.chave

    def document_number(self):
        if self.issuer == DOCUMENT_ISSUER_COMPANY:
            if not self.number and self.document_serie_id:
                self.number = self.document_serie_id.next_seq_number()
                self.document_serie = self.document_serie_id.code

            if not self.operation_name:
                self.operation_name = ', '.join(
                    [l.name for l in self.line_ids.mapped(
                        'fiscal_operation_id')])

            if self.document_electronic and not self.key:
                self._generate_key()

    def _document_confirm(self):
        self._change_state(SITUACAO_EDOC_A_ENVIAR)

    def action_document_confirm(self):
        to_confirm = self.filtered(
            lambda inv: inv.state_edoc != SITUACAO_EDOC_A_ENVIAR
        )
        if to_confirm:
            to_confirm._document_confirm()

    def _document_send(self):
        self._change_state(SITUACAO_EDOC_AUTORIZADA)

    def _document_export(self):
        pass

    def action_document_send(self):
        to_send = self.filtered(lambda d: d.state_edoc in (
            SITUACAO_EDOC_A_ENVIAR,
            SITUACAO_EDOC_ENVIADA,
            SITUACAO_EDOC_REJEITADA,
        ))
        if to_send:
            to_send._document_send()

    def action_document_back2draft(self):
        self._change_state(SITUACAO_EDOC_EM_DIGITACAO)

    def _document_cancel(self, justificative):
        self.cancel_reason = justificative
        if self._change_state(SITUACAO_EDOC_CANCELADA):
            self.cancel_reason = justificative
            msg = "Cancelamento: {}".format(justificative)
            self.message_post(body=msg)

    @api.multi
    def action_document_cancel(self):
        result = self.env["ir.actions.act_window"].for_xml_id(
            "l10n_br_fiscal", "document_cancel_wizard_action"
        )
        return result

    @api.multi
    def action_document_invalidate(self):
        result = self.env["ir.actions.act_window"].for_xml_id(
            "l10n_br_fiscal", "wizard_document_invalidate_action"
        )
        return result

    def _document_correction(self, justificative):
        self.correction_reason = justificative
        msg = "Carta de correção: {}".format(justificative)
        self.message_post(body=msg)

    @api.multi
    def action_document_correction(self):
        result = self.env["ir.actions.act_window"].for_xml_id(
            "l10n_br_fiscal", "document_correction_wizard_action"
        )
        return result
