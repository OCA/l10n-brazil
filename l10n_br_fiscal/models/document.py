# Copyright (C) 2013  Renato Lima - Akretion
# Copyright (C) 2019  KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from ast import literal_eval

from erpbrasil.base.fiscal.edoc import ChaveEdoc

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants.fiscal import (
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
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_INUTILIZADA,
)


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
        "l10n_br_fiscal.document.mixin",
        "l10n_br_fiscal.document.electronic",
        "l10n_br_fiscal.document.invoice.mixin",
    ]
    _description = "Fiscal Document"

    # used mostly to enable _inherits of account.invoice on
    # fiscal_document when existing invoices have no fiscal document.
    active = fields.Boolean(
        string="Active",
        default=True,
    )

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

    document_number = fields.Char(
        string="Document Number",
        copy=False,
        index=True,
    )

    rps_number = fields.Char(
        string="RPS Number",
        copy=False,
        index=True,
    )

    document_key = fields.Char(
        string="Key",
        copy=False,
        index=True,
    )

    document_date = fields.Datetime(
        string="Document Date",
        copy=False,
    )

    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        index=True,
        default=lambda self: self.env.user,
    )

    document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
    )

    operation_name = fields.Char(
        string="Operation Name",
        copy=False,
    )

    document_electronic = fields.Boolean(
        related="document_type_id.electronic",
        string="Electronic?",
        store=True,
    )

    date_in_out = fields.Datetime(
        string="Date Move",
        copy=False,
    )

    document_serie_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.serie",
        domain="[('active', '=', True)," "('document_type_id', '=', document_type_id)]",
    )

    document_serie = fields.Char(
        string="Serie Number",
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
        default=lambda self: self.env["res.company"]._company_default_get(
            "l10n_br_fiscal.document"
        ),
    )

    line_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document.line",
        inverse_name="document_id",
        string="Document Lines",
        copy=True,
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

    close_id = fields.Many2one(comodel_name="l10n_br_fiscal.closing", string="Close ID")

    document_type = fields.Char(
        related="document_type_id.code",
        store=True,
    )

    dfe_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.dfe",
        string="DF-e Consult",
    )

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

    @api.constrains("document_key")
    def _check_key(self):
        for record in self:
            if not record.document_key:
                return

            documents = record.env["l10n_br_fiscal.document"].search_count(
                [
                    ("id", "!=", record.id),
                    ("active", "=", True),
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
                ]
            )

            if documents:
                raise ValidationError(
                    _(
                        "There is already a fiscal document with this "
                        "key: {} !".format(record.document_key)
                    )
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
                ("active", "=", True),
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
                        "Serie: {}, Number: {} !".format(
                            record.document_serie, record.document_number
                        )
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
        "line_ids.estimate_tax",
        "line_ids.price_gross",
        "line_ids.amount_untaxed",
        "line_ids.amount_tax",
        "line_ids.amount_taxed",
        "line_ids.amount_total",
        "line_ids.financial_total",
        "line_ids.financial_total_gross",
        "line_ids.financial_discount_value",
        "line_ids.amount_tax_included",
        "line_ids.amount_tax_not_included",
        "line_ids.amount_tax_withholding",
    )
    def _compute_amount(self):
        super()._compute_amount()

    @api.model
    def create(self, values):
        if not values.get("document_date"):
            values["document_date"] = self._date_server_format()
        return super().create(values)

    def unlink(self):
        forbidden_states_unlink = [
            SITUACAO_EDOC_AUTORIZADA,
            SITUACAO_EDOC_CANCELADA,
            SITUACAO_EDOC_DENEGADA,
            SITUACAO_EDOC_INUTILIZADA,
        ]

        for record in self.filtered(
            lambda d: d != self.env.user.company_id.fiscal_dummy_id
            and d.state_edoc in forbidden_states_unlink
        ):
            raise ValidationError(
                _(
                    "You cannot delete fiscal document number {} with "
                    "the status: {}!".format(record.document_number, record.state_edoc)
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
                        "Operation defined".format(record.fiscal_operation_id)
                    )
                )

            new_doc = record.copy()
            new_doc.fiscal_operation_id = fsc_op
            new_doc._onchange_fiscal_operation_id()

            for line in new_doc.line_ids:
                fsc_op_line = line.fiscal_operation_id.return_fiscal_operation_id
                if not fsc_op_line:
                    raise ValidationError(
                        _(
                            "The fiscal operation {} has no return Fiscal "
                            "Operation defined".format(line.fiscal_operation_id)
                        )
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
            email_template.send_mail(self.id)

    def _after_change_state(self, old_state, new_state):
        self.ensure_one()
        super()._after_change_state(old_state, new_state)
        self.send_email(new_state)

    @api.onchange("fiscal_operation_id")
    def _onchange_fiscal_operation_id(self):
        super()._onchange_fiscal_operation_id()
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

    @api.onchange("document_type_id")
    def _onchange_document_type_id(self):
        if self.document_type_id and self.issuer == DOCUMENT_ISSUER_COMPANY:
            self.document_serie_id = self.document_type_id.get_document_serie(
                self.company_id, self.fiscal_operation_id
            )

    @api.onchange("document_serie_id")
    def _onchange_document_serie_id(self):
        if self.document_serie_id and self.issuer == DOCUMENT_ISSUER_COMPANY:
            self.document_serie = self.document_serie_id.code

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

    def action_send_email(self):
        """Open a window to compose an email, with the fiscal document_type
        template message loaded by default
        """
        self.ensure_one()
        template = self._get_email_template(self.state)
        compose_form = self.env.ref("mail.email_compose_message_wizard_form", False)
        lang = self.env.context.get("lang")
        if template and template.lang:
            lang = template._render_template(template.lang, self._name, self.id)
        self = self.with_context(lang=lang)
        ctx = dict(
            default_model="l10n_br_fiscal.document",
            default_res_id=self.id,
            default_use_template=bool(template),
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
