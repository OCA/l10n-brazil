# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

USER_TYPE_MAP = {
    ("outgoing", "customer"): ["sale"],
    ("outgoing", "supplier"): ["purchase"],
    ("outgoing", "transit"): ["sale", "purchase"],
    ("incoming", "supplier"): ["purchase"],
    ("incoming", "customer"): ["sale"],
    ("incoming", "transit"): ["purchase", "sale"],
}


class StockMove(models.Model):
    _name = "stock.move"
    _inherit = [_name, "l10n_br_fiscal.document.line.mixin"]

    @api.model
    def _default_fiscal_operation(self):
        return False

    @api.model
    def _fiscal_operation_domain(self):
        # TODO Check in context to define in or out move default.
        domain = [("state", "=", "approved")]
        return domain

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        readonly=True,
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain(),
    )

    # Adapt Mixin's fields
    fiscal_tax_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax",
        string="Fiscal Taxes",
        precompute=False,
    )

    uom_id = fields.Many2one(
        related="product_uom",
    )

    tax_framework = fields.Selection(
        related="picking_id.company_id.tax_framework",
        string="Tax Framework",
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="stock_move_line_comment_rel",
        column1="stock_move_id",
        column2="comment_id",
        string="Comments",
    )

    # O price_unit fica negativo por metodos do core
    # durante o processo chamado pelo botão Validate p/
    # valorização de estoque, sem o compute o valor permance positivo.
    # A Fatura é criada com os dois valores positivos.
    fiscal_price = fields.Float(compute="_compute_fiscal_price")

    # Usado para tornar Somente Leitura os campos totais dos custos
    # de entrega quando a definição for por Linha
    delivery_costs = fields.Selection(
        related="company_id.delivery_costs",
    )

    tax_ids = fields.Many2many(
        comodel_name="account.tax",
        string="Taxes",
        check_company=True,
        help="Taxes that apply on the base amount",
        compute="_compute_tax_ids",
        store=True,
    )

    # adapted for _compute_find_final:
    def _get_document(self):
        self.ensure_one()
        return self.picking_id

    @api.depends("fiscal_tax_ids", "fiscal_operation_line_id")
    def _compute_tax_ids(self):
        for record in self:
            # TODO: Ver na v16 ou posterior se é possível fazer esse
            #  mapeamento do user_type no stock_picking_invoicing
            #  para reduzir metodos duplicados
            if record.product_id and record.fiscal_operation_line_id:
                pick_type_code = record.picking_id.picking_type_id.code
                if pick_type_code == "incoming":
                    usage = record.location_id.usage
                else:
                    usage = record.location_dest_id.usage
                user_type = USER_TYPE_MAP.get((pick_type_code, usage))

                if user_type:
                    # Necessario usar o with_company porque sem isso, pelo menos,
                    # no caso dos Dados de Demonstração são criados sem o Tax IDs
                    # porque a empresa do self.env.company vai errado
                    tax_ids = self.fiscal_tax_ids.with_company(
                        record.company_id
                    ).account_taxes(
                        user_type=user_type[0],
                        fiscal_operation=record.fiscal_operation_id,
                        company=record.company_id,
                    )

                    if tax_ids:
                        record.tax_ids = tax_ids

    @api.model
    def _add_precomputed_values(self, vals_list):
        # Skip fiscal_tax_ids precompute for stock.move to avoid FK constraint
        # on the m2m relation table during creation. The taxes will be
        # computed later via _compute_fiscal_tax_ids when the record exists.
        for vals in vals_list:
            vals.pop("fiscal_tax_ids", None)
        return super()._add_precomputed_values(vals_list)

    @api.model
    def _setup_base(self):
        res = super()._setup_base()
        # The l10n_br_fiscal.document.line.mixin fields are precomputed by
        # default, but stock.move depends on non-precomputed fields like
        # partner_id and quantity. All those precomputed computed fields must
        # be disabled to avoid the Odoo 18 warnings during registry setup.
        mixin_classes = [
            klass
            for klass in self._model_classes__
            if getattr(klass, "_name", None) == "l10n_br_fiscal.document.line.mixin"
        ]
        if not mixin_classes:
            return res
        mixin_class = mixin_classes[0]
        mixin_names = {field.name for field in mixin_class._field_definitions}
        for name in mixin_names:
            field = self._fields.get(name)
            if field is None or not field.precompute:
                continue
            if field.related:
                # Related fields are safe to disable and may otherwise warn
                # when their related path crosses non-precomputed fields.
                field.precompute = False
                continue
            if not field.compute:
                continue
            # Look at the mixin method, not the stock.move override: the
            # override may not repeat @api.depends, but the original field
            # definition still declares dependencies that drive precompute.
            compute = getattr(mixin_class, field.compute, None)
            if compute is None:
                continue
            func = getattr(compute, "__func__", compute)
            if not getattr(func, "_depends", None):
                # Compute methods without explicit @api.depends rely on
                # precompute to get their initial value (e.g. ind_final).
                # Keep precompute enabled for them.
                continue
            field.precompute = False
        return res

    @api.model_create_multi
    def create(self, vals_list):
        return super(
            StockMove, self.with_context(skip_compute_fiscal_tax_ids=True)
        ).create(vals_list)

    def _compute_fiscal_tax_ids(self):
        # Skip during creation/precompute when record is not yet in DB.
        # In Odoo 18, precompute runs during create before flush, causing
        # the m2m insert to fail with FK constraint.
        # Check if records exist in DB before writing to m2m relation.
        if self.ids:
            self.env.cr.execute(
                "SELECT id FROM stock_move WHERE id IN %s", (tuple(self.ids),)
            )
            existing_ids = {r[0] for r in self.env.cr.fetchall()}
            if not existing_ids:
                # All records are new (not yet flushed) - skip
                return
        return super()._compute_fiscal_tax_ids()

    @api.onchange("product_id", "fiscal_operation_id", "price_unit")
    def _onchange_product_quantity(self):
        """No Brasil o caso de Ordens de Entrega com Operação Fiscal
        de Saída precisam informar o Preço de Custo e não o de Venda
        ex.: Simples Remessa, Remessa p/ Industrialiazação e etc."""
        if (
            self.fiscal_operation_id.fiscal_operation_type == "out"
            and self.price_unit == 0.0
        ):
            self.price_unit = self.product_id.with_company(
                self.company_id
            ).standard_price

    def _get_new_picking_values(self):
        """Prepares a new picking for this move as it could not be assigned to
        another picking. This method is designed to be inherited."""
        result = super()._get_new_picking_values()
        # O self pode conter mais de uma stock.move, com os modulos
        # l10n_br_sale_stock e l10n_br_purchase_stock instalados o self pode vir
        # com mais de uma Operação Fiscal, nesses outros modulos é feita a
        # alteração para usar a Operação Fiscal principal, isso é a do
        # cabeçalho do Pedido
        fiscal_operations = self.mapped("fiscal_operation_id")
        if fiscal_operations:
            result.update({"fiscal_operation_id": fiscal_operations[0].id})
        # A mesma questão do self, aqui se uma linha for
        # 2binvoiced o Picking também será
        result.update({"invoice_state": self.mapped("invoice_state")[0]})
        return result

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super()._prepare_merge_moves_distinct_fields()
        distinct_fields += ["fiscal_operation_id", "fiscal_operation_line_id"]
        return distinct_fields

    @api.model
    def _prepare_merge_move_sort_method(self, move):
        move.ensure_one()
        keys_sorted = super()._prepare_merge_move_sort_method(move)
        keys_sorted += [move.fiscal_operation_id.id, move.fiscal_operation_line_id.id]
        return keys_sorted

    def _prepare_extra_move_vals(self, qty):
        values = {}
        if self.fiscal_operation_id:
            # Caso Brasil se caracteriza por ter Operação Fiscal
            values = self._prepare_br_fiscal_dict()
        values.update(super()._prepare_extra_move_vals(qty))
        return values

    def _prepare_move_split_vals(self, uom_qty):
        values = {}
        if self.fiscal_operation_id:
            # Caso Brasil se caracteriza por ter Operação Fiscal
            values = self._prepare_br_fiscal_dict()
        values.update(super()._prepare_move_split_vals(uom_qty))
        return values

    def _get_price_unit_invoice(self, inv_type, partner, qty=1):
        result = super()._get_price_unit_invoice(inv_type, partner, qty)
        if not self.fiscal_operation_id:
            # Caso não tenha a Operação Fiscal não é uma Fatura do Brasil
            return result

        product = self.mapped("product_id")
        product.ensure_one()

        # No Brasil o caso de Ordens de Entrega com Operação Fiscal
        # de Saída precisam informar o Preço de Custo e não o de Venda
        # ex.: Simples Remessa, Remessa p/ Industrialiazação e etc.
        # Mas o valor informado pelo usuário tem prioridade
        price_unit = self.mapped("price_unit")[0]
        if inv_type in ("out_invoice", "out_refund") and price_unit == 0.0:
            result = product.with_company(self.company_id).standard_price
        else:
            # Caso do Valor Informado pelo usuário tem prioridade
            result = price_unit

        return result

    def _get_price_unit(self):
        """Returns the unit price to store on the quant"""
        result = super()._get_price_unit()
        if not self.fiscal_operation_id:
            # Caso não tenha a Operação Fiscal não é uma caso do Brasil
            return result

        # No Brasil o caso de Ordens de Entrega com Operação Fiscal
        # de Saída precisam informar o Preço de Custo e não o de Venda
        # ex.: Simples Remessa, Remessa p/ Industrialiazação e etc.
        # TODO: Deve ser o valor informado pelo usuário ou no
        #  Quant deve ser registrado o preço padrão como era feito antes
        #  e continua sendo feito abaixo?
        if self.fiscal_operation_id.fiscal_operation_type == "out":
            result = {
                self.env["stock.lot"]: self.product_id.with_company(
                    self.company_id
                ).standard_price
            }

        return result

    def _split(self, qty, restrict_partner_id=False):
        new_moves_vals = super()._split(qty, restrict_partner_id)
        if not self.fiscal_operation_id:
            # Caso Brasil se caracteriza por ter Operação Fiscal
            return new_moves_vals

        for new_move_vals in new_moves_vals:
            new_move_vals.update(self._prepare_br_fiscal_dict())

        return new_moves_vals

    @api.depends("price_unit")
    def _compute_fiscal_price(self):
        for record in self:
            record.fiscal_price = record.price_unit

    @api.depends("product_id", "state")
    def _compute_product_fiscal_fields(self):
        # Skip compute for "done" records
        moves = self.filtered(lambda m: m.state != "done")
        return super(StockMove, moves)._compute_product_fiscal_fields()

    def _get_taxes(self, fiscal_position, inv_type):
        """
        Map product taxes based on given fiscal position
        :param fiscal_position: account.fiscal.position recordset
        :param inv_type: string
        :return: account.tax recordset
        """
        taxes = super()._get_taxes(fiscal_position, inv_type)
        if self.fiscal_operation_line_id:
            # Caso Brasil
            taxes = self.tax_ids

        return taxes

    def _get_document(self):
        """Override to return picking as the fiscal document."""
        self.ensure_one()
        return self.picking_id

    def _get_fiscal_partner(self):
        """
        Adjust the partner, both for an invoice from picking with
        no related SO or PO,
        https://github.com/OCA/account-invoicing/blob/14.0/
        stock_picking_invoicing/models/stock_picking.py#L38
        and also in the case of a picking originating from a PO:
        https://github.com/OCA/OCB/blob/14.0/addons/purchase/
        models/purchase.py#L556
        """
        self.ensure_one()
        partner = super()._get_fiscal_partner()
        if partner.id != partner.address_get(["invoice"]).get("invoice"):
            partner = self.env["res.partner"].browse(
                partner.address_get(["invoice"]).get("invoice")
            )

        return partner
