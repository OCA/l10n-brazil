# Copyright (C) 2019  KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from erpbrasil.base.fiscal.edoc import ChaveEdoc

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    MODELO_FISCAL_CTE,
    MODELO_FISCAL_MDFE,
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_NFSE,
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_EM_DIGITACAO,
    SITUACAO_EDOC_ENVIADA,
    SITUACAO_EDOC_INUTILIZADA,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_FISCAL_SPED_CONSIDERA_CANCELADO,
    WORKFLOW_DOCUMENTO_NAO_ELETRONICO,
    WORKFLOW_EDOC,
)


class DocumentWorkflow(models.AbstractModel):
    """
    This mixin encapsulates the fiscal_state and state_edoc transitions logic.
    This is legacy code that was made by the KMEE company in version 10
    and included in the l10n_br_fiscal in version 12. The strange method names
    with _exec_after_*/_exec_before_* reflect the old Odoo "low-code"
    "state machine" for invoices that was customized in version 8 by Akretion.
    So this legacy code can probably be improved a lot...
    """

    _name = "l10n_br_fiscal.document.workflow"
    _description = "Fiscal Document Workflow"

    cancel_reason = fields.Char()

    correction_reason = fields.Char()

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
        self._document_date()
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
                    "%(old_state)s, %(fiscal_state)s",
                    old_state=old_state,
                    fiscal_state=self.state_fiscal,
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

    def _change_state(self, new_state, force_change=False):
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

            if force_change or record._avaliable_transition(old_state, new_state):
                pass
            else:
                raise UserError(
                    _(
                        "Não é possível realizar esta operação,\n"
                        "esta transição não é permitida:\n\n"
                        "De: {old_state}\n\n Para: {new_state}"
                    ).format(old_state=old_state, new_state=new_state)
                )

            if record._before_change_state(old_state, new_state):
                record.state_edoc = new_state
                record._after_change_state(old_state, new_state)
                status = True

        return status

    def _document_date(self):
        if not self.document_date:
            self.document_date = self._date_server_format()
        if not self.date_in_out:
            self.date_in_out = self._date_server_format()

    def _document_check(self):
        return True

    def _generate_key(self):
        for record in self:
            if record.document_type_id.code in (
                MODELO_FISCAL_NFE,
                MODELO_FISCAL_NFCE,
                MODELO_FISCAL_CTE,
                MODELO_FISCAL_MDFE,
            ):
                date = fields.Datetime.context_timestamp(record, record.document_date)
                chave_edoc = ChaveEdoc(
                    ano_mes=date.strftime("%y%m").zfill(4),
                    cnpj_cpf_emitente=record.company_id.vat,
                    codigo_uf=(
                        record.company_id.state_id
                        and record.company_id.state_id.ibge_code
                        or ""
                    ),
                    forma_emissao=1,  # TODO: Implementar campo no Odoo
                    modelo_documento=record.document_type_id.code or "",
                    numero_documento=record.document_number or "",
                    numero_serie=record.document_serie or "",
                    validar=False,
                )
                record.key_random_code = chave_edoc.codigo_aleatorio
                record.key_check_digit = chave_edoc.digito_verificador

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
        else:
            self._change_state(SITUACAO_EDOC_AUTORIZADA)

    def _document_confirm_to_send(self):
        to_confirm = self.filtered(lambda inv: inv.state_edoc != SITUACAO_EDOC_A_ENVIAR)
        if to_confirm:
            to_confirm._document_confirm()

    def _no_eletronic_document_send(self):
        self._change_state(SITUACAO_EDOC_AUTORIZADA)

    def _document_export(self):
        pass

    def _action_document_send(self):
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

    def document_back2draft(self):
        self.xml_error_message = False
        self.file_report_id = False
        if self.issuer == DOCUMENT_ISSUER_COMPANY:
            self._change_state(SITUACAO_EDOC_EM_DIGITACAO)
        else:
            self.state_edoc = SITUACAO_EDOC_EM_DIGITACAO

    def _action_document_back2draft(self):
        self.filtered(
            lambda d: d.state_edoc != SITUACAO_EDOC_EM_DIGITACAO
        ).document_back2draft()

    def _document_cancel(self, justificative):
        self.ensure_one()
        self.cancel_reason = justificative
        if self._change_state(SITUACAO_EDOC_CANCELADA):
            self.cancel_reason = justificative

    def _action_document_cancel(self):
        self.ensure_one()
        if self.issuer == DOCUMENT_ISSUER_COMPANY:
            if self.state_edoc == SITUACAO_EDOC_AUTORIZADA:
                result = self.env["ir.actions.act_window"]._for_xml_id(
                    "l10n_br_fiscal_edi.document_cancel_wizard_action"
                )
                return result
        else:
            self.state_edoc = SITUACAO_EDOC_CANCELADA

    def _action_document_invalidate(self):
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
                "l10n_br_fiscal_edi.invalidate_number_wizard_action"
            )
        else:
            raise UserError(_("You cannot invalidate this document"))

    def _document_correction(self, justificative):
        self.ensure_one()
        self.correction_reason = justificative

    def _action_document_correction(self):
        self.ensure_one()
        if (
            self.state_edoc in SITUACAO_EDOC_AUTORIZADA
            and self.issuer == DOCUMENT_ISSUER_COMPANY
        ):
            return self.env["ir.actions.act_window"]._for_xml_id(
                "l10n_br_fiscal_edi.document_correction_wizard_action"
            )
        else:
            raise UserError(
                _(
                    "You cannot create a fiscal correction document if "
                    "this fical document you are not the document issuer"
                )
            )

    def _document_qrcode(self):
        pass

    def _edoc_processor(self):
        pass

    def _validate_xml(self, xml_file):
        pass
