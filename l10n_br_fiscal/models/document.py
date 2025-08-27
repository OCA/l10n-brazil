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
    SITUACAO_EDOC,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_EM_DIGITACAO,
    SITUACAO_EDOC_INUTILIZADA,
    SITUACAO_FISCAL,
)


class Document(models.Model):
    """
    Base implementation for Brazilian fiscal documents.

    This model serves as the foundational structure for various fiscal
    documents within the Brazilian localization. It's designed to be
    extensible, allowing other OCA modules to build upon it, ideally
    minimizing the need for additional custom coding for common fiscal
    document functionalities.

    Key aspects to note:
    - The fiscal document manages two primary states:
        - Electronic Document State (`state_edoc`): Reflects the status
          of the document in its electronic lifecycle (e.g., Draft,
          Authorized, Cancelled).
        - Fiscal State (`state_fiscal`): Represents the document's status
          from a purely fiscal accounting perspective (e.g., Regular,
          Cancelled for fiscal purposes). This state is less automated
          and often managed by the fiscal responsible to ensure correct
          reporting, such as in SPED Fiscal.

    This model inherits common fields and methods from
    `l10n_br_fiscal.document.mixin` and includes features for document
    numbering, key validation, partner and company fiscal details, line
    items and returns.
    """

    _name = "l10n_br_fiscal.document"
    _inherit = [
        "l10n_br_fiscal.document.mixin",
        "mail.thread",
        "mail.activity.mixin",
    ]
    _description = "Fiscal Document"
    _check_company_auto = True

    name = fields.Char(
        compute="_compute_name",
        store=True,
        index=True,
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

    fiscal_operation_id = fields.Many2one(
        "l10n_br_fiscal.operation",
        string="Fiscal Operation",
        domain="[('state', '=', 'approved')]",
    )

    fiscal_operation_type = fields.Selection(
        store=True,
    )

    rps_number = fields.Char(
        string="RPS Number",
        copy=False,
        index=True,
        unaccent=False,
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
        compute="_compute_edoc_purpose",
        store=True,
        precompute=True,
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

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        compute="_compute_currency_id",
    )

    # this related "state" field is required for the status bar widget
    # while state_edoc avoids colliding with the state field
    # of objects where the fiscal mixin might be injected.
    state = fields.Selection(related="state_edoc", string="State")

    transport_modal = fields.Selection(
        selection=[
            ("01", "Rodoviário"),
            ("02", "Aéreo"),
            ("03", "Aquaviário"),
            ("04", "Ferroviário"),
            ("05", "Dutoviário"),
            ("06", "Multimodal"),
        ],
        string="Modal de Transporte",
    )

    service_provider = fields.Selection(
        selection=[
            ("0", "Remetente"),
            ("1", "Expedidor"),
            ("2", "Recebedor"),
            ("3", "Destinatário"),
            ("4", "Outros"),
        ],
        string="Tomador do Serviço",
    )
    partner_legal_name = fields.Char(
        string="Legal Name",
        related="partner_id.legal_name",
    )
    partner_cnpj_cpf = fields.Char(
        string="CNPJ",
        related="partner_id.vat",
    )
    partner_l10n_br_ie_code = fields.Char(
        string="State Tax Number",
        related="partner_id.l10n_br_ie_code",
    )

    processador_edoc = fields.Selection(
        related="company_id.processador_edoc",
    )
    company_l10n_br_ie_code_st = fields.Char(
        string="Company ST State Tax Number",
    )

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
                    _("There is already a fiscal document with this key: {} !").format(
                        record.document_key
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

    @api.onchange("fiscal_operation_type")
    def _onchange_fiscal_operation_type(self):
        domain = [("state", "=", "approved")]
        if self.fiscal_operation_type:
            domain.append(("fiscal_operation_type", "=", self.fiscal_operation_type))
        if (
            self.fiscal_operation_id
            and self.fiscal_operation_id.fiscal_operation_type
            != self.fiscal_operation_type
        ):
            self.fiscal_operation_id = False
        return {"domain": {"fiscal_operation_id": domain}}

    @api.depends("company_id")
    def _compute_currency_id(self):
        for doc in self:
            doc.currency_id = doc.company_id.currency_id or self.env.company.currency_id

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
            if not self.partner_id.vat:
                name += " - " + _("Unidentified Consumer")
            elif self.partner_id.legal_name:
                name += " - " + self.partner_id.legal_name
                name += " - " + self.partner_id.vat
            else:
                name += " - " + self.partner_id.name
                name += " - " + self.partner_id.vat
        elif self._context.get("fiscal_document_no_company"):
            name += type_serie_number
        else:
            name += "{name}/{type_serie_number}".format(
                name=self.company_id.name or "",
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

    @api.model
    def _get_fiscal_lines_field_name(self):
        return "fiscal_line_ids"

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

    def _create_return(self):
        return_docs = self.env[self._name]
        for record in self:
            fsc_op = record.fiscal_operation_id.return_fiscal_operation_id
            if not fsc_op:
                raise ValidationError(
                    _(
                        "The fiscal operation {} has no return Fiscal Operation defined"
                    ).format(record.fiscal_operation_id)
                )

            new_doc = record.copy()
            new_doc.fiscal_operation_id = fsc_op

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

            return_docs |= new_doc
        return return_docs

    def action_create_return(self):
        action = self.env.ref("l10n_br_fiscal.document_all_action").read()[0]
        return_docs = self._create_return()

        if return_docs:
            action["domain"] = literal_eval(action["domain"] or "[]")
            action["domain"].append(("id", "in", return_docs.ids))

        return action

    # the following actions are meant to be implemented in other modules such as
    # l10n_br_fiscal_edi. They are defined here so they can be overriden in modules
    # that don't depend on l10n_br_fiscal_edi (such as l10n_br_account).
    def view_pdf(self):
        pass

    def view_xml(self):
        pass

    def action_document_confirm(self):
        pass

    def action_document_send(self):
        pass

    def action_document_back2draft(self):
        pass

    def action_document_cancel(self):
        pass

    def action_document_invalidate(self):
        pass

    def action_document_correction(self):
        pass

    def exec_after_SITUACAO_EDOC_DENEGADA(self, old_state, new_state):
        # see https://github.com/OCA/l10n-brazil/pull/3272
        pass

    @api.depends("fiscal_operation_id")
    def _compute_edoc_purpose(self):
        for record in self:
            record.edoc_purpose = record.fiscal_operation_id.edoc_purpose
