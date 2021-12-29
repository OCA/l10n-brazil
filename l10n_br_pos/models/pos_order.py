# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from satcomum.ersat import ChaveCFeSAT

from odoo import api, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import NFCE_IND_PRES_DEFAULT


class PosOrder(models.Model):
    _name = "pos.order"
    _inherit = [
        _name,
        "mail.thread",
        "mail.activity.mixin",
        "l10n_br_fiscal.document.mixin",
    ]

    cnpj_cpf = fields.Char(
        string="CNPJ/CPF",
        related=False,
        readonly=True,
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
        string="Document Number",
        copy=False,
        index=True,
        readonly=True,
    )

    document_key = fields.Char(
        string="Key",
        copy=False,
        index=True,
        readonly=True,
    )

    ind_pres = fields.Selection(
        default=NFCE_IND_PRES_DEFAULT,
    )

    document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
        readonly=True,
    )

    document_type = fields.Char(
        related="document_type_id.code",
        store=True,
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
        readonly=True,
    )

    document_serie = fields.Char(
        string="Serie Number",
        readonly=True,
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
    )

    document_authorization_date = fields.Datetime(
        string="Authorization Date",
        copy=False,
    )

    document_status_code = fields.Char(
        string="Status Code",
        copy=False,
    )
    document_status_name = fields.Char(
        string="Status Name",
        copy=False,
    )
    document_session_number = fields.Char(
        string="Numero identificador sessao",
        copy=False,
    )
    # TODO: Trocar para eventos?
    document_file_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="XML",
        copy=False,
        readony=True,
    )

    @api.multi
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
    def _process_order(self, pos_order_vals):
        order = super(PosOrder, self.with_context(
            mail_create_nolog=True, tracking_disable=True, mail_create_nosubscribe=True,
            mail_notrack=True))._process_order(pos_order_vals)
        document_file = pos_order_vals.get("document_file")
        if document_file:
            order.document_file_id = order._save_attachment(
                file_name=order.document_key + ".xml", file_content=document_file
            ).id
        return order

    @api.model
    def _order_fields(self, ui_order):
        result = super()._order_fields(ui_order)
        ui_order.get("document_type")
        temp = {
            "document_authorization_date": ui_order.get("document_authorization_date"),
            "document_status_code": ui_order.get("document_status_code"),
            "document_status_name": ui_order.get("document_status_name"),
            "document_session_number": ui_order.get("document_session_number"),
            "document_key": ui_order.get("document_key"),
            "cnpj_cpf": ui_order.get("cnpj_cpf"),
            "fiscal_operation_id": ui_order.get("fiscal_operation_id"),
            "document_type_id": ui_order.get("document_type_id"),
        }
        document_key = ui_order.get("document_key")
        if document_key:
            key = ChaveCFeSAT(document_key)
            temp.update(
                {
                    "document_number": key.numero_cupom_fiscal,
                    "document_serie": key.numero_serie,
                }
            )
        result.update(temp)
        return result

    # @api.model
    # def _pos_order_type(self):
    #     return SIMPLIFIED_INVOICE_TYPE + [('nfe', 'NF-E')]
    #
    # simplified = fields.Boolean(string='Simplified invoice', default=True)
    # fiscal_document_type = fields.Selection(
    #     string='Fiscal Document Type',
    #     selection='_pos_order_type',
    #     states={'draft': [('readonly', False)]},
    #     readonly=True
    # )
    #
    # cfe_return = fields.Binary('Retorno Cfe')
    #
    # chave_cfe = fields.Char('Chave da Cfe')
    #
    # num_sessao_sat = fields.Char('Número Sessão SAT envio Cfe')
    #
    # pos_order_associated = fields.Many2one('pos.order', 'Venda Associada')
    #
    # canceled_order = fields.Boolean('Venda Cancelada', readonly=True)
    #
    # cfe_cancelamento_return = fields.Binary('Retorno Cfe Cancelamento')
    #
    # chave_cfe_cancelamento = fields.Char('Chave da Cfe Cancelamento')
    #
    # num_sessao_sat_cancelamento = fields.Char(
    #     'Número Sessão SAT Cancelamento'
    # )

    # @api.multi
    # def write(self, vals):
    #     result = super(PosOrder, self).write(vals)
    #     self.simplified_limit_check()
    #     return result
    #
    # @api.model
    # def create(self, vals):
    #     order = super(PosOrder, self).create(vals)
    #     pos_config = order.session_id.config_id
    #     if pos_config.iface_sat_via_proxy:
    #         sequence = pos_config.sequence_id
    #         cfe = ChaveCFeSAT(vals['chave_cfe'])
    #         order.name = sequence._interpolate_value("%s / %s" % (
    #             cfe.numero_serie,
    #             cfe.numero_cupom_fiscal,
    #         ))
    #     order.simplified_limit_check()
    #     return order

    # @api.multi
    # def create_picking(self):
    #     super().create_picking()
    #     fiscal_category = self.session_id.config_id.fiscal_operation_id
    #     self.picking_id.fiscal_operation_id = \
    #         fiscal_category.id
    #     obj_fp_rule = self.env['account.fiscal.position.rule']
    #     kwargs = {
    #         'partner_id': self.picking_id.company_id.partner_id.id,
    #         'partner_shipping_id': self.picking_id.company_id.partner_id.id,
    #         'fiscal_operation_id': fiscal_category.id,
    #         'company_id': self.picking_id.company_id.id,
    #     }
    #     self.picking_id.fiscal_position = obj_fp_rule.apply_fiscal_mapping(
    #         {'value': {}}, **kwargs
    #     )['value']['fiscal_position']
    #     return True
    #
    # @api.model
    # def _process_order(self, order):
    #     order_id = super()._process_order(order)
    #     # order_id = self.browse(order_id)
    #     # for statement in order_id.statement_ids:
    #     #     if statement.journal_id.sat_payment_mode == '05' and statement.journal_id.pagamento_funcionarios:
    #     #         order_id.partner_id.credit_funcionario -= statement.amount
    #     #     elif statement.journal_id.sat_payment_mode == "05":
    #     #         order_id.partner_id.credit_limit -= statement.amount
    #     return order_id
    #
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
    #
    # @api.model
    # def retornar_order_by_id(self, order_id):
    #     order = self.browse(order_id)
    #
    #     dados_reimpressao = {
    #         'order_id': order_id,
    #         'chaveConsulta': order.chave_cfe,
    #         'doc_destinatario': order.partner_id.cnpj_cpf if order.partner_id
    #         else False,
    #         'xml_cfe_cacelada': order.cfe_cancelamento_return,
    #         'xml_cfe_venda': order.cfe_return,
    #         'canceled_order': order.canceled_order,
    #     }
    #
    #     return dados_reimpressao
    #
    # @api.one
    # def action_invoice(self):
    #     self.simplified = False
    #     self.fiscal_document_type = 'nfe'
    #
    # @api.multi
    # def simplified_limit_check(self):
    #     for order in self:
    #         if not order.simplified:
    #             continue
    #         limit = order.session_id.config_id.simplified_invoice_limit
    #         amount_total = order.amount_total
    #         precision_digits = dp.get_precision('Account')(self.env.cr)[1]
    #         # -1 or 0: amount_total <= limit, simplified
    #         #       1: amount_total > limit, can not be simplified
    #         simplified = (
    #             float_compare(amount_total, limit,
    #                           precision_digits=precision_digits) <= 0)
    #         # Change simplified flag if incompatible
    #         if not simplified:
    #             order.write(
    #                 {'simplified': simplified,
    #                  'fiscal_document_type':
    #                      order.session_id.config_id.simplified_invoice_type
    #                  })
