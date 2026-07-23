# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class StockValuationNetCostCase(TransactionCase):
    """Base comum (setup + helpers) para os testes de valorização pelo
    custo líquido — sem testes próprios."""

    @classmethod
    def _get_fiscal_operation_refs(cls):
        return ("l10n_br_fiscal.fo_compras", "l10n_br_fiscal.fo_compras_compras")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env.user.company_ids += cls.company
        cls.env.user.company_id = cls.company

        cls.product = cls.env.ref("product.product_product_6")
        cls.supplier_normal = cls.env.ref("l10n_br_base.res_partner_intel")
        cls.supplier_simples = cls.env.ref("l10n_br_base.res_partner_cliente2_sp")
        op_ref, op_line_ref = cls._get_fiscal_operation_refs()
        cls.fiscal_operation = cls.env.ref(op_ref)
        cls.fiscal_operation_line = cls.env.ref(op_line_ref)

        # Contas dedicadas para asserts limpos da ponte contábil.
        Account = cls.env["account.account"]
        cls.account_valuation = Account.create(
            {
                "name": "Estoque (teste valuation)",
                "code": "TSTVAL",
                "account_type": "asset_current",
                "company_id": cls.company.id,
            }
        )
        cls.account_stock_in = Account.create(
            {
                "name": "Ponte entrada estoque (teste)",
                "code": "TSTIN",
                "account_type": "asset_current",
                "company_id": cls.company.id,
            }
        )
        cls.account_stock_out = Account.create(
            {
                "name": "Ponte saída estoque (teste)",
                "code": "TSTOUT",
                "account_type": "asset_current",
                "company_id": cls.company.id,
            }
        )
        cls.stock_journal = cls.env["account.journal"].create(
            {
                "name": "Stock Journal (teste)",
                "code": "TSTJ",
                "type": "general",
                "company_id": cls.company.id,
            }
        )
        cls.categ = cls.product.categ_id
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )

    def _set_cost_method(self, cost_method):
        self.categ.with_company(self.company).write(
            {
                "property_valuation": "real_time",
                "property_cost_method": cost_method,
                "property_stock_account_input_categ_id": self.account_stock_in.id,
                "property_stock_account_output_categ_id": self.account_stock_out.id,
                "property_stock_valuation_account_id": self.account_valuation.id,
                "property_stock_journal": self.stock_journal.id,
            }
        )

    def _make_incoming(self, partner, price_unit=800.0, qty=1.0, fiscal=True):
        picking_vals = {
            "picking_type_id": self.warehouse.in_type_id.id,
            "location_id": self.env.ref("stock.stock_location_suppliers").id,
            "location_dest_id": self.warehouse.lot_stock_id.id,
            "partner_id": partner.id,
            "company_id": self.company.id,
        }
        move_vals = {
            "name": "entrada teste",
            "product_id": self.product.id,
            "product_uom": self.product.uom_id.id,
            "product_uom_qty": qty,
            "price_unit": price_unit,
            "company_id": self.company.id,
            "partner_id": partner.id,
        }
        if fiscal:
            picking_vals["fiscal_operation_id"] = self.fiscal_operation.id
            move_vals.update(
                {
                    "fiscal_operation_id": self.fiscal_operation.id,
                    "fiscal_operation_line_id": self.fiscal_operation_line.id,
                }
            )
        picking = self.env["stock.picking"].create(picking_vals)
        move_vals.update(
            {
                "picking_id": picking.id,
                "location_id": picking.location_id.id,
                "location_dest_id": picking.location_dest_id.id,
            }
        )
        move = self.env["stock.move"].create(move_vals)
        return picking, move

    def _receive(self, picking, qty_done=None):
        picking.action_confirm()
        picking.action_assign()
        for line in picking.move_ids.move_line_ids:
            line.qty_done = qty_done if qty_done is not None else line.reserved_uom_qty
        picking.with_context(skip_immediate=True, skip_backorder=True).with_user(
            self.env.user
        ).button_validate()


class TestStockValuationNetCost(StockValuationNetCostCase):
    """Valorização de entrada pelo custo líquido (Art. 301 RIR/2018, CPC 16).

    Cruzamento das três pontes, na mesma operação:

    * **fiscal** — a NF destaca ICMS embutido e IPI por fora
      (``icms_value``/``ipi_value`` na linha);
    * **custo/valorização** — o SVL entra pelo ``stock_cost_unit``
      (líquido dos créditos, somando não recuperáveis);
    * **contábil** — o lançamento do SVL (Db estoque / Cr conta ponte de
      entrada) é feito pelo MESMO líquido, deixando a ponte pronta para a
      fatura de fornecedor (que, com ``deductible_taxes``, debita a ponte
      pelo líquido e os créditos de impostos nas contas próprias) zerá-la.
    """

    def test_fifo_incoming_net_cost(self):
        """FIFO: SVL entra pelo custo líquido, não pelo preço bruto da NF."""
        self._set_cost_method("fifo")
        picking, move = self._make_incoming(self.supplier_normal)
        self._receive(picking)

        # Ponte 1 — fiscal: ICMS destacado (embutido) na linha.
        self.assertGreater(move.icms_value, 0, "ICMS deveria estar destacado")

        svl = move.stock_valuation_layer_ids
        self.assertEqual(len(svl), 1)
        # Ponte 2 — custo: SVL = custo líquido ≠ preço bruto.
        # Presumido industrial + industrialização: ICMS credita (subtrai),
        # IPI credita (não soma), PIS/COFINS cumulativos ficam embutidos.
        expected = move.price_unit - move.icms_value
        self.assertAlmostEqual(move.stock_cost_unit, expected, places=2)
        self.assertAlmostEqual(svl.unit_cost, move.stock_cost_unit, places=2)
        self.assertNotEqual(svl.unit_cost, move.price_unit)

        # Ponte 3 — contábil: Db estoque / Cr ponte de entrada pelo líquido.
        account_move = svl.account_move_id
        self.assertTrue(account_move, "SVL deveria gerar lançamento (real_time)")
        line_val = account_move.line_ids.filtered(
            lambda ln: ln.account_id == self.account_valuation
        )
        line_in = account_move.line_ids.filtered(
            lambda ln: ln.account_id == self.account_stock_in
        )
        self.assertAlmostEqual(line_val.debit, svl.value, places=2)
        self.assertAlmostEqual(line_in.credit, svl.value, places=2)
        # A ponte fica com o crédito EXATO que a fatura de fornecedor
        # (deductible_taxes) debita — os R$ do ICMS ficam fora do estoque,
        # na conta de crédito do imposto (sem dupla contagem).

    def test_avco_incoming_net_cost(self):
        """AVCO: custo médio do produto passa a ser o líquido."""
        self._set_cost_method("average")
        picking, move = self._make_incoming(self.supplier_normal)
        self._receive(picking)

        svl = move.stock_valuation_layer_ids
        self.assertAlmostEqual(svl.unit_cost, move.stock_cost_unit, places=2)
        self.assertAlmostEqual(
            self.product.with_company(self.company).standard_price,
            move.stock_cost_unit,
            places=2,
        )

    def test_supplier_simples_valuation(self):
        """Compra de fornecedor Simples: nada credita e o IPI soma —
        o SVL fica MAIOR que o preço da mercadoria."""
        self._set_cost_method("fifo")
        picking, move = self._make_incoming(self.supplier_simples)
        self._receive(picking)

        svl = move.stock_valuation_layer_ids
        expected = move.price_unit + move.ipi_value
        self.assertAlmostEqual(move.stock_cost_unit, expected, places=2)
        self.assertAlmostEqual(svl.unit_cost, expected, places=2)
        self.assertGreater(svl.unit_cost, move.price_unit)

    def test_partial_receipt_net_cost(self):
        """Receber 3 de 10: o SVL das 3 unidades usa o custo líquido
        unitário (o split preserva os campos fiscais)."""
        self._set_cost_method("fifo")
        picking, move = self._make_incoming(self.supplier_normal, qty=10.0)
        self._receive(picking, qty_done=3.0)

        done_move = picking.move_ids.filtered(lambda m: m.state == "done")
        svl = done_move.stock_valuation_layer_ids
        self.assertEqual(svl.quantity, 3.0)
        self.assertAlmostEqual(svl.value, 3.0 * done_move.stock_cost_unit, places=2)

    def test_invoice_price_unaffected(self):
        """O preço da fatura do picking continua sendo o price_unit
        (preço da NF), NÃO o custo líquido."""
        self._set_cost_method("fifo")
        picking, move = self._make_incoming(self.supplier_normal)
        self._receive(picking)

        invoice_price = move._get_price_unit_invoice("in_invoice", move.partner_id)
        self.assertAlmostEqual(invoice_price, move.price_unit, places=2)
        self.assertNotEqual(invoice_price, move.stock_cost_unit)

    def test_no_fiscal_operation_core_behavior(self):
        """Sem operação fiscal (caso não-Brasil), o SVL usa o preço bruto
        como no core."""
        self._set_cost_method("fifo")
        picking, move = self._make_incoming(self.supplier_normal, fiscal=False)
        self._receive(picking)

        svl = move.stock_valuation_layer_ids
        self.assertAlmostEqual(svl.unit_cost, move.price_unit, places=2)


class TestTransferValuation(StockValuationNetCostCase):
    """Fase G — transferências entre filiais (RF-G1/G2): o custo trafega
    LÍQUIDO. O ICMS destacado na NF de transferência gera crédito na filial
    destino (regime que credita) e NÃO infla o SVL; numa filial do Simples
    nada credita e o SVL fica pelo valor cheio. A operação de transferência
    não destaca IPI (IPI NT nas operation lines).

    Nota: o valor da alíquota interestadual na entrada depende da RFC do
    motor fiscal (ICMS interestadual em operações de entrada) — estes testes
    cobrem a mecânica de custo com o ICMS que o motor mapeia hoje."""

    @classmethod
    def _get_fiscal_operation_refs(cls):
        return (
            "l10n_br_fiscal.fo_transferencia_entrada",
            "l10n_br_fiscal.fo_transferencia_entrada_transferencia",
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Filial de origem: contribuinte normal (a NF de transferência
        # destaca ICMS).
        cls.branch_partner = cls.env.ref("l10n_br_base.lucro_presumido_partner")

    def test_transfer_in_net_cost(self):
        """Filial destino que credita: SVL = valor da NF − ICMS destacado
        (o custo trafega líquido); o ICMS vira crédito, não custo; sem IPI."""
        self._set_cost_method("fifo")
        picking, move = self._make_incoming(self.branch_partner)
        self._receive(picking)

        self.assertGreater(move.icms_value, 0)
        self.assertEqual(move.ipi_value, 0, "transferência não destaca IPI")
        tax_map = move._get_stock_cost_tax_map()
        self.assertEqual(tax_map.get("icms"), "credit")

        svl = move.stock_valuation_layer_ids
        self.assertAlmostEqual(
            svl.unit_cost, move.price_unit - move.icms_value, places=2
        )

    # O caso "filial destino no Simples Nacional (nada credita -> SVL cheio)"
    # é coberto em l10n_br_fiscal/tests/test_stock_cost.py (resolvedor) e no
    # teste unit do crédito CSOSN por comprador — o E2E correspondente depende
    # do refinamento CSOSN do PR da granularidade por CST.
