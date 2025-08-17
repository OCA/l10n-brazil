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
        states={"draft": [("readonly", False)]},
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain(),
    )

    # Adapt Mixin's fields
    fiscal_tax_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax",
        relation="fiscal_move_line_tax_rel",
        column1="document_id",
        column2="fiscal_tax_id",
        string="Fiscal Taxes",
    )

    quantity = fields.Float(
        related="product_uom_qty",
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

    ind_final = fields.Selection(related="picking_id.ind_final")

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
            result = self.product_id.with_company(self.company_id).standard_price

        return result

    @api.onchange("product_id")
    def _onchange_product_id_fiscal(self):
        # Metodo super altera o price_unit
        # TODO: Isso deveria ser resolvido no metodo principal?
        if self.picking_id.fiscal_operation_id:
            price_unit = self.price_unit
            result = super()._onchange_product_id_fiscal()
            # Valor informado pelo usuario tem prioridade
            if self.product_id and price_unit == 0.0:
                price_unit = self._get_price_unit()

            self.price_unit = price_unit

            return result

    def _split(self, qty, restrict_partner_id=False):
        new_moves_vals = super()._split(qty, restrict_partner_id)
        if not self.fiscal_operation_id:
            # Caso Brasil se caracteriza por ter Operação Fiscal
            return new_moves_vals

        self._onchange_fiscal_taxes()

        for new_move_vals in new_moves_vals:
            new_move_vals.update(self._prepare_br_fiscal_dict())

        return new_moves_vals

    @api.depends("price_unit")
    def _compute_fiscal_price(self):
        for record in self:
            record.fiscal_price = record.price_unit

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
