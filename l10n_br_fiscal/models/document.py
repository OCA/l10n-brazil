# Copyright (C) 2013  Renato Lima - Akretion
# Copyright (C) 2019  KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from ast import literal_eval

from erpbrasil.base.fiscal.edoc import ChaveEdoc

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..constants.fiscal import (
    DOCUMENT_ISSUER,
    DOCUMENT_ISSUER_COMPANY,
    DOCUMENT_ISSUER_DICT,
    DOCUMENT_ISSUER_PARTNER,
    EDOC_PURPOSE,
    EDOC_PURPOSE_NORMAL,
    FISCAL_IN_OUT_DICT,
    MODELO_FISCAL_CTE,
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_NFSE,
    PROCESSADOR_NENHUM,
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


def filter_processador(record):
    if record.document_electronic and record.processador_edoc == PROCESSADOR_NENHUM:
        return True
    return False


class Document(models.Model):
    """Implementação base dos documentos fiscais

    Devemos sempre ter em mente que o modelo que vai usar este módulo abstrato
     tem diversos metodos importantes e a intenção que os módulos da OCA que
     extendem este modelo, funcionem se possível sem a necessidade de
     codificação extra.

    É preciso também estar atento que o documento fiscal tem dois estados:

    - Estado do documento eletrônico / não eletônico: state_edoc
    - Estado FISCAL: state_fiscal

    O estado fiscal é um campo que é alterado apenas algumas vezes pelo código
    e é de responsabilidade do responsável fiscal pela empresa de manter a
    integridade do mesmo, pois ele não tem um fluxo realmente definido e
    interfere no lançamento do registro no arquivo do SPED FISCAL.
    """

    _name = "l10n_br_fiscal.document"
    _inherit = [
        "l10n_br_fiscal.document.mixin.fields",
        "l10n_br_fiscal.document.move.mixin",
        "mail.thread",
    ]
    _description = "Fiscal Document"
    _check_company_auto = True

    name = fields.Char(
        compute="_compute_name",
        store=True,
        index=True,
    )

    fiscal_operation_id = fields.Many2one(
        domain="[('state', '=', 'approved'), "
        "'|', ('fiscal_operation_type', '=', fiscal_operation_type),"
        " ('fiscal_operation_type', '=', 'all')]",
    )

    fiscal_operation_type = fields.Selection(
        store=True,
    )

    rps_number = fields.Char(
        string="RPS Number",
        copy=False,
        index=True,
    )

    document_date = fields.Datetime(
        copy=False,
    )

    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        index=True,
        default=lambda self: self.env.user,
    )

    operation_name = fields.Char(
        copy=False,
    )

    document_electronic = fields.Boolean(
        related="document_type_id.electronic",
        string="Electronic?",
        store=True,
    )

    date_in_out = fields.Datetime(
        string="Date IN/OUT",
        copy=False,
    )

    document_related_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document.related",
        inverse_name="document_id",
        string="Fiscal Document Related",
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
    )

    partner_shipping_id = fields.Many2one(
        comodel_name="res.partner",
        string="Shipping Address",
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

    fiscal_line_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document.line",
        inverse_name="document_id",
        string="Document Lines",
        copy=True,
        check_company=True,
    )

    edoc_purpose = fields.Selection(
        selection=EDOC_PURPOSE,
        string="Finalidade",
        default=EDOC_PURPOSE_NORMAL,
    )

    event_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.event",
        inverse_name="document_id",
        string="Events",
        copy=False,
        readonly=True,
    )

    correction_event_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.event",
        inverse_name="document_id",
        domain=[("type", "=", "14")],
        string="Correction Events",
        copy=False,
        readonly=True,
    )

    document_type = fields.Char(
        string="Document Type Code",
        related="document_type_id.code",
        store=True,
    )

    imported_document = fields.Boolean(string="Imported", default=False)

    xml_error_message = fields.Text(
        readonly=True,
        string="XML validation errors",
        copy=False,
    )

    # Você não vai poder fazer isso em modelos que já tem state
    # TODO Porque não usar o campo state do fiscal.document???
    state = fields.Selection(related="state_edoc", string="State")

    document_subsequent_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.subsequent.document",
        inverse_name="source_document_id",
        copy=True,
    )

    document_subsequent_generated = fields.Boolean(
        string="Subsequent documents generated?",
        compute="_compute_document_subsequent_generated",
        default=False,
    )

    issuer = fields.Selection(
        selection=DOCUMENT_ISSUER,
        default=DOCUMENT_ISSUER_COMPANY,
    )

    status_code = fields.Char(
        copy=False,
    )

    status_name = fields.Char(
        copy=False,
    )

    status_description = fields.Char(
        compute="_compute_status_description",
        copy=False,
    )

    # Authorization Event Related Fields
    authorization_event_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.event",
        string="Authorization Event",
        readonly=True,
        copy=False,
    )

    authorization_date = fields.Datetime(
        related="authorization_event_id.protocol_date",
        string="Authorization Protocol Date",
        readonly=True,
    )

    authorization_protocol = fields.Char(
        related="authorization_event_id.protocol_number",
        string="Authorization Protocol Number",
        readonly=True,
    )

    send_file_id = fields.Many2one(
        comodel_name="ir.attachment",
        related="authorization_event_id.file_request_id",
        string="Send Document File XML",
        ondelete="restrict",
        readonly=True,
    )

    authorization_file_id = fields.Many2one(
        comodel_name="ir.attachment",
        related="authorization_event_id.file_response_id",
        string="Authorization File XML",
        ondelete="restrict",
        readonly=True,
    )

    # Cancel Event Related Fields
    cancel_event_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.event",
        string="Cancel Event",
        copy=False,
    )

    cancel_date = fields.Datetime(
        related="cancel_event_id.protocol_date",
        string="Cancel Protocol Date",
        readonly=True,
    )

    cancel_protocol_number = fields.Char(
        related="cancel_event_id.protocol_number",
        string="Cancel Protocol Protocol",
        readonly=True,
    )

    cancel_file_id = fields.Many2one(
        comodel_name="ir.attachment",
        related="cancel_event_id.file_response_id",
        string="Cancel File XML",
        ondelete="restrict",
        readonly=True,
    )

    # Invalidate Event Related Fields
    invalidate_event_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.event",
        string="Invalidate Event",
        copy=False,
    )

    invalidate_date = fields.Datetime(
        related="invalidate_event_id.protocol_date",
        string="Invalidate Protocol Date",
        readonly=True,
    )

    invalidate_protocol_number = fields.Char(
        related="invalidate_event_id.protocol_number",
        string="Invalidate Protocol Number",
        readonly=True,
    )

    invalidate_file_id = fields.Many2one(
        comodel_name="ir.attachment",
        related="invalidate_event_id.file_response_id",
        string="Invalidate File XML",
        ondelete="restrict",
        readonly=True,
    )

    document_version = fields.Char(string="Version", default="4.00", readonly=True)

    is_edoc_printed = fields.Boolean(string="Is Printed?", readonly=True)

    file_report_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="Document Report",
        ondelete="restrict",
        readonly=True,
        copy=False,
    )

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

    cancel_reason = fields.Char()

    correction_reason = fields.Char()

    @api.constrains("document_key")
    def _check_key(self):
        for record in self:
            if not record.document_key:
                return

            documents = record.env["l10n_br_fiscal.document"].search_count(
                [
                    ("id", "!=", record.id),
                    ("company_id", "=", record.company_id.id),
                    ("issuer", "=", record.issuer),
                    ("document_key", "=", record.document_key),
                    (
                        "document_type",
                        "in",
                        (
                            MODELO_FISCAL_CTE,
                            MODELO_FISCAL_NFCE,
                            MODELO_FISCAL_NFE,
                            MODELO_FISCAL_NFSE,
                        ),
                    ),
                    ("state", "!=", "cancelada"),
                ]
            )

            if documents:
                raise ValidationError(
                    _(
                        "There is already a fiscal document with this " "key: {} !"
                    ).format(record.document_key)
                )
            else:
                ChaveEdoc(chave=record.document_key, validar=True)

    @api.constrains("document_number")
    def _check_number(self):
        for record in self:
            if not record.document_number:
                return
            domain = [
                ("id", "!=", record.id),
                ("company_id", "=", record.company_id.id),
                ("issuer", "=", record.issuer),
                ("document_type_id", "=", record.document_type_id.id),
                ("document_serie", "=", record.document_serie),
                ("document_number", "=", record.document_number),
            ]

            invalid_number = False

            if record.issuer == DOCUMENT_ISSUER_PARTNER:
                domain.append(("partner_id", "=", record.partner_id.id))
            else:
                if record.document_serie_id:
                    invalid_number = record.document_serie_id._is_invalid_number(
                        record.document_number
                    )

            documents = record.env["l10n_br_fiscal.document"].search_count(domain)

            if documents or invalid_number:
                raise ValidationError(
                    _(
                        "There is already a fiscal document with this "
                        "Serie: %(serie)s, Number: %(number)s!",
                        serie=record.document_serie,
                        number=record.document_number,
                    )
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
        self._generates_subsequent_operations()
        self.send_email(new_state)

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
            ):
                date = fields.Datetime.context_timestamp(record, record.document_date)
                chave_edoc = ChaveEdoc(
                    ano_mes=date.strftime("%y%m").zfill(4),
                    cnpj_cpf_emitente=record.company_cnpj_cpf,
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
        else:
            self._change_state(SITUACAO_EDOC_AUTORIZADA)

    def _document_confirm_to_send(self):
        to_confirm = self.filtered(lambda inv: inv.state_edoc != SITUACAO_EDOC_A_ENVIAR)
        if to_confirm:
            to_confirm._document_confirm()

    def action_document_confirm(self):
        self._document_confirm_to_send()

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

    def document_back2draft(self):
        self.xml_error_message = False
        self.file_report_id = False
        if self.issuer == DOCUMENT_ISSUER_COMPANY:
            self._change_state(SITUACAO_EDOC_EM_DIGITACAO)
        else:
            self.state_edoc = SITUACAO_EDOC_EM_DIGITACAO

    def action_document_back2draft(self):
        self.document_back2draft()

    def _document_cancel(self, justificative):
        self.ensure_one()
        self.cancel_reason = justificative
        if self._change_state(SITUACAO_EDOC_CANCELADA):
            self.cancel_reason = justificative

    def action_document_cancel(self):
        self.ensure_one()
        if self.issuer == DOCUMENT_ISSUER_COMPANY:
            if self.state_edoc == SITUACAO_EDOC_AUTORIZADA:
                result = self.env["ir.actions.act_window"]._for_xml_id(
                    "l10n_br_fiscal.document_cancel_wizard_action"
                )
                return result
        else:
            self.state_edoc = SITUACAO_EDOC_CANCELADA

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

    def _compute_document_name(self):
        self.ensure_one()
        name = ""
        type_serie_number = ""

        if self.document_type:
            type_serie_number += self.document_type
        if self.document_serie:
            type_serie_number += "/" + self.document_serie.zfill(3)
        if self.document_number or self.rps_number:
            type_serie_number += "/" + (self.document_number or self.rps_number)

        if self._context.get("fiscal_document_complete_name"):
            name += DOCUMENT_ISSUER_DICT.get(self.issuer, "")
            if self.issuer == DOCUMENT_ISSUER_COMPANY and self.fiscal_operation_type:
                name += "/" + FISCAL_IN_OUT_DICT.get(self.fiscal_operation_type, "")
            name += "/" + type_serie_number
            if self.document_date:
                name += " - " + self.document_date.strftime("%d/%m/%Y")
            if not self.partner_cnpj_cpf:
                name += " - " + _("Unidentified Consumer")
            elif self.partner_legal_name:
                name += " - " + self.partner_legal_name
                name += " - " + self.partner_cnpj_cpf
            else:
                name += " - " + self.partner_name
                name += " - " + self.partner_cnpj_cpf
        elif self._context.get("fiscal_document_no_company"):
            name += type_serie_number
        else:
            name += "{name}/{type_serie_number}".format(
                name=self.company_name or "",
                type_serie_number=type_serie_number,
            )
        return name

    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, record._compute_document_name()))
        return res

    @api.depends(
        "issuer",
        "fiscal_operation_type",
        "document_type",
        "document_serie",
        "document_number",
        "document_date",
        "partner_id",
    )
    def _compute_name(self):
        for r in self:
            r.name = r._compute_document_name()

    @api.depends(
        "fiscal_line_ids.estimate_tax",
        "fiscal_line_ids.price_gross",
        "fiscal_line_ids.amount_untaxed",
        "fiscal_line_ids.amount_tax",
        "fiscal_line_ids.amount_taxed",
        "fiscal_line_ids.amount_total",
        "fiscal_line_ids.financial_total",
        "fiscal_line_ids.financial_total_gross",
        "fiscal_line_ids.financial_discount_value",
        "fiscal_line_ids.amount_tax_included",
        "fiscal_line_ids.amount_tax_not_included",
        "fiscal_line_ids.amount_tax_withholding",
    )
    def _compute_amount(self):
        return super()._compute_amount()

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if not values.get("document_date"):
                values["document_date"] = self._date_server_format()
        return super().create(vals_list)

    def unlink(self):
        forbidden_states_unlink = [
            SITUACAO_EDOC_AUTORIZADA,
            SITUACAO_EDOC_CANCELADA,
            SITUACAO_EDOC_DENEGADA,
            SITUACAO_EDOC_INUTILIZADA,
        ]

        for record in self.filtered(lambda d: d.state_edoc in forbidden_states_unlink):
            raise ValidationError(
                _(
                    "You cannot delete fiscal document number %(number)s with "
                    "the status: %(state)s!",
                    number=record.document_number,
                    state=record.state_edoc,
                )
            )

        return super().unlink()

    @api.onchange("company_id")
    def _onchange_company_id(self):
        if self.company_id:
            self.currency_id = self.company_id.currency_id

    def _create_return(self):
        return_docs = self.env[self._name]
        for record in self:
            fsc_op = record.fiscal_operation_id.return_fiscal_operation_id
            if not fsc_op:
                raise ValidationError(
                    _(
                        "The fiscal operation {} has no return Fiscal "
                        "Operation defined"
                    ).format(record.fiscal_operation_id)
                )

            new_doc = record.copy()
            new_doc.fiscal_operation_id = fsc_op
            new_doc._onchange_fiscal_operation_id()

            for line in new_doc.fiscal_line_ids:
                fsc_op_line = line.fiscal_operation_id.return_fiscal_operation_id
                if not fsc_op_line:
                    raise ValidationError(
                        _(
                            "The fiscal operation {} has no return Fiscal "
                            "Operation defined"
                        ).format(line.fiscal_operation_id)
                    )
                line.fiscal_operation_id = fsc_op_line
                line._onchange_fiscal_operation_id()
                line._onchange_fiscal_operation_line_id()

            return_docs |= new_doc
        return return_docs

    def action_create_return(self):
        action = self.env.ref("l10n_br_fiscal.document_all_action").read()[0]
        return_docs = self._create_return()

        if return_docs:
            action["domain"] = literal_eval(action["domain"] or "[]")
            action["domain"].append(("id", "in", return_docs.ids))

        return action

    def _get_email_template(self, state):
        self.ensure_one()
        return self.document_type_id.document_email_ids.search(
            [
                "|",
                ("state_edoc", "=", False),
                ("state_edoc", "=", state),
                ("issuer", "=", self.issuer),
                "|",
                ("document_type_id", "=", False),
                ("document_type_id", "=", self.document_type_id.id),
            ],
            limit=1,
            order="state_edoc, document_type_id",
        ).mapped("email_template_id")

    def send_email(self, state):
        self.ensure_one()
        email_template = self._get_email_template(state)
        if email_template:
            email_template.with_context(
                default_attachment_ids=self._get_mail_attachment()
            ).send_mail(self.id)

    @api.onchange("fiscal_operation_id")
    def _onchange_fiscal_operation_id(self):
        result = super()._onchange_fiscal_operation_id()
        if self.fiscal_operation_id:
            self.fiscal_operation_type = self.fiscal_operation_id.fiscal_operation_type
            self.edoc_purpose = self.fiscal_operation_id.edoc_purpose

        if self.issuer == DOCUMENT_ISSUER_COMPANY and not self.document_type_id:
            self.document_type_id = self.company_id.document_type_id

        subsequent_documents = [(6, 0, {})]
        for subsequent_id in self.fiscal_operation_id.mapped(
            "operation_subsequent_ids"
        ):
            subsequent_documents.append(
                (
                    0,
                    0,
                    {
                        "source_document_id": self.id,
                        "subsequent_operation_id": subsequent_id.id,
                        "fiscal_operation_id": subsequent_id.subsequent_operation_id.id,
                    },
                )
            )
        self.document_subsequent_ids = subsequent_documents
        return result

    def _prepare_referenced_subsequent(self, doc_referenced):
        self.ensure_one()
        return {
            "document_id": self.id,
            "document_related_id": doc_referenced.id,
            "document_type_id": doc_referenced.document_type_id.id,
            "document_serie": doc_referenced.document_serie,
            "document_number": doc_referenced.document_number,
            "document_date": doc_referenced.document_date,
            "document_key": doc_referenced.document_key,
        }

    def _document_reference(self, documents_referenced):
        self.ensure_one()
        for doc_referenced in documents_referenced:
            self.env["l10n_br_fiscal.document.related"].create(
                self._prepare_referenced_subsequent(doc_referenced)
            )

    @api.depends("document_subsequent_ids.subsequent_document_id")
    def _compute_document_subsequent_generated(self):
        for document in self:
            if not document.document_subsequent_ids:
                document.document_subsequent_generated = False
            else:
                document.document_subsequent_generated = all(
                    subsequent_id.operation_performed
                    for subsequent_id in document.document_subsequent_ids
                )

    def _generates_subsequent_operations(self):
        for record in self.filtered(lambda doc: not doc.document_subsequent_generated):
            for subsequent_id in record.document_subsequent_ids.filtered(
                lambda doc_sub: doc_sub._confirms_document_generation()
            ):
                subsequent_id.generate_subsequent_document()

    def cancel_edoc(self):
        self.ensure_one()
        if any(
            doc.state_edoc == SITUACAO_EDOC_AUTORIZADA
            for doc in self.document_subsequent_ids.mapped("document_subsequent_ids")
        ):
            message = _(
                "Canceling the document is not allowed: one or more "
                "associated documents have already been authorized."
            )
            raise UserWarning(message)

    def _get_mail_attachment(self):
        self.ensure_one()
        attachment_ids = []
        if self.state_edoc == SITUACAO_EDOC_AUTORIZADA:
            if self.file_report_id:
                attachment_ids.append(self.file_report_id.id)
            if self.authorization_file_id:
                attachment_ids.append(self.authorization_file_id.id)
        return attachment_ids

    def action_send_email(self):
        """Open a window to compose an email, with the fiscal document_type
        template message loaded by default
        """
        self.ensure_one()
        template = self._get_email_template(self.state)
        compose_form = self.env.ref("mail.email_compose_message_wizard_form", False)
        lang = self.env.context.get("lang")
        if template and template.lang:
            lang = template._render_template(template.lang, self._name, [self.id])
        self = self.with_context(lang=lang)
        ctx = dict(
            default_model="l10n_br_fiscal.document",
            default_res_id=self.id,
            default_use_template=bool(template),
            default_attachment_ids=self._get_mail_attachment(),
            default_template_id=template and template.id or False,
            default_composition_mode="comment",
            model_description=self.document_type_id.name or self._name,
            force_email=True,
        )
        return {
            "name": _("Send Fiscal Document Email Notification"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form.id, "form")],
            "view_id": compose_form.id,
            "target": "new",
            "context": ctx,
        }

    @api.depends("status_code", "status_name")
    def _compute_status_description(self):
        for record in self:
            if record.status_code:
                record.status_description = "{} - {}".format(
                    record.status_code or "",
                    record.status_name or "",
                )
            else:
                record.status_description = False

    def _eletronic_document_send(self):
        """Implement this method in your transmission module,
        to send the electronic document and use the method _change_state
        to update the state of the transmited document,

        def _eletronic_document_send(self):
            super()._document_send()
            for record in self.filtered(myfilter):
                Do your transmission stuff
                [...]
                Change the state of the document
        """
        for record in self.filtered(filter_processador):
            record._change_state(SITUACAO_EDOC_AUTORIZADA)

    def _document_send(self):
        no_electronic = self.filtered(
            lambda d: not d.document_electronic
            or not d.issuer == DOCUMENT_ISSUER_COMPANY
        )
        no_electronic._no_eletronic_document_send()
        electronic = self - no_electronic
        electronic._eletronic_document_send()

    def serialize(self):
        edocs = []
        self._serialize(edocs)
        return edocs

    def _serialize(self, edocs):
        return edocs

    def _target_new_tab(self, attachment_id):
        if attachment_id:
            return {
                "type": "ir.actions.act_url",
                "url": f"/web/content/{attachment_id.id}/{attachment_id.name}",
                "target": "new",
            }

    def view_xml(self):
        self.ensure_one()
        xml_file = self.authorization_file_id or self.send_file_id
        if not xml_file:
            self._document_export()
            xml_file = self.authorization_file_id or self.send_file_id
        if not xml_file:
            raise UserError(_("No XML file generated!"))
        return self._target_new_tab(xml_file)

    def make_pdf(self):
        pass

    def view_pdf(self):
        self.ensure_one()
        if not self.file_report_id or not self.authorization_file_id:
            self.make_pdf()
        if not self.file_report_id:
            raise UserError(_("No PDF file generated!"))
        return self._target_new_tab(self.file_report_id)

    def _document_status(self):
        """Retorna o status do documento em texto e se necessário,
        atualiza o status do documento"""
        return

    @api.constrains("issuer")
    def _check_issuer(self):
        for record in self.filtered(lambda d: d.document_electronic):
            if not record.issuer:
                raise ValidationError(
                    _(
                        "The field 'Issuer' is required for brazilian electronic "
                        "documents!"
                    )
                )
