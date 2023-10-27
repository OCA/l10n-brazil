# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from datetime import datetime

from odoo import api, fields, models
from odoo.osv.expression import AND

from odoo.addons.l10n_br_fiscal.constants.fiscal import SITUACAO_EDOC

NFCE_IND_PRES_DEFAULT = "1"

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _name = "pos.order"
    _inherit = [
        _name,
        "mail.thread",
        "mail.activity.mixin",
        "l10n_br_fiscal.document.mixin",
    ]

    @api.model
    def _default_fiscal_operation(self):
        return self.env.company.out_pos_fiscal_operation_id

    @api.model
    def _fiscal_operation_domain(self):
        domain = [("state", "=", "approved")]
        return domain

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain(),
    )

    cnpj_cpf = fields.Char(
        string="CNPJ/CPF",
        related=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    legal_name = fields.Char(
        string="Legal Name",
        related="partner_id.legal_name",
    )

    ie = fields.Char(
        string="State Tax Number/RG",
        related="partner_id.inscr_est",
    )

    # Fiscal document fields

    document_number = fields.Char(
        copy=False,
        index=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    document_rps_number = fields.Char(
        string="Document Number",
        copy=False,
        index=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    document_key = fields.Char(
        string="Key",
        copy=False,
        index=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    ind_pres = fields.Selection(
        default=NFCE_IND_PRES_DEFAULT,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    document_type = fields.Char(
        related="document_type_id.code",
        store=True,
    )

    operation_name = fields.Char(
        copy=False,
    )

    document_electronic = fields.Boolean(
        related="document_type_id.electronic",
        string="Electronic?",
        store=True,
    )

    document_qrcode_signature = fields.Char(
        string="QrCode Signature",
        copy=False,
    )

    document_qrcode_url = fields.Char(
        string="QrCode URL",
        copy=False,
    )

    date_in_out = fields.Datetime(
        string="Date Move",
        copy=False,
    )

    document_serie_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.serie",
        domain="[('active', '=', True)," "('document_type_id', '=', document_type_id)]",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    document_serie = fields.Char(
        string="Serie Number",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    partner_shipping_id = fields.Many2one(
        comodel_name="res.partner",
        string="Shipping Address",
    )

    edoc_purpose = fields.Selection(
        selection=[
            ("1", "Normal"),
            ("2", "Complementary"),
            ("3", "Adjustment"),
            ("4", "Goods return"),
        ],
        string="Goal",
        default="1",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    status_code = fields.Char(
        copy=False,
    )

    status_name = fields.Char(
        copy=False,
    )

    status_description = fields.Char(
        string="Status Name",
        copy=False,
    )

    authorization_date = fields.Datetime(
        copy=False,
    )

    authorization_protocol = fields.Char(
        readonly=True,
    )

    authorization_file = fields.Binary(
        readonly=True,
    )

    cancel_date = fields.Datetime(
        copy=False,
    )

    cancel_protocol = fields.Char(
        readonly=True,
    )

    cancel_file = fields.Binary(
        readonly=True,
    )

    state_edoc = fields.Selection(
        selection=SITUACAO_EDOC,
        string="e-doc Status",
        copy=False,
        index=True,
    )

    document_session_number = fields.Char(
        string="Session identifier number",
        copy=False,
    )

    document_date = fields.Date(string="Date")

    # TODO: Switch to events?
    document_file_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="XML",
        copy=False,
        readonly=True,
    )
    cancel_document_session_number = fields.Char(
        string="Cancel Session identifier number",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    cancel_document_key = fields.Char(
        string="Cancel Key",
        copy=False,
        index=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    cancel_document_file_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="Cancel XML",
        copy=False,
        readonly=True,
    )

    fiscal_coupon_date = fields.Datetime(
        string="Coupon Fiscal Date",
        readonly=True,
        index=True,
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="pos_order_fiscal_comment_rel",
        column1="pos_order_id",
        column2="comment_id",
        string="Comments",
    )

    additional_data = fields.Text()

    def _get_amount_lines(self):
        """Get object lines instaces used to compute fields"""
        return self.mapped("lines")

    @api.depends("lines")
    def _compute_amount(self):
        return super()._compute_amount()

    @api.depends("lines.price_subtotal_incl")
    def _amount_all(self):
        """Compute the total amounts of the SO."""
        for order in self:
            order._compute_amount()

    @api.model
    def _process_order(self, order, draft, existing_order):
        order_id = super(
            PosOrder,
            self.with_context(
                mail_create_nolog=True,
                tracking_disable=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
            ),
        )._process_order(order, draft, existing_order)

        return order_id

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super()._order_fields(ui_order)
        order_fields["status_code"] = ui_order.get("status_code")
        order_fields["status_name"] = ui_order.get("status_name")
        order_fields["status_description"] = ui_order.get("status_description")

        # TODO: Save with utc
        if ui_order.get("authorization_date"):
            order_fields["authorization_date"] = datetime.fromisoformat(
                ui_order.get("authorization_date")
            )
        order_fields["authorization_protocol"] = ui_order.get("authorization_protocol")
        order_fields["authorization_file"] = ui_order.get("authorization_file")

        if ui_order.get("cancel_date"):
            order_fields["cancel_date"] = datetime.fromisoformat(
                ui_order.get("cancel_date")
            )
        order_fields["cancel_protocol"] = ui_order.get("cancel_protocol")
        order_fields["cancel_file"] = ui_order.get("cancel_file")

        order_fields["state_edoc"] = ui_order.get("state_edoc")
        order_fields["document_number"] = ui_order.get("document_number")
        order_fields["document_serie"] = ui_order.get("document_serie")
        order_fields["document_session_number"] = ui_order.get(
            "document_session_number"
        )
        order_fields["document_rps_number"] = ui_order.get("document_rps_number")

        order_fields["document_key"] = ui_order.get("document_key")
        order_fields["document_date"] = ui_order.get("document_date")
        order_fields["document_electronic"] = ui_order.get("document_electronic")

        order_fields["document_qrcode_signature"] = ui_order.get(
            "document_qrcode_signature"
        )
        order_fields["document_qrcode_url"] = ui_order.get("document_qrcode_url")

        # order_fields['document_event_messages'] = ui_order.get('document_qrcode_url')

        order_fields["fiscal_operation_id"] = ui_order.get("fiscal_operation_id")
        order_fields["document_type_id"] = ui_order.get("document_type_id")
        order_fields["document_type"] = ui_order.get("document_type")

        order_fields["cnpj_cpf"] = ui_order.get("cnpj_cpf")

        order_fields["additional_data"] = ui_order.get("additional_data")

        return order_fields

    def _export_for_ui(self, order):
        res = super()._export_for_ui(order)

        res["status_code"] = order.status_code
        res["status_name"] = order.status_name
        res["status_description"] = order.status_description

        if order.authorization_date:
            res["authorization_date"] = order.authorization_date.astimezone()

        res["authorization_protocol"] = order.authorization_protocol
        res["authorization_file"] = order.authorization_file

        if order.cancel_date:
            res["cancel_date"] = order.cancel_date.astimezone()
        res["cancel_protocol"] = order.cancel_protocol
        res["cancel_file"] = order.cancel_file

        res["state_edoc"] = order.state_edoc
        res["document_number"] = order.document_number
        res["document_serie"] = order.document_serie
        res["document_session_number"] = order.document_session_number
        res["document_rps_number"] = order.document_rps_number

        res["document_key"] = order.document_key
        res["document_date"] = order.document_date
        res["document_electronic"] = order.document_electronic

        res["document_qrcode_signature"] = order.document_qrcode_signature
        res["document_qrcode_url"] = order.document_qrcode_url

        # res['document_event_messages'] = order.document_event_messages

        res["fiscal_operation_id"] = order.fiscal_operation_id.id
        res["document_type_id"] = order.document_type_id.id
        res["document_type"] = order.document_type

        res["cnpj_cpf"] = order.cnpj_cpf

        res["additional_data"] = order.additional_data

        return res

    def _populate_cancel_order_fields(self, order_vals):
        self.cancel_document_key = order_vals["chave_cfe"]
        self.cancel_document_session_number = order_vals["numSessao"]
        self.state_edoc = "cancelada"
        self.cancel_file = order_vals["xml"]

    def _generate_refund_payments(self, refund_order):
        for payment in self.payment_ids:
            payment_wizard = self.env["pos.make.payment"].create(
                {
                    "config_id": refund_order.config_id.id,
                    "payment_method_id": payment.payment_method_id.id,
                    "amount": payment.amount * -1,
                }
            )

            payment_wizard.with_context(active_id=refund_order.id).check()

    def refund(self):
        res = super(
            PosOrder,
            self.with_context(
                mail_create_nolog=True,
                tracking_disable=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
            ),
        ).refund()
        refund_order = self.browse(res["res_id"])
        refund_order.amount_total = self.amount_total * -1
        refund_order.state_edoc = "cancelada"

        self._generate_refund_payments(refund_order)

        return res

    @api.model
    def cancel_order(self, result):
        _logger.info(f"Result: {result}")
        order = self.browse(result["order_id"])
        order.write({"state": "cancel"})

        order._populate_cancel_order_fields(result)

        order.with_context(
            mail_create_nolog=True,
            tracking_disable=True,
            mail_create_nosubscribe=True,
            mail_notrack=True,
        ).refund()

        refund_order = self.search(
            [("pos_reference", "=", order.pos_reference), ("amount_total", ">", 0)]
        )
        refund_order.pos_reference = f"{order.pos_reference}-cancelled"

    @api.model
    def search_paid_order_ids(self, config_id, domain, limit, offset):
        """Search for 'paid' orders that satisfy the given domain, limit and offset."""
        default_domain = [
            "&",
            ("config_id", "=", config_id),
            "!",
            "|",
            ("state", "=", "draft"),
            ("state", "=", "cancel"),
        ]
        real_domain = AND([domain, default_domain])
        ids = self.search(AND([domain, default_domain]), limit=limit, offset=offset).ids
        totalCount = self.search_count(real_domain)
        return {"ids": ids, "totalCount": totalCount}
