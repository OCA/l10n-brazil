# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from datetime import datetime

import pytz

from odoo import api, fields, models

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
            ("2", "Complementar"),
            ("3", "Ajuste"),
            ("4", "Devolução de mercadoria"),
        ],
        string="Finalidade",
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
        string="Situação e-doc",
        copy=False,
        index=True,
    )

    document_session_number = fields.Char(
        string="Numero identificador sessao",
        copy=False,
    )

    document_date = fields.Date(string="Data")

    # TODO: Trocar para eventos?
    document_file_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="XML",
        copy=False,
        readonly=True,
    )
    cancel_document_session_number = fields.Char(
        string="Numero identificador sessao",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    cancel_document_key = fields.Char(
        string="Key",
        copy=False,
        index=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    cancel_document_file_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="XML",
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
        super()._compute_amount()

    @api.depends("lines.price_subtotal_incl")
    def _amount_all(self):
        """Compute the total amounts of the SO."""
        for order in self:
            order._compute_amount()

    def _save_attachment(
        self, file_name="", file_content="", file_type="application/xml"
    ):
        self.ensure_one()
        attachment = self.env["ir.attachment"]
        domain = [
            ("res_model", "=", self._name),
            ("res_id", "=", self.id),
            ("name", "=", file_name),
        ]
        attachment_ids = attachment.search(domain)
        attachment_ids.unlink()
        vals = {
            "name": file_name,
            "datas_fname": file_name,
            "res_model": self._name,
            "res_id": self.id,
            "datas": file_content.encode("utf-8"),
            "mimetype": file_type,
        }
        return attachment.create(vals)

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

        if order.get("authorization_file"):
            order.document_file_id = order._save_attachment(
                file_name=order.document_key + ".xml",
                file_content=order.pop("authorization_file"),
            ).id

        if order.get("cancel_file"):
            order.cancel_document_file_id = order._save_attachment(
                file_name=order.document_key + ".xml",
                file_content=order.pop("cancel_file"),
            ).id

        return order_id

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        order_fields["status_code"] = ui_order.get("status_code")
        order_fields["status_name"] = ui_order.get("status_name")
        order_fields["status_description"] = ui_order.get("status_description")

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

    # @api.model
    # def return_orders_from_session(self, **kwargs):
    #     orders_session = {'Orders': []}
    #     orders = self.search(
    #         [
    #             ('session_id', '=', kwargs['session_id']),
    #             ('state', '=', 'paid'),
    #             ('chave_cfe', '!=', '')
    #         ], limit=5, order="id DESC"
    #     )
    #     for order in orders:
    #         order_vals = {
    #             'id': order.id,
    #             'name': order.name,
    #             'pos_reference': order.pos_reference,
    #             'partner': order.partner_id.name,
    #             'date': order.date_order,
    #             'total': '%.2f' % order.amount_total,
    #             'chave_cfe': order.chave_cfe,
    #             'canceled_order': order.canceled_order,
    #             'can_cancel': False,
    #         }
    #         orders_session['Orders'].append(order_vals)
    #         orders_session['Orders'][0]['can_cancel'] = True
    #     return orders_session
    #
    # @api.model
    # def refund(self, ids, dados):
    #     """Create a copy of order  for refund order"""
    #     clone_list = []
    #
    #     for order in self.browse(ids):
    #
    #         for statement in order.statement_ids:
    #             if statement.journal_id.sat_payment_mode == "05":
    #                 order.partner_id.credit_limit += statement.amount
    #
    #         current_session_ids = self.env['pos.session'].search([
    #             ('state', '!=', 'closed'),
    #             ('user_id', '=', self.env.uid)]
    #         )
    #
    #         # if not current_session_ids:
    #         #     raise osv.except_osv(_('Error!'), _('To return product(s),
    #         # you need to open a session that will be used to register
    #         # the refund.'))
    #
    #         clone_id = order.copy()
    #
    #         clone_id.write({
    #             'name': order.name + ' CANCEL',
    #             'pos_reference': order.pos_reference + ' CANCEL',
    #             'session_id': current_session_ids.id,
    #             'date_order': time.strftime('%Y-%m-%d %H:%M:%S'),
    #             'pos_order_associated': order.id,
    #             'canceled_order': True,
    #             'chave_cfe': '',
    #             'cfe_return': '',
    #             'num_sessao_sat': ''
    #         })
    #
    #         clone_list.append(clone_id.id)
    #
    #     for clone in self.browse(clone_list):
    #         for order_line in clone.lines:
    #             order_line.write({
    #                 'qty': -order_line.qty
    #             })
    #
    #         statements = self.env['account.bank.statement.line']
    #
    #         for statement in order.statement_ids:
    #             vals = {
    #                 'name': statement.display_name + " CANCEL",
    #                 'statement_id': statement.statement_id.id,
    #                 'ref': statement.ref,
    #                 'pos_statement_id': clone.id,
    #                 'journal_id': statement.journal_id.id,
    #                 'amount': statement.amount * -1,
    #                 'date': statement.date,
    #                 'partner_id': statement.partner_id.id
    #                 if statement.partner_id else False,
    #                 'account_id': statement.account_id.id
    #             }
    #
    #             statements.create(vals)
    #
    #         clone.action_paid()
    #         parent_order = self.browse(clone.pos_order_associated.id)
    #         parent_order.write({
    #             'canceled_order': True,
    #             'pos_order_associated': clone.id,
    #             'cfe_cancelamento_return': dados['xml'],
    #             'chave_cfe_cancelamento': dados['numSessao'],
    #             'num_sessao_sat_cancelamento': dados['chave_cfe'],
    #         })
    #
    #     return True

    def _export_for_ui(self, order):
        res = super()._export_for_ui(order)

        timezone = pytz.timezone(self._context.get("tz") or self.env.user.tz or "UTC")

        res["status_code"] = order.status_code
        res["status_name"] = order.status_name
        res["status_description"] = order.status_description

        if order.authorization_date:
            res["authorization_date"] = order.authorization_date.astimezone(timezone)

        res["authorization_protocol"] = order.authorization_protocol
        res["authorization_file"] = order.authorization_file

        if order.cancel_date:
            res["cancel_date"] = order.cancel_date.astimezone(timezone)
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

    def _generate_refund_payments(self, refund_order):
        for payment in self.statement_ids:
            payment_wizard = self.env["pos.make.payment"].create(
                {
                    "session_id": refund_order.session_id.id,
                    "journal_id": payment.journal_id.id,
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

        self._generate_refund_payments(refund_order)

        return res

    @api.model
    def cancelar_order(self, result):
        _logger.info(f"Result: {result}")
        order = self.browse(result["order_id"])

        order._populate_cancel_order_fields(result)
        order.cancel_document_file_id = order._save_attachment(
            file_name=result["chave_cfe"] + ".xml", file_content=result["xml"]
        ).id

        order.with_context(
            mail_create_nolog=True,
            tracking_disable=True,
            mail_create_nosubscribe=True,
            mail_notrack=True,
        ).refund()
