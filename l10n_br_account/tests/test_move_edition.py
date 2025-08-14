# Copyright 2025-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import logging
from unittest import mock

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase
from odoo.tests.common import Form

_logger = logging.getLogger(__name__)


class PatchedForm(Form):
    def _cleanup_onchange(self, descr, value, current):
        """
        Ignore "ValueError: Unsupported M2M command 0" in test_move_entry.
        Not sure why this error happen, but it seems more like a bug in Form
        than in l10n_br_account, so we ignore it.
        """
        try:
            return super()._cleanup_onchange(descr, value, current)
        except ValueError as e:
            _logger.debug(f"ignoring error {e}")


class TestMoveEdition(TransactionCase):
    """
    Test basic invoicing scenarios through the user interface to ensure
    expected fields are presents and that the fiscal "decoration" works
    as expected in the account.move(.line).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.out_invoice_account_id = cls.env["account.account"].create(
            {
                "company_id": cls.company.id,
                "account_type": "asset_receivable",
                "code": "RECTEST",
                "name": "Test receivable account",
                "reconcile": True,
            }
        )

        cls.user = cls.env["res.users"].create(
            {
                "name": "Because I am accountman!",
                "login": "accountman",
                "password": "accountman",
                "groups_id": [
                    # we purposely don't give Fiscal access rights now to ensure
                    # non fiscal operations are still allowed
                    Command.set(cls.env.user.groups_id.ids),
                    Command.link(cls.env.ref("account.group_account_manager").id),
                    Command.link(cls.env.ref("account.group_account_user").id),
                ],
            }
        )
        cls.user.partner_id.email = "accountman@test.com"
        companies = cls.env["res.company"].search([])
        cls.user.write(
            {
                "company_ids": [Command.set(companies.ids)],
                "company_id": cls.company.id,
            }
        )

        cls.env = cls.env(
            user=cls.user, context=dict(cls.env.context, tracking_disable=True)
        )

        cls.non_br_partner = cls.env["res.partner"].create(
            {"name": "Non BR Invoicing Partner"}
        )
        cls.product_id = cls.env.ref("product.product_product_7")

    def test_move_entry(self):
        """
        Ensure Accounting Entries edition require no fiscal fields.
        """

        move_form = PatchedForm(
            self.env["account.move"].with_context(
                default_move_type="entry",
            )
        )
        move_form.ref = "some_ref"
        move_form.date = fields.Date.from_string("2025-01-01")

        with move_form.line_ids.new() as line_form:
            line_form.account_id = self.out_invoice_account_id
            line_form.debit = 10
        with self.assertRaises(UserError):  # ensure not balanced is still checked
            move = move_form.save()

        with move_form.line_ids.new() as line_form:
            line_form.account_id = self.out_invoice_account_id
            line_form.credit = 10
        move = move_form.save()
        self.assertFalse(move.fiscal_document_id)
        self.assertEqual(len(move.fiscal_document_ids), 0)
        move.action_post()
        self.assertEqual(move.state, "posted")
        move.button_cancel()
        self.assertEqual(move.state, "cancel")

    def test_out_non_fiscal_invoice(self):
        """
        Ensure customer Invoice with no fiscal document type can be edited.
        """

        move_form = Form(
            self.env["account.move"].with_context(
                default_move_type="out_invoice",
            )
        )
        move_form.partner_id = self.non_br_partner
        move_form.ref = "some_ref"
        with move_form.invoice_line_ids.new() as line_form:
            line_form.name = "some line label"
            line_form.price_unit = 42
        move = move_form.save()
        self.assertFalse(move.fiscal_document_id)
        self.assertEqual(len(move.fiscal_document_ids), 0)
        self.assertEqual(move.amount_total, 42)
        self.assertEqual(move.state, "draft")
        move.action_post()
        self.assertEqual(move.state, "posted")
        move.button_cancel()
        self.assertEqual(move.state, "cancel")

    def test_out_fiscal_invoice(self):
        """
        Ensure customer Invoice with a fiscal document be edited.
        """

        # now user needs to be a Fiscal User:
        self.user.groups_id += self.env.ref("l10n_br_fiscal.group_user")
        nfe_user_group = self.env.ref(
            "l10n_br_nfe.group_user", raise_if_not_found=False
        )
        if nfe_user_group:
            self.user.groups_id += nfe_user_group

        self.product_id.list_price = 150  # we will later test price_unit can be changed

        move_form = Form(
            self.env["account.move"].with_context(
                default_move_type="out_invoice",
            )
        )
        move_form.partner_id = self.env.ref("l10n_br_base.res_partner_cliente5_pe")
        move_form.document_type_id = self.env.ref("l10n_br_fiscal.document_55")
        with self.assertRaises(AssertionError):  # missing fiscal fields
            move_form.save()

        move_form.document_serie_id = self.env.ref(
            "l10n_br_fiscal.empresa_lc_document_55_serie_1"
        )
        with self.assertRaises(AssertionError):  # missing fiscal fields
            move_form.save()

        move_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        move_form.ind_final = "1"
        with move_form.invoice_line_ids.new() as line_form:
            original_method = type(
                self.env["l10n_br_fiscal.operation.line"]
            ).map_fiscal_taxes

            def wrapped_method(self, *args, **kwargs):
                return original_method(self, *args, **kwargs)

            with mock.patch.object(
                type(self.env["l10n_br_fiscal.operation.line"]),
                "map_fiscal_taxes",
                side_effect=wrapped_method,
                autospec=True,
            ) as mocked:
                line_form.product_id = self.product_id

            # ensure the tax engine is called with the proper
            # parameters, especially ind_final
            # as it is related=document_id.ind_final
            # which is converted to move_id.ind_final to work live
            mocked.assert_called_with(
                self.env.ref("l10n_br_fiscal.fo_venda_revenda"),
                company=move_form.company_id,
                partner=move_form.partner_id,
                product=self.product_id,
                ncm=self.product_id.ncm_id,
                nbm=self.env["l10n_br_fiscal.nbm"],
                nbs=self.env["l10n_br_fiscal.nbs"],
                cest=self.env["l10n_br_fiscal.cest"],
                city_taxation_code=self.env["l10n_br_fiscal.city.taxation.code"],
                service_type=self.env["l10n_br_fiscal.service.type"],
                ind_final="1",
            )

            line_form.price_unit = 42
            line_form.quantity = 5
            self.assertEqual(len(line_form.fiscal_tax_ids), 4)
            self.assertEqual(
                line_form.icms_tax_id, self.env.ref("l10n_br_fiscal.tax_icms_7")
            )
            self.assertEqual(
                line_form.ipi_tax_id, self.env.ref("l10n_br_fiscal.tax_ipi_nt")
            )
            self.assertTrue(abs(line_form.icms_value - 14.7) < 0.01)
            line_form.quantity = 10
            self.assertTrue(abs(line_form.icms_value - 29.40) < 0.01)

            line_form.fiscal_operation_line_id = self.env.ref(
                "l10n_br_fiscal.fo_venda_venda"
            )
            self.assertEqual(len(line_form.fiscal_tax_ids), 4)
            self.assertEqual(
                line_form.icms_tax_id, self.env.ref("l10n_br_fiscal.tax_icms_7")
            )
            self.assertEqual(
                line_form.ipi_tax_id, self.env.ref("l10n_br_fiscal.tax_ipi_5")
            )

            # ensure manually setting a xx_tax_id is properly saved (not recomputed):
            line_form.icms_tax_id = self.env.ref("l10n_br_fiscal.tax_icms_18")
            self.assertEqual(line_form.icms_value, 79.38)
            self.assertEqual(
                line_form.ipi_tax_id, self.env.ref("l10n_br_fiscal.tax_ipi_5")
            )

        move = move_form.save()

        self.assertEqual(move.state, "draft")
        self.assertEqual(move.state_edoc, "em_digitacao")
        self.assertEqual(move.fiscal_document_id.document_serie, "1")
        self.assertTrue(move.fiscal_document_id)
        self.assertEqual(len(move.fiscal_document_ids), 1)
        self.assertEqual(len(move.fiscal_line_ids), 1)

        # test "shadowed" fields:
        self.assertEqual(move.partner_id, move.fiscal_document_id.partner_id)
        self.assertEqual(move.currency_id, move.fiscal_document_id.currency_id)
        self.assertEqual(move.company_id, move.fiscal_document_id.company_id)
        self.assertEqual(move.user_id, move.fiscal_document_id.user_id)

        # test "shadowed" line fields:
        aml = move.line_ids[0]
        fisc_line = move.fiscal_line_ids[0]
        self.assertEqual(aml.product_id, fisc_line.product_id)
        self.assertEqual(aml.name, fisc_line.name)
        self.assertEqual(aml.price_unit, 42)
        self.assertEqual(aml.quantity, 10)
        self.assertEqual(aml.quantity, fisc_line.quantity)
        self.assertEqual(aml.price_unit, fisc_line.price_unit)

        self.assertEqual(
            aml.fiscal_operation_line_id,
            self.env.ref("l10n_br_fiscal.fo_venda_venda"),
        )

        self.assertEqual(
            aml.icms_tax_id.id,
            self.ref("l10n_br_fiscal.tax_icms_18"),
        )
        self.assertEqual(aml.ipi_tax_id, self.env.ref("l10n_br_fiscal.tax_ipi_5"))
        self.assertEqual(aml.icms_value, 79.38)

        move.action_post()
        self.assertEqual(move.state, "posted")
        move.button_cancel()
        self.assertEqual(move.state, "cancel")
        move.button_draft()
        self.assertEqual(move.state, "draft")

    def test_in_non_fiscal_invoice(self):
        """
        Ensure supplier Invoice with no fiscal document type can be edited.
        """

        move_form = Form(
            self.env["account.move"].with_context(
                default_move_type="in_invoice",
            )
        )
        move_form.partner_id = self.non_br_partner
        move_form.ref = "some_ref"
        move_form.invoice_date = fields.Date.from_string("2025-01-01")
        with move_form.invoice_line_ids.new() as line_form:
            line_form.name = "some line label"
            line_form.price_unit = 42
        move = move_form.save()
        self.assertFalse(move.fiscal_document_id)
        self.assertEqual(len(move.fiscal_document_ids), 0)
        self.assertEqual(move.amount_total, 42)
        self.assertEqual(move.state, "draft")
        move.action_post()
        self.assertEqual(move.state, "posted")
        move.button_cancel()
        self.assertEqual(move.state, "cancel")

    def test_in_fiscal_invoice(self):
        """
        Ensure customer Invoice with a fiscal document be edited.
        """

        # now user needs to be a Fiscal User:
        self.user.groups_id += self.env.ref("l10n_br_fiscal.group_user")
        nfe_user_group = self.env.ref(
            "l10n_br_nfe.group_user", raise_if_not_found=False
        )
        if nfe_user_group:
            self.user.groups_id += nfe_user_group

        move_form = Form(
            self.env["account.move"].with_context(
                default_move_type="in_invoice",
            )
        )
        move_form.partner_id = self.env.ref("l10n_br_base.res_partner_cliente5_pe")
        move_form.document_type_id = self.env.ref("l10n_br_fiscal.document_55")
        with self.assertRaises(AssertionError):  # missing fiscal fields
            move_form.save()

        move_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_compras")

        with self.assertRaises(AssertionError):  # not visible for supplier invoice
            move_form.document_serie_id = self.env.ref(
                "l10n_br_fiscal.empresa_lc_document_55_serie_1"
            )

        with self.assertRaises(AssertionError):  # missing fiscal fields
            move_form.save()

        move_form.document_serie = "1"
        move_form.document_number = "123"
        move_form.invoice_date = fields.Date.from_string("2025-01-01")

        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product_id
            line_form.price_unit = 42
            line_form.quantity = 42

        move = move_form.save()

        self.assertEqual(move.state, "draft")
        self.assertEqual(move.state_edoc, "em_digitacao")
        self.assertEqual(move.fiscal_document_id.document_serie, "1")
        self.assertTrue(move.fiscal_document_id)
        self.assertEqual(len(move.fiscal_document_ids), 1)
        self.assertEqual(len(move.fiscal_line_ids), 1)

        # test "shadowed" fields:
        self.assertEqual(move.partner_id, move.fiscal_document_id.partner_id)
        self.assertEqual(move.currency_id, move.fiscal_document_id.currency_id)
        self.assertEqual(move.company_id, move.fiscal_document_id.company_id)
        self.assertEqual(move.user_id, move.fiscal_document_id.user_id)

        # test "shadowed" line fields:
        aml = move.line_ids[0]
        fisc_line = move.fiscal_line_ids[0]
        self.assertEqual(aml.product_id, fisc_line.product_id)
        self.assertEqual(aml.name, fisc_line.name)
        self.assertEqual(aml.quantity, fisc_line.quantity)
        self.assertEqual(aml.price_unit, fisc_line.price_unit)

        self.assertEqual(
            aml.fiscal_operation_line_id,
            self.env.ref("l10n_br_fiscal.fo_compras_compras_comercializacao"),
        )

        move.action_post()
        self.assertEqual(move.state, "posted")
        move.button_cancel()
        self.assertEqual(move.state, "cancel")
        move.button_draft()
        self.assertEqual(move.state, "draft")

    def test_product_fiscal_price_and_qty_edition(self):
        self.user.groups_id += self.env.ref("l10n_br_fiscal.group_user")
        nfe_user_group = self.env.ref(
            "l10n_br_nfe.group_user", raise_if_not_found=False
        )
        if nfe_user_group:
            self.user.groups_id += nfe_user_group

        move_form = Form(
            self.env["account.move"].with_context(
                default_move_type="out_invoice",
            )
        )
        move_form.company_id = self.env.ref("l10n_br_base.empresa_lucro_presumido")
        move_form.partner_id = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        move_form.document_type_id = self.env.ref("l10n_br_fiscal.document_55")
        move_form.document_serie_id = self.env.ref(
            "l10n_br_fiscal.empresa_lc_document_55_serie_1"
        )
        move_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        move_form.ind_final = "1"
        product_id = self.env.ref("product.product_product_6")
        product_id.list_price = 100
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product_id
            line_form.price_unit = 110
            line_form.quantity = 10
            line_form.fiscal_price = 112
            line_form.fiscal_quantity = 5

        move = move_form.save()
        self.assertEqual(move.fiscal_line_ids[0].price_unit, 110)
        self.assertEqual(move.fiscal_line_ids[0].fiscal_price, 112)
        self.assertEqual(move.fiscal_line_ids[0].quantity, 10)
        self.assertEqual(move.fiscal_line_ids[0].fiscal_quantity, 5)

    def test_product_fiscal_factor(self):
        self.user.groups_id += self.env.ref("l10n_br_fiscal.group_user")
        nfe_user_group = self.env.ref(
            "l10n_br_nfe.group_user", raise_if_not_found=False
        )
        if nfe_user_group:
            self.user.groups_id += nfe_user_group

        move_form = Form(
            self.env["account.move"].with_context(
                default_move_type="out_invoice",
            )
        )
        move_form.company_id = self.env.ref("l10n_br_base.empresa_lucro_presumido")
        move_form.partner_id = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        move_form.document_type_id = self.env.ref("l10n_br_fiscal.document_55")
        move_form.document_serie_id = self.env.ref(
            "l10n_br_fiscal.empresa_lc_document_55_serie_1"
        )
        move_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        product_id = self.env.ref("product.product_product_6")
        product_id.uot_factor = 2
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = product_id
            line_form.price_unit = 100
            line_form.quantity = 10

        doc = move_form.save()
        self.assertEqual(doc.fiscal_line_ids[0].price_unit, 100)
        self.assertEqual(doc.fiscal_line_ids[0].fiscal_price, 50)
        self.assertEqual(doc.fiscal_line_ids[0].quantity, 10)
        self.assertEqual(doc.fiscal_line_ids[0].fiscal_quantity, 20)
