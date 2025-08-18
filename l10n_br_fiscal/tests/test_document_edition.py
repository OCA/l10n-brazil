# Copyright 2025-TODAY  Akretion - Raphaël Valyi
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest import mock

from odoo import Command
from odoo.tests import Form, TransactionCase


class TestDocumentEdition(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env["res.users"].create(
            {
                "name": "Fiscal User",
                "login": "fiscaluser",
                "password": "fiscaluser",
                "groups_id": [
                    Command.set(cls.env.user.groups_id.ids),
                    Command.link(cls.env.ref("l10n_br_fiscal.group_user").id),
                    Command.link(cls.env.ref("base.group_multi_company").id),
                ],
            }
        )
        cls.user.partner_id.email = "accountman@test.com"
        companies = cls.env["res.company"].search([])
        cls.user.write(
            {
                "company_ids": [Command.set(companies.ids)],
                "company_id": cls.env.ref("l10n_br_base.empresa_lucro_presumido"),
            }
        )

        cls.env = cls.env(
            user=cls.user, context=dict(cls.env.context, tracking_disable=True)
        )

    def test_basic_doc_edition(self):
        doc_form = Form(
            self.env["l10n_br_fiscal.document"].with_context(
                default_fiscal_operation_type="out",
            )
        )
        doc_form.company_id = self.env.ref("l10n_br_base.empresa_lucro_presumido")
        doc_form.partner_id = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        doc_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        doc_form.ind_final = "1"
        product_id = self.env.ref("product.product_product_6")
        product_id.list_price = 150  # we will later check we can set price_unit to 100
        with doc_form.fiscal_line_ids.new() as line_form:
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
                line_form.product_id = product_id

            # ensure the tax engine is called with the proper
            # parameters, especially ind_final
            # as it is related=document_id.ind_final
            # which is converted to move_id.ind_final to work live
            mocked.assert_called_with(
                self.env.ref("l10n_br_fiscal.fo_venda_revenda"),
                company=doc_form.company_id,
                partner=doc_form.partner_id,
                product=product_id,
                ncm=product_id.ncm_id,
                nbm=self.env["l10n_br_fiscal.nbm"],
                nbs=self.env["l10n_br_fiscal.nbs"],
                cest=self.env["l10n_br_fiscal.cest"],
                city_taxation_code=self.env["l10n_br_fiscal.city.taxation.code"],
                service_type=self.env["l10n_br_fiscal.service.type"],
                ind_final="1",
            )

            line_form.price_unit = 50
            line_form.quantity = 2
            self.assertEqual(len(line_form.fiscal_tax_ids), 4)
            self.assertEqual(
                line_form.icms_tax_id, self.env.ref("l10n_br_fiscal.tax_icms_12")
            )
            self.assertEqual(line_form.icms_value, 12.0)
            line_form.price_unit = 100
            self.assertEqual(
                line_form.icms_tax_id, self.env.ref("l10n_br_fiscal.tax_icms_12")
            )
            self.assertEqual(line_form.icms_value, 24.0)
            self.assertEqual(
                line_form.fiscal_operation_line_id,
                self.env.ref("l10n_br_fiscal.fo_venda_revenda"),
            )

            # line_form.fiscal_operation_line_id = False
            # self.assertEqual(len(line_form.fiscal_tax_ids), 0)

        doc = doc_form.save()
        self.assertEqual(doc.fiscal_line_ids[0].price_unit, 100)
        self.assertEqual(doc.fiscal_line_ids[0].fiscal_price, 100)
        self.assertEqual(doc.fiscal_line_ids[0].quantity, 2)
        self.assertEqual(doc.fiscal_line_ids[0].fiscal_quantity, 2)
        self.assertEqual(len(doc.fiscal_line_ids[0].fiscal_tax_ids), 4)
        self.assertEqual(
            doc.fiscal_line_ids[0].icms_tax_id.id,
            self.ref("l10n_br_fiscal.tax_icms_12"),
        )

    def test_product_fiscal_factor(self):
        doc_form = Form(
            self.env["l10n_br_fiscal.document"].with_context(
                default_fiscal_operation_type="out",
            )
        )
        doc_form.partner_id = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        doc_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        doc_form.ind_final = "1"
        product_id = self.env.ref("product.product_product_6")
        product_id.uot_factor = 2
        with doc_form.fiscal_line_ids.new() as line_form:
            line_form.product_id = product_id
            line_form.price_unit = 100
            line_form.quantity = 10

        doc = doc_form.save()
        self.assertEqual(doc.fiscal_line_ids[0].price_unit, 100)
        self.assertEqual(doc.fiscal_line_ids[0].fiscal_price, 50)
        self.assertEqual(doc.fiscal_line_ids[0].quantity, 10)
        self.assertEqual(doc.fiscal_line_ids[0].fiscal_quantity, 20)

    def test_product_fiscal_price_and_qty_edition(self):
        doc_form = Form(
            self.env["l10n_br_fiscal.document"].with_context(
                default_fiscal_operation_type="out",
            )
        )
        doc_form.partner_id = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        doc_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        doc_form.ind_final = "1"
        product_id = self.env.ref("product.product_product_6")
        product_id.list_price = 100
        with doc_form.fiscal_line_ids.new() as line_form:
            line_form.product_id = product_id
            line_form.price_unit = 110
            line_form.quantity = 10
            line_form.fiscal_price = 112
            line_form.fiscal_quantity = 5
            self.assertEqual(line_form.price_unit, 110)
            self.assertEqual(line_form.fiscal_price, 112)
            self.assertEqual(line_form.quantity, 10)
            self.assertEqual(line_form.fiscal_quantity, 5)

        doc = doc_form.save()
        self.assertEqual(doc.fiscal_line_ids[0].price_unit, 110)
        self.assertEqual(doc.fiscal_line_ids[0].fiscal_price, 112)
        self.assertEqual(doc.fiscal_line_ids[0].quantity, 10)
        self.assertEqual(doc.fiscal_line_ids[0].fiscal_quantity, 5)
