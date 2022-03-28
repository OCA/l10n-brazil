# Copyright (C) 2019  KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    MODELO_FISCAL_CTE,
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_NFSE,
    SITUACAO_EDOC,
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_EM_DIGITACAO,
    SITUACAO_EDOC_ENVIADA,
    SITUACAO_EDOC_INUTILIZADA,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_FISCAL,
    SITUACAO_FISCAL_SPED_CONSIDERA_CANCELADO,
    WORKFLOW_DOCUMENTO_NAO_ELETRONICO,
    WORKFLOW_EDOC,
)

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base.fiscal.edoc import ChaveEdoc
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")


class DocumentWorkflow(models.AbstractModel):
    _name = "l10n_br_fiscal.document.workflow"
    _description = "Fiscal Document Workflow"

    state_edoc = fields.Selection(
        selection=SITUACAO_EDOC,
        string="Situação e-doc",
        default=SITUACAO_EDOC_EM_DIGITACAO,
        copy=False,
        required=True,
        readonly=True,
        # tracking=True,
        index=True,
    )

    state_fiscal = fields.Selection(
        selection=SITUACAO_FISCAL,
        string="Situação Fiscal",
        copy=False,
        # tracking=True,
        index=True,
    )

    cancel_reason = fields.Char(
        string="Cancel Reason",
    )

    correction_reason = fields.Char(
        string="Correction Reason",
    )

    def _direct_draft_send(self):
        return False

    @api.model
    def _avaliable_transition(self, old_state, new_state):
        """Verifica as transições disponiveis, para não permitir alterações
         de estado desconhecidas. Para mais detalhes verificar a variável
          WORKFLOW_EDOC

           (old_state, new_state) in (SITUACAO_EDOC_EM_DIGITACAO,
                                      SITUACAO_EDOC_A_ENVIAR)

        :param old_state: estado antigo
        :param new_state: novo estado
        :return:
        """
        self.ensure_one()
        if self.document_electronic:
            return (old_state, new_state) in WORKFLOW_EDOC
        else:
            return (old_state, new_state) in WORKFLOW_DOCUMENTO_NAO_ELETRONICO

    def _exec_before_SITUACAO_EDOC_EM_DIGITACAO(self, old_state, new_state):
        return True

    def _exec_before_SITUACAO_EDOC_A_ENVIAR(self, old_state, new_state):
        self._document_date()
        self._document_number()
        self._document_comment()
        self._document_check()
        self._document_export()
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
        """Hook para realizar alterações depois da alteração do estado do doc.

        A variável self.state_edoc já estará com o novo estado neste momento.

        :param old_state:
        :param new_state:
        :return:
        """
        self.ensure_one()
        if new_state == SITUACAO_EDOC_EM_DIGITACAO:
            return self._exec_before_SITUACAO_EDOC_EM_DIGITACAO(old_state, new_state)
        elif new_state == SITUACAO_EDOC_A_ENVIAR:
            return self._exec_before_SITUACAO_EDOC_A_ENVIAR(old_state, new_state)
        elif new_state == SITUACAO_EDOC_ENVIADA:
            return self._exec_before_SITUACAO_EDOC_ENVIADA(old_state, new_state)
        elif new_state == SITUACAO_EDOC_REJEITADA:
            return self._exec_before_SITUACAO_EDOC_REJEITADA(old_state, new_state)
        elif new_state == SITUACAO_EDOC_AUTORIZADA:
            return self._exec_before_SITUACAO_EDOC_AUTORIZADA(old_state, new_state)
        elif new_state == SITUACAO_EDOC_CANCELADA:
            return self._exec_before_SITUACAO_EDOC_CANCELADA(old_state, new_state)
        elif new_state == SITUACAO_EDOC_DENEGADA:
            return self._exec_before_SITUACAO_EDOC_DENEGADA(old_state, new_state)
        elif new_state == SITUACAO_EDOC_INUTILIZADA:
            return self._exec_before_SITUACAO_EDOC_INUTILIZADA(old_state, new_state)

    def _exec_after_SITUACAO_EDOC_EM_DIGITACAO(self, old_state, new_state):
        self.ensure_one()
        if self.state_fiscal in SITUACAO_FISCAL_SPED_CONSIDERA_CANCELADO:
            raise (
                _(
                    "Não é possível retornar o documento para em \n"
                    "digitação, quando o mesmo esta na situação: \n"
                    "{}, {}".format(old_state, self.state_fiscal)
                )
            )

    def _exec_after_SITUACAO_EDOC_A_ENVIAR(self, old_state, new_state):
        self.ensure_one()
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
        """Hook para realizar alterações depois da alteração do estado do doc.

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

        self._generates_subsequent_operations()

    def _change_state(self, new_state):
        """Método para alterar o estado do documento fiscal, mantendo a
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

    def _document_date(self):
        if not self.document_date:
            self.document_date = self._date_server_format()

    def _document_check(self):
        return True

    def _generate_key(self):
        for record in self:
            if record.document_type_id.code in (
                MODELO_FISCAL_NFE,
                MODELO_FISCAL_NFCE,
                MODELO_FISCAL_CTE,
            ):
                chave_edoc = ChaveEdoc(
                    ano_mes=record.document_date.strftime("%y%m").zfill(4),
                    cnpj_emitente=record.company_cnpj_cpf,
                    codigo_uf=(
                        record.company_state_id
                        and record.company_state_id.ibge_code
                        or ""
                    ),
                    forma_emissao=1,  # TODO: Implementar campo no Odoo
                    modelo_documento=record.document_type_id.code or "",
                    numero_documento=record.document_number or "",
                    numero_serie=record.document_serie or "",
                    validar=False,
                )
                # TODO: Implementar campos no Odoo
                # record.key_number = chave_edoc.campos
                # record.key_formated = ' '.joint(chave_edoc.partes())
                record.document_key = chave_edoc.chave

    def _document_number(self):
        self.ensure_one()
        if self.issuer == DOCUMENT_ISSUER_COMPANY:
            if self.document_serie_id:
                self.document_serie = self.document_serie_id.code

                if self.document_type == MODELO_FISCAL_NFSE and not self.rps_number:
                    self.rps_number = self.document_serie_id.next_seq_number()

                if (
                    self.document_type != MODELO_FISCAL_NFSE
                    and not self.document_number
                ):
                    self.document_number = self.document_serie_id.next_seq_number()

            if not self.operation_name:
                self.operation_name = ", ".join(
                    [
                        line.name
                        for line in self.fiscal_line_ids.mapped("fiscal_operation_id")
                    ]
                )

            if self.document_electronic and not self.document_key:
                self._generate_key()

    def _document_confirm(self):
        if self.issuer == DOCUMENT_ISSUER_COMPANY:
            if not self.comment_ids and self.fiscal_operation_id.comment_ids:
                self.comment_ids |= self.fiscal_operation_id.comment_ids

            for line in self.fiscal_line_ids:
                if not line.comment_ids and line.fiscal_operation_line_id.comment_ids:
                    line.comment_ids |= line.fiscal_operation_line_id.comment_ids
            self._change_state(SITUACAO_EDOC_A_ENVIAR)

    def action_document_confirm(self):
        to_confirm = self.filtered(lambda inv: inv.state_edoc != SITUACAO_EDOC_A_ENVIAR)
        if to_confirm:
            to_confirm._document_confirm()

    def _no_eletronic_document_send(self):
        self._change_state(SITUACAO_EDOC_AUTORIZADA)

    def _document_export(self):
        pass

    def action_document_send(self):
        to_send = self.filtered(
            lambda d: d.state_edoc
            in (
                SITUACAO_EDOC_A_ENVIAR,
                SITUACAO_EDOC_ENVIADA,
                SITUACAO_EDOC_REJEITADA,
            )
        )
        if to_send:
            to_send._document_send()

    def action_document_back2draft(self):
        self.xml_error_message = False
        self._change_state(SITUACAO_EDOC_EM_DIGITACAO)

    def _document_cancel(self, justificative):
        self.ensure_one()
        self.cancel_reason = justificative
        if self._change_state(SITUACAO_EDOC_CANCELADA):
            self.cancel_reason = justificative

    def action_document_cancel(self):
        self.ensure_one()
        if self.state_edoc == SITUACAO_EDOC_AUTORIZADA:
            result = self.env["ir.actions.act_window"]._for_xml_id(
                "l10n_br_fiscal.document_cancel_wizard_action"
            )
            return result

    def action_document_invalidate(self):
        self.ensure_one()
        if (
            self.document_number
            and self.document_serie
            and self.state_edoc
            in (
                SITUACAO_EDOC_EM_DIGITACAO,
                SITUACAO_EDOC_REJEITADA,
                SITUACAO_EDOC_A_ENVIAR,
            )
            and self.issuer == DOCUMENT_ISSUER_COMPANY
        ):
            return self.env["ir.actions.act_window"]._for_xml_id(
                "l10n_br_fiscal.invalidate_number_wizard_action"
            )
        else:
            raise UserError(_("You cannot invalidate this document"))

    def _document_correction(self, justificative):
        self.ensure_one()
        self.correction_reason = justificative

    def action_document_correction(self):
        self.ensure_one()
        if (
            self.state_edoc in SITUACAO_EDOC_AUTORIZADA
            and self.issuer == DOCUMENT_ISSUER_COMPANY
        ):
            return self.env["ir.actions.act_window"]._for_xml_id(
                "l10n_br_fiscal.document_correction_wizard_action"
            )
        else:
            raise UserError(
                _(
                    "You cannot create a fiscal correction document if "
                    "this fical document you are not the document issuer"
                )
            )
