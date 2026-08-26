# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Gerador dos ciclos de demonstracao de creditabilidade.

Cada ciclo e uma compra completa e **confirmada**: pedido, recebimento, fatura
e confirmacao. Ficam gravados na base para inspecao na tela, ao contrario da
suite de testes, que roda em `TransactionCase` e reverte tudo.

Os cenarios existem para tornar visivel a **creditabilidade condicional**: o
mesmo produto, pelo mesmo preco, do mesmo fornecedor, deve valer coisas
diferentes no estoque conforme a operacao permita ou nao o credito do imposto.
"""

import logging

from odoo import _, api, fields, models
from odoo.tests import Form

_logger = logging.getLogger(__name__)

CATEGORY_NAME = "Demo Creditabilidade (AVCO / Automated)"
PRICE = 100.0

ACCOUNT_BRIDGE = "1.1.9.0.01"
ACCOUNT_STOCK = "1.1.3.1.02"
ACCOUNT_COGS = "5.1.1.1.01"
PREFIX_RECOVERABLE = "1.1.4.1."
ACCOUNT_ICMS = "1.1.4.1.02"

SIMPLES_FRAMEWORKS = ("1", "4")


class CreditabilityDemo(models.AbstractModel):
    _name = "l10n_br.creditability.demo"
    _description = "Gerador dos ciclos de demonstracao de creditabilidade"

    # ------------------------------------------------------------------
    # Ambiente
    # ------------------------------------------------------------------

    @api.model
    def _demo_company(self):
        company = self.env.ref(
            "l10n_br_base.empresa_lucro_presumido", raise_if_not_found=False
        )
        if not company:
            _logger.warning(
                "Demo de creditabilidade ignorada: a empresa "
                "l10n_br_base.empresa_lucro_presumido nao existe nesta base."
            )
        return company

    @api.model
    def _demo_account(self, company, code):
        return self.env["account.account"].search(
            [("code", "=", code), ("company_id", "=", company.id)], limit=1
        )

    @api.model
    def _demo_supplier(self):
        """Fornecedor do regime normal.

        Um fornecedor do Simples Nacional nao transfere credito de ICMS
        (LC 123/2006, art. 23) - so o destacado sob CSOSN 101/201. Medir
        creditabilidade contra ele daria uma baseline errada.
        """
        supplier = self.env.ref(
            "l10n_br_base.res_partner_intel", raise_if_not_found=False
        )
        if supplier and supplier.tax_framework in SIMPLES_FRAMEWORKS:
            _logger.warning(
                "Demo de creditabilidade ignorada: o fornecedor %s e do "
                "Simples Nacional.",
                supplier.display_name,
            )
            return self.env["res.partner"]
        return supplier

    @api.model
    def _demo_product(self, company, code, label):
        """Produto em categoria AVCO com avaliacao automatica.

        A localizacao nao entrega nenhuma categoria assim, e sem ela o ajuste
        de diferenca de preco da fatura nem chega a rodar.
        """
        product = self.env["product.product"].search(
            [("default_code", "=", code)], limit=1
        )
        if product:
            return product

        bridge = self._demo_account(company, ACCOUNT_BRIDGE)
        stock = self._demo_account(company, ACCOUNT_STOCK)
        cogs = self._demo_account(company, ACCOUNT_COGS)
        journal = self.env["account.journal"].search(
            [("code", "=", "STJ"), ("company_id", "=", company.id)], limit=1
        ) or self.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", company.id)], limit=1
        )
        if not (bridge and stock and cogs and journal):
            _logger.warning(
                "Demo de creditabilidade ignorada: faltam contas ou diario de "
                "estoque na empresa %s. Esperado o plano l10n_br_coa_generic.",
                company.display_name,
            )
            return self.env["product.product"]

        category = self.env["product.category"].search(
            [("name", "=", CATEGORY_NAME)], limit=1
        ) or self.env["product.category"].with_company(company).create(
            {
                "name": CATEGORY_NAME,
                "property_cost_method": "average",
                "property_valuation": "real_time",
                "property_stock_account_input_categ_id": bridge.id,
                "property_stock_account_output_categ_id": bridge.id,
                "property_stock_valuation_account_id": stock.id,
                "property_account_expense_categ_id": cogs.id,
                "property_stock_journal": journal.id,
            }
        )
        return (
            self.env.ref("product.product_product_12")
            .with_company(company)
            .copy(
                {
                    "name": label,
                    "default_code": code,
                    "categ_id": category.id,
                    "detailed_type": "product",
                    "purchase_ok": True,
                    "standard_price": 0.0,
                    "seller_ids": [(5, 0, 0)],
                }
            )
        )

    # ------------------------------------------------------------------
    # Medidas
    # ------------------------------------------------------------------

    @api.model
    def _demo_balances(self, company, product):
        self.env.flush_all()

        def total(accounts):
            lines = self.env["account.move.line"].search(
                [
                    ("account_id", "in", accounts.ids),
                    ("parent_state", "=", "posted"),
                    ("company_id", "=", company.id),
                ]
            )
            return round(sum(lines.mapped("balance")), 2)

        recoverable = self.env["account.account"].search(
            [
                ("code", "=like", PREFIX_RECOVERABLE + "%"),
                ("company_id", "=", company.id),
            ]
        )
        layers = self.env["stock.valuation.layer"].search(
            [("product_id", "=", product.id)]
        )
        return {
            "ponte": total(self._demo_account(company, ACCOUNT_BRIDGE)),
            "estoque": total(self._demo_account(company, ACCOUNT_STOCK)),
            "cmv": total(self._demo_account(company, ACCOUNT_COGS)),
            "a compensar": total(recoverable),
            "icms": total(self._demo_account(company, ACCOUNT_ICMS)),
            "svl": round(sum(layers.mapped("value")), 2),
        }

    # ------------------------------------------------------------------
    # Ciclo
    # ------------------------------------------------------------------

    @api.model
    def _generate_cycle(
        self,
        operation_line_xmlid,
        reference,
        product_code,
        product_label,
        deductible_taxes=False,
        price=PRICE,
    ):
        """Pedido, recebimento, fatura e confirmacao, gravados na base.

        `deductible_taxes` e uma configuracao da operacao fiscal, compartilhada
        por toda a base. O valor anterior e **restaurado no fim**, para a demo
        nao deixar a operacao Compras num estado que o proximo teste nao espera.
        """
        company = self._demo_company()
        supplier = self._demo_supplier()
        if not (company and supplier):
            return self.env["account.move"]

        existing = self.env["account.move"].search(
            [("ref", "=", reference), ("company_id", "=", company.id)], limit=1
        )
        if existing:
            _logger.info("Ciclo de demo %s ja existe (%s).", reference, existing.name)
            return existing

        product = self._demo_product(company, product_code, product_label)
        operation = self.env.ref("l10n_br_fiscal.fo_compras")
        operation_line = self.env.ref(operation_line_xmlid, raise_if_not_found=False)
        if not (product and operation_line):
            return self.env["account.move"]

        env = self.env(
            user=self.env.ref("base.user_admin"),
            context=dict(self.env.context, allowed_company_ids=[company.id]),
        )
        scoped_operation = operation.with_company(company)
        previous = scoped_operation.deductible_taxes
        scoped_operation.deductible_taxes = deductible_taxes
        try:
            before = self.with_env(env)._demo_balances(company, product)

            order_form = Form(env["purchase.order"].with_company(company))
            order_form.partner_id = supplier
            order_form.fiscal_operation_id = operation
            with order_form.order_line.new() as line:
                line.product_id = product
                line.fiscal_operation_line_id = operation_line
                line.product_qty = 1.0
                line.price_unit = price
            order = order_form.save()
            order.button_confirm()

            picking = order.picking_ids
            picking.action_confirm()
            picking.action_assign()
            for move in picking.move_ids_without_package:
                move.quantity_done = move.product_uom_qty
            picking.button_validate()

            order.action_create_invoice()
            bill = order.invoice_ids
            bill.invoice_date = fields.Date.context_today(bill)
            bill.ref = reference
            bill.action_post()

            after = self.with_env(env)._demo_balances(company, product)
        finally:
            # Devolve a operacao ao estado anterior: a flag e compartilhada
            scoped_operation.deductible_taxes = previous

        _logger.info(
            "[demo creditabilidade] %s | %s | cfop %s | dedutiveis %s | "
            "ponte %+.2f | estoque %+.2f | a compensar %+.2f | icms %+.2f | "
            "camada %+.2f",
            reference,
            bill.name,
            operation_line.cfop_internal_id.code,
            "ON" if deductible_taxes else "OFF",
            after["ponte"] - before["ponte"],
            after["estoque"] - before["estoque"],
            after["a compensar"] - before["a compensar"],
            after["icms"] - before["icms"],
            after["svl"] - before["svl"],
        )
        return bill

    # ------------------------------------------------------------------
    # Cenarios
    # ------------------------------------------------------------------

    OPERATION_RESALE = "l10n_br_fiscal.fo_compras_compras_comercializacao"
    OPERATION_OWN_USE = "l10n_br_fiscal.fo_compras_compras_uso_consumo"

    @api.model
    def generate_case_1a(self):
        """CFOP 1102 revenda, dedutiveis OFF.

        O ICMS destacado gera credito, abatido do ICMS devido na saida
        (LC 87/96, art. 20). O imposto nunca foi custo: e ativo a recuperar.
        O estoque deveria valer o preco menos o ICMS.
        """
        return self._generate_cycle(
            self.OPERATION_RESALE,
            "CASO 1A - CFOP 1102 revenda - dedutiveis OFF",
            "DEMO-1A",
            _("Demo 1A - revenda, dedutiveis OFF"),
            deductible_taxes=False,
        )

    @api.model
    def generate_case_1b(self):
        """CFOP 1102 revenda, dedutiveis ON. Mesmos saldos do 1A."""
        return self._generate_cycle(
            self.OPERATION_RESALE,
            "CASO 1B - CFOP 1102 revenda - dedutiveis ON",
            "DEMO-1B",
            _("Demo 1B - revenda, dedutiveis ON"),
            deductible_taxes=True,
        )

    @api.model
    def generate_case_2a(self):
        """CFOP 1556 uso e consumo, dedutiveis OFF.

        Quem compra para consumo proprio e consumidor final: nao havera saida
        tributada onde abater. O credito de ICMS sobre material de uso e
        consumo segue vedado ate 2033 (LC 87/96, art. 33, I, na redacao da
        LC 171/2019). O imposto e custo e o estoque deveria valer o preco
        cheio - mais que no caso 1A, exatamente pelo ICMS.
        """
        return self._generate_cycle(
            self.OPERATION_OWN_USE,
            "CASO 2A - CFOP 1556 uso e consumo - dedutiveis OFF",
            "DEMO-2A",
            _("Demo 2A - uso e consumo, dedutiveis OFF"),
            deductible_taxes=False,
        )

    @api.model
    def generate_case_2b(self):
        """CFOP 1556 uso e consumo, dedutiveis ON. Mesmos saldos do 2A."""
        return self._generate_cycle(
            self.OPERATION_OWN_USE,
            "CASO 2B - CFOP 1556 uso e consumo - dedutiveis ON",
            "DEMO-2B",
            _("Demo 2B - uso e consumo, dedutiveis ON"),
            deductible_taxes=True,
        )
