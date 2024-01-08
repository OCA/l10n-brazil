# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from odoo import api, fields, models
from odoo.osv.expression import AND

from odoo.addons.l10n_br_fiscal.constants.fiscal import SITUACAO_EDOC


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
        string="Fiscal Operation",
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

    # Fiscal document fields

    document_key = fields.Char(
        string="Document Key",
        copy=False,
        index=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    document_electronic = fields.Boolean(
        related="document_type_id.electronic",
        string="Electronic?",
        store=True,
    )

    document_serie_id = fields.Many2one(
        string="Document Serie",
        comodel_name="l10n_br_fiscal.document.serie",
        domain="[('active', '=', True)," "('document_type_id', '=', document_type_id)]",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    document_serie_number = fields.Char(
        string="Document Number",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    edoc_purpose = fields.Selection(
        selection=[
            ("1", "Normal"),
            ("2", "Complementary"),
            ("3", "Adjustment"),
            ("4", "Goods return"),
        ],
        string="eDoc Purpose",
        default="1",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    status_code = fields.Char(
        copy=False,
    )

    status_description = fields.Char(
        string="Status Name",
        copy=False,
    )

    # Authorization Fields

    authorization_date = fields.Datetime(
        string="Authorization Date",
        copy=False,
    )

    authorization_file = fields.Binary(
        string="Authorization File",
        readonly=True,
    )

    # Cancellation Fields

    cancel_date = fields.Datetime(
        string="Cancellation Date",
        copy=False,
    )

    cancel_file = fields.Binary(
        string="Cancellation File",
        readonly=True,
    )

    cancel_document_key = fields.Char(
        string="Cancellation Key",
        copy=False,
        index=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    state_edoc = fields.Selection(
        selection=SITUACAO_EDOC,
        string="eDoc State",
        copy=False,
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

    @api.depends("lines.price_subtotal_incl")
    def _amount_all(self):
        """Compute the total amounts of the SO."""
        for order in self:
            order._compute_amount()

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super()._order_fields(ui_order)

        order_fields.update({
            "cnpj_cpf": ui_order.get("cnpj_cpf"),
            "fiscal_operation_id": ui_order.get("fiscal_operation_id"),
            "document_type_id": ui_order.get("document_type_id"),
            "state_edoc": ui_order.get("state_edoc"),
            "document_serie_id": ui_order.get("document_serie_id"),
            "document_serie_number": ui_order.get("document_serie_number"),
            "document_key": ui_order.get("document_key"),
            "authorization_date": ui_order.get("authorization_date") if ui_order.get("authorization_date") else datetime.now(),
            "authorization_file": ui_order.get("authorization_file"),
            "additional_data": ui_order.get("additional_data"),
        })

        return order_fields

    def _export_for_ui(self, order):
        res = super()._export_for_ui(order)

        res.update({
            "cnpj_cpf": order.cnpj_cpf,
            "document_type_id": order.document_type_id.id,
            "fiscal_operation_id": order.fiscal_operation_id.id,
            "status_code": order.status_code,
            "status_description": order.status_description,
            "state_edoc": order.state_edoc,
            "document_serie_number": order.document_serie_number,
            "document_serie_id": order.document_serie_id.id,
            "document_key": order.document_key,
            "authorization_date": order.authorization_date.astimezone() if order.authorization_date else None,
            "cancel_date": order.cancel_date.astimezone() if order.cancel_date else None,
            "additional_data": order.additional_data,
        })

        return res

    @api.model
    def cancel_pos_order(self, result):
        """
            Cancel a Point of Sale (POS) order and initiate the refund process.
        """
        order = self.env["pos.order"].search([("pos_reference", "=", result["pos_reference"])], limit=1)
        self._cancel_order(order, result)
        self._refund_order(order)

    def _cancel_order(self, order, result):
        """
            Cancel a specific order in the system and perform related operations.
        """
        order.write({"state": "cancel"})
        order._populate_cancel_order_fields(result)
        order.with_context(mail_create_nolog=True, tracking_disable=True, mail_create_nosubscribe=True, mail_notrack=True).refund()

    def _populate_cancel_order_fields(self, order_vals):
        """
            Populate fields related to canceling an order with values from the provided dictionary.
        """
        self.write({
            "state_edoc": "cancelada",
        })

    def refund(self):
        res = super(PosOrder, self.with_context(
                    mail_create_nolog=True,
                    tracking_disable=True,
                    mail_create_nosubscribe=True,
                    mail_notrack=True,
                    )).refund()
        refund_order = self.browse(res["res_id"])
        self._update_refund_order(refund_order)
        self._generate_refund_payments(refund_order)

        return res

    def _update_refund_order(self, refund_order):
        """
            Update the refunded order with specific attributes
        """
        refund_order.write({
            "amount_total": self.amount_total * -1,
            "state_edoc": "cancelada"
        })

    def _generate_refund_payments(self, refund_order):
        """
            Generate refund payments for the refunded order.
        """
        payment_data = [
            {
                "config_id": refund_order.config_id.id,
                "payment_method_id": payment.payment_method_id.id,
                "amount": payment.amount * -1,
            }
            for payment in self.payment_ids
        ]
        payment_wizards = self.env["pos.make.payment"].create(payment_data)

        for payment_wizard in payment_wizards:
            payment_wizard.with_context(active_id=refund_order.id).check()

    def _refund_order(self, order):
        """
            Process a refund for a Point of Sale (POS) order if applicable.
        """
        refund_order = self.search([("pos_reference", "=", order.pos_reference), ("amount_total", ">", 0)], limit=1)
        refund_order.pos_reference = f"{order.pos_reference}-cancelled"

    @api.model
    def search_paid_order_ids(self, config_id, domain, limit, offset):
        """
            Search for 'paid' orders with the given configuration ID, custom
            domain, limit, and offset.
        """

        default_domain = [
            "&",
            ("config_id", "=", config_id),
            "!",
            "|",
            ("state", "=", "draft"),
            ("state", "=", "cancel"),
        ]

        final_domain = AND([domain, default_domain]) if domain else default_domain

        order_ids = self.search(final_domain, limit=limit, offset=offset).ids
        total_count = self.search_count(final_domain)

        return {"ids": order_ids, "total_count": total_count}
