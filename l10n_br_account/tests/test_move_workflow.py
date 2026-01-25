# Copyright (C) 2025 Diego Paradeda - KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestMoveWorkflow(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.configure_normal_company_taxes()

        cls.move_out_venda = cls.init_invoice(
            "out_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=cls.empresa_lc_document_55_serie_1,
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[cls.env.ref("l10n_br_fiscal.fo_venda_venda")],
        )

        cls.env.ref("l10n_br_fiscal.fo_compras").deductible_taxes = True
        cls.move_in_compra_para_revenda = cls.init_invoice(
            "in_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_compras"),
            fiscal_operation_lines=[
                cls.env.ref("l10n_br_fiscal.fo_compras_compras_comercializacao")
            ],
            document_serie="1",
            document_number="42",
        )

    def test_change_states(self):
        document_id = self.move_out_venda.fiscal_document_id
        self.assertEqual(self.move_out_venda.state, "draft")
        self.assertEqual(document_id.state, "em_digitacao")
        self.move_out_venda.action_post()
        self.assertEqual(self.move_out_venda.state, "posted")
        fiscal_edi = self.env["ir.module.module"].search(
            [("name", "=", "l10n_br_fiscal_edi")]
        )
        if fiscal_edi and fiscal_edi.state == "installed":
            self.assertEqual(document_id.state, "a_enviar")
            self.move_out_venda.button_draft()
            self.assertEqual(self.move_out_venda.state, "draft")
            self.assertEqual(document_id.state, "em_digitacao")
            document_id.action_document_confirm()
            self.assertEqual(self.move_out_venda.state, "posted")
            self.assertEqual(document_id.state, "a_enviar")
            document_id.action_document_back2draft()
            self.assertEqual(self.move_out_venda.state, "draft")
            self.assertEqual(document_id.state, "em_digitacao")

    def test_document_deny(self):
        document_id = self.move_out_venda.fiscal_document_id
        self.assertEqual(self.move_out_venda.state, "draft")
        document_id.exec_after_SITUACAO_EDOC_DENEGADA("em_digitacao", "denegada")
        self.assertEqual(self.move_out_venda.state, "cancel")

    def test_in_invoice_confirm_from_fiscal_document(self):
        document_id = self.move_in_compra_para_revenda.fiscal_document_id
        self.assertEqual(self.move_in_compra_para_revenda.state, "draft")
        self.assertEqual(document_id.state, "em_digitacao")
        fiscal_edi = self.env["ir.module.module"].search(
            [("name", "=", "l10n_br_fiscal_edi")]
        )
        if fiscal_edi and fiscal_edi.state == "installed":
            self.assertEqual(document_id.issuer, "partner")
            document_id.action_document_confirm()
            self.assertEqual(document_id.state, "autorizada")
            self.assertEqual(self.move_in_compra_para_revenda.state, "posted")
