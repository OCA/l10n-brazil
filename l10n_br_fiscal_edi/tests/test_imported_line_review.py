# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase


class TestImportedLineReview(TransactionCase):
    """Review of the lines of an imported document: states, unit, factor and de-para."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_kg = cls.env.ref("uom.product_uom_kgm")
        cls.uom_ton = cls.env.ref("uom.product_uom_ton")
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Supplier of flour",
                "state_id": cls.env.ref("base.state_br_mg").id,
                "country_id": cls.env.ref("base.br").id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Wheat flour", "uom_id": cls.uom_kg.id, "uom_po_id": cls.uom_kg.id}
        )
        cls.company = cls.env.company
        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": cls.env.ref(
                    "l10n_br_fiscal.document_55_serie_1"
                ).id,
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_compras").id,
                "imported_document": True,
                "partner_id": cls.partner.id,
                "company_id": cls.company.id,
            }
        )
        # The supplier sells bags (SC) of 25 kg
        cls.line = cls._create_line()

    @classmethod
    def _create_line(cls, **values):
        vals = {
            "document_id": cls.document.id,
            "name": "FLOUR T1 BAG 25KG",
            "quantity": 2.0,
            "price_unit": 100.0,
            "uom_id": cls.uom_unit.id,
            "partner_uom_code": "SC",
            "partner_cfop_id": cls.env.ref("l10n_br_fiscal.cfop_6102").id,
        }
        vals.update(values)
        return cls.env["l10n_br_fiscal.document.line"].create(vals)

    def test_init_and_aggregate_states(self):
        matched = self._create_line(
            name="Already matched",
            product_id=self.product.id,
            quantity=1.0,
            price_unit=10.0,
            uom_id=self.uom_kg.id,
            partner_uom_code="KG",
        )
        self.document._init_import_states()
        self.assertEqual(self.line.import_state, "pending")
        self.assertEqual(matched.import_state, "matched")
        self.assertEqual(self.document.import_state, "pending")
        self.assertEqual(self.document.import_pending_count, 2)

        matched._apply_import_depara()
        self.assertEqual(self.document.import_state, "in_progress")
        self.line.product_id = self.product
        self.line._apply_import_depara(uom=self.uom_kg, factor=25.0)
        self.assertEqual(self.document.import_state, "resolved")
        self.assertEqual(self.document.import_pending_count, 0)

    def test_init_never_undoes_the_decision_of_a_person(self):
        self.line.import_state = "resolved"
        self.document._init_import_states()
        self.assertEqual(self.line.import_state, "resolved")

    def test_unit_not_confirmed_keeps_the_line_pending(self):
        """A unit the supplier declared that matched nothing is not replaced by the
        unit of the product: the line waits for a person until one is chosen."""
        self.line.product_id = self.product
        self.assertTrue(self.line._import_unit_unconfirmed())
        self.document._init_import_states()
        self.assertEqual(self.line.import_state, "pending")
        # applying the review with the unit still unconfirmed does not resolve it
        self.line._apply_import_depara()
        self.assertEqual(self.line.import_state, "pending")
        self.line._apply_import_depara(uom=self.uom_kg, factor=25.0)
        self.assertFalse(self.line._import_unit_unconfirmed())
        self.assertEqual(self.line.import_state, "resolved")

    def test_unit_declared_and_matched_is_confirmed(self):
        line = self._create_line(
            product_id=self.product.id, uom_id=self.uom_kg.id, partner_uom_code="KG"
        )
        self.assertFalse(line._import_unit_unconfirmed())
        self.assertTrue(self.line._import_unit_unconfirmed())

    def test_apply_depara_math_and_snapshot(self):
        """Quantity times factor, price divided by it: the total does not change and
        the values of the supplier stay as a snapshot."""
        self.line._apply_import_depara(
            product=self.product, uom=self.uom_kg, factor=25.0
        )
        self.assertEqual(self.line.import_state, "resolved")
        self.assertEqual(self.line.partner_quantity, 2.0)
        self.assertEqual(self.line.partner_price_unit, 100.0)
        self.assertEqual(self.line.partner_uom_code, "SC")
        self.assertEqual(self.line.uom_id, self.uom_kg)
        self.assertEqual(self.line.quantity, 50.0)
        self.assertEqual(self.line.price_unit, 4.0)
        # what was learned is the code and the name of the supplier: the price is
        # negotiated by purchasing and is not taken from the note
        info = self.line.import_supplierinfo_id
        self.assertEqual(info.partner_id, self.partner)
        self.assertFalse(info.price)
        self.assertIn(info, self.product.product_tmpl_id.seller_ids)

    def test_the_total_declared_survives_the_factor(self):
        """10 boxes at 35.00 with a factor of 12 are 120 units at 2.92: the total
        is 350.00 as the file declared it, not 350.40."""
        line = self._create_line(
            quantity=10.0,
            price_unit=35.0,
            partner_price_gross=350.0,
            partner_uom_code="CX",
        )
        line._apply_import_depara(product=self.product, uom=self.uom_kg, factor=12.0)
        self.assertEqual(line.quantity, 120.0)
        self.assertEqual(line.price_unit, 2.92)
        self.assertEqual(line.price_gross, 350.0)
        self.assertEqual(line.fiscal_amount_total, 350.0)
        # control: without the declared total the cents drift
        line.partner_price_gross = 0.0
        self.assertAlmostEqual(line.price_gross, 350.4)

    def test_reapplying_converts_from_the_snapshot(self):
        """Fixing a wrong factor converts the declared values again, it does not
        compound the first conversion."""
        self.line._apply_import_depara(
            product=self.product, uom=self.uom_kg, factor=25.0
        )
        self.line._apply_import_depara(uom=self.uom_ton, factor=0.025)
        self.assertEqual(self.line.partner_quantity, 2.0)
        self.assertAlmostEqual(self.line.quantity, 0.05, places=4)
        self.assertAlmostEqual(self.line.price_unit, 4000.0, places=2)

    def test_reapplying_a_pending_line_does_not_compound(self):
        """A line left pending by an unconfirmed unit was converted once: the next
        application starts from the snapshot too."""
        self.line._apply_import_depara(product=self.product, factor=25.0)
        self.assertEqual(self.line.import_state, "pending")
        self.line._apply_import_depara(factor=25.0)
        self.assertEqual(self.line.quantity, 50.0)
        self.assertEqual(self.line.price_unit, 4.0)

    def test_factor_back_to_one_restores_the_declared_values(self):
        self.line._apply_import_depara(
            product=self.product, uom=self.uom_kg, factor=25.0
        )
        self.line._apply_import_depara(uom=self.uom_kg, factor=1.0)
        # quantity and price are checked apart: the total does not depend on the factor
        self.assertEqual(self.line.quantity, 2.0)
        self.assertEqual(self.line.price_unit, 100.0)

    def test_unknown_supplier_unit_does_not_zero_the_line(self):
        """A unit with no equivalent leaves the line with no unit and no snapshot:
        the conversion must not run against zeros."""
        line = self._create_line(uom_id=False)
        self.assertFalse(line.uom_id)
        line._apply_import_depara(product=self.product, uom=self.uom_kg, factor=25.0)
        self.assertEqual(line.partner_uom_code, "SC")
        self.assertEqual(line.quantity, 50.0)
        self.assertEqual(line.price_unit, 4.0)

    def test_resolving_a_line_reloads_the_form_of_the_document(self):
        """The button is in the dialog of the line, and the form of the document would
        keep the values it read before the review."""
        self.line.product_id = self.product
        action = self.line.action_resolve_line()
        self.assertEqual(action, {"type": "ir.actions.client", "tag": "reload"})

    def test_resolving_a_line_needs_the_product(self):
        with self.assertRaises(UserError):
            self.line.action_resolve_line()

    def test_supplier_info_is_reused_across_imports(self):
        """The same item of the same supplier reuses what was learned."""
        self.line._apply_import_depara(
            product=self.product, uom=self.uom_kg, factor=25.0
        )
        learned = self.line.import_supplierinfo_id
        second = self._create_line(quantity=4.0, price_unit=110.0)
        second._apply_import_depara(product=self.product, uom=self.uom_kg, factor=25.0)
        self.assertEqual(second.import_supplierinfo_id, learned)
        self.assertEqual(
            self.env["product.supplierinfo"].search_count(
                [
                    ("partner_id", "=", self.partner.id),
                    ("product_id", "=", self.product.id),
                ]
            ),
            1,
        )
        self.assertFalse(learned.price)

    def test_the_review_starts_with_a_factor_of_one(self):
        """The column has no default, so a line is not rewritten at the installation:
        the factor of one is given when the review starts."""
        line = self._create_line()
        self.assertFalse(line.import_uom_factor)
        line.document_id._init_import_states()
        self.assertEqual(line.import_uom_factor, 1.0)

    def test_the_pre_migration_creates_the_column_of_the_state_and_can_run_again(
        self,
    ):
        import importlib.util
        import os

        from odoo.modules.module import get_module_path

        path = os.path.join(
            get_module_path("l10n_br_fiscal_edi"),
            "migrations",
            "16.0.2.5.2",
            "pre-migration.py",
        )
        spec = importlib.util.spec_from_file_location("edi_pre_migration", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.migrate(self.env.cr, "16.0.2.5.0")
        module.migrate(self.env.cr, "16.0.2.5.0")
        self.env.cr.execute(
            "SELECT 1 FROM information_schema.columns WHERE table_name = "
            "'l10n_br_fiscal_document' AND column_name = 'import_state'"
        )
        self.assertTrue(self.env.cr.fetchone())

    def test_the_hook_that_creates_the_column_of_the_state_can_run_again(self):
        from ..hooks import pre_init_hook

        pre_init_hook(self.env.cr)
        pre_init_hook(self.env.cr)
        self.env.cr.execute(
            "SELECT 1 FROM information_schema.columns WHERE table_name = "
            "'l10n_br_fiscal_document' AND column_name = 'import_state'"
        )
        self.assertTrue(self.env.cr.fetchone())

    def test_the_registry_of_purchasing_keeps_its_price_and_its_product(self):
        """A registry that purchasing keeps on the template, with the price it
        negotiated, learns the code of the supplier and nothing else."""
        registry = self.env["product.supplierinfo"].create(
            {
                "partner_id": self.partner.id,
                "product_tmpl_id": self.product.product_tmpl_id.id,
                "product_code": self.line._get_partner_product_code(),
                "price": 10.0,
                "min_qty": 5.0,
            }
        )
        self.line._apply_import_depara(
            product=self.product, uom=self.uom_kg, factor=25.0
        )
        self.assertEqual(self.line.import_supplierinfo_id, registry)
        self.assertEqual(registry.price, 10.0)
        self.assertFalse(registry.product_id)

    def test_the_mapping_of_another_company_is_not_used(self):
        other = self.env["res.company"].search([("id", "!=", self.company.id)], limit=1)
        self.assertTrue(other)
        registry = self.env["product.supplierinfo"].create(
            {
                "partner_id": self.partner.id,
                "product_tmpl_id": self.product.product_tmpl_id.id,
                "product_code": self.line._get_partner_product_code(),
                "company_id": other.id,
            }
        )
        self.line._apply_import_depara(
            product=self.product, uom=self.uom_kg, factor=25.0
        )
        self.assertNotEqual(self.line.import_supplierinfo_id, registry)
        self.assertEqual(
            self.line.import_supplierinfo_id.company_id, self.line.company_id
        )

    def test_a_fiscal_user_learns_the_mapping_as_the_author(self):
        """The fiscal user has no right on purchases, and the supplier info is
        still created, in the name of whoever reviewed the line."""
        user = self.env["res.users"].create(
            {
                "name": "Fiscal user",
                "login": "fiscal_user_review",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("l10n_br_fiscal.group_user").id,
                        ],
                    )
                ],
            }
        )
        self.assertFalse(
            self.env["product.supplierinfo"]
            .with_user(user)
            .check_access_rights("create", raise_exception=False)
        )
        line = self.line.with_user(user)
        line._apply_import_depara(product=self.product, uom=self.uom_kg, factor=25.0)
        info = line.import_supplierinfo_id.sudo()
        self.assertTrue(info)
        self.assertEqual(info.create_uid, user)

    def test_operation_suggested_through_the_cfop_of_the_issuer(self):
        """The operation that receives the CFOP the issuer wrote is suggested for
        the line and, by vote, for the document."""
        operation = self.env["l10n_br_fiscal.operation"].create(
            {
                "code": "TST-COMPRA",
                "name": "Purchase for resale (test)",
                "fiscal_operation_type": "in",
                "fiscal_type": "purchase",
            }
        )
        self.env["l10n_br_fiscal.operation.line"].create(
            {
                "fiscal_operation_id": operation.id,
                "name": "Purchase for resale (test)",
                "cfop_internal_id": self.env.ref("l10n_br_fiscal.cfop_2102").id,
            }
        )
        operation.action_approve()
        self.document.partner_operation_name = operation.name
        suggested = self.line._suggest_fiscal_operation_in()
        self.assertEqual(suggested, operation)
        self.assertEqual(self.document._suggest_fiscal_operation(), operation)
        self.assertFalse(
            self._create_line(partner_cfop_id=False)._suggest_fiscal_operation_in()
        )

    def test_the_nature_declared_breaks_a_tie_between_operations(self):
        """Two operations answer the same CFOP: the one named like the nature of the
        operation that the file declared wins."""
        first = self.line._suggest_fiscal_operation_in()
        self.assertTrue(first)
        operation = self.env["l10n_br_fiscal.operation"].create(
            {
                "code": "TST-TIE",
                "name": "Same CFOP as the first (test)",
                "fiscal_operation_type": "in",
                "fiscal_type": "purchase",
            }
        )
        self.env["l10n_br_fiscal.operation.line"].create(
            {
                "fiscal_operation_id": operation.id,
                "name": "Same CFOP as the first (test)",
                "cfop_internal_id": self.env.ref("l10n_br_fiscal.cfop_2102").id,
            }
        )
        operation.action_approve()
        self.assertNotEqual(first, operation)
        self.document.partner_operation_name = operation.name
        self.assertEqual(self.line._suggest_fiscal_operation_in(), operation)

    def test_find_unit_by_fiscal_code_then_by_alias(self):
        uom_model = self.env["uom.uom"]
        sack = uom_model.create(
            {
                "name": "Zz bag of 25 kg",
                "category_id": self.uom_kg.category_id.id,
                "uom_type": "bigger",
                "factor_inv": 25.0,
                "code": "ZZB",
                "alias_ids": [(0, 0, {"code": "SACKX"})],
            }
        )
        self.assertEqual(uom_model._match_by_fiscal_code("ZZB"), sack)
        self.assertEqual(uom_model._match_by_fiscal_code("SACKX"), sack)
        self.assertEqual(uom_model._match_by_fiscal_code("", "SACKX"), sack)
        self.assertFalse(uom_model._match_by_fiscal_code("NOPE"))
        self.assertFalse(uom_model._match_by_fiscal_code(False))

    def test_search_unit_by_fiscal_code_and_alias(self):
        """The unit is searched the way people think of it, and the list is exactly
        the units that answer."""
        uom_model = self.env["uom.uom"]
        sack = uom_model.create(
            {
                "name": "Zz bag of 25 kg",
                "category_id": self.uom_kg.category_id.id,
                "uom_type": "bigger",
                "factor_inv": 25.0,
                "code": "ZZB",
                "alias_ids": [(0, 0, {"code": "SACKX"})],
            }
        )
        search = uom_model.with_context(uom_search_fiscal_code=True)
        self.assertEqual(
            [uom.id for uom, _name in self._names(search, "ZZB")], [sack.id]
        )
        self.assertEqual(
            [uom.id for uom, _name in self._names(search, "SACKX")], [sack.id]
        )
        self.assertEqual(
            [uom.id for uom, _name in self._names(search, "Zz bag")], [sack.id]
        )
        self.assertEqual(search.name_search("NOPE"), [])
        # without the context the code is not searched
        self.assertNotIn(
            sack.id, [uom_id for uom_id, _name in uom_model.name_search("ZZB")]
        )

    def _names(self, model, term):
        return [
            (model.browse(uom_id), name) for uom_id, name in model.name_search(term)
        ]

    def _plain_user(self, login, fiscal=False):
        groups = [self.env.ref("base.group_user").id]
        if fiscal:
            groups.append(self.env.ref("l10n_br_fiscal.group_user").id)
        return self.env["res.users"].create(
            {
                "name": login,
                "login": login,
                "company_id": self.company.id,
                "company_ids": [(6, 0, self.company.ids)],
                "groups_id": [(6, 0, groups)],
            }
        )

    def _open_the_access_of_the_line(self):
        """As l10n_br_account does: every internal user reads and writes the line,
        and the users of invoicing read the document."""
        for model, write in (
            ("l10n_br_fiscal.model_l10n_br_fiscal_document_line", True),
            ("l10n_br_fiscal.model_l10n_br_fiscal_document", False),
        ):
            self.env["ir.model.access"].create(
                {
                    "name": "test: open to the internal user",
                    "model_id": self.env.ref(model).id,
                    "group_id": self.env.ref("base.group_user").id,
                    "perm_read": True,
                    "perm_write": write,
                    "perm_create": write,
                    "perm_unlink": False,
                }
            )

    def test_a_user_without_the_fiscal_group_cannot_choose_the_product_directly(self):
        self._open_the_access_of_the_line()
        self.document._init_import_states()
        user = self._plain_user("test_line_plain_user")
        line = self.line.with_user(user)
        with self.assertRaises(AccessError):
            line.write({"product_id": self.product.id})
        self.assertFalse(self.line.product_id)
        # what is not the product is not the rule of this check
        line.write({"name": "Renamed by the buyer"})

    def test_a_fiscal_user_chooses_the_product_of_a_line_under_review(self):
        self._open_the_access_of_the_line()
        self.document._init_import_states()
        user = self._plain_user("test_line_fiscal_user", fiscal=True)
        self.line.with_user(user).write({"product_id": self.product.id})
        self.assertEqual(self.line.product_id, self.product)

    def test_the_line_already_resolved_follows_the_ordinary_rules(self):
        """The bill is edited by users of accounting: once the review is over the
        line is not under this rule."""
        self._open_the_access_of_the_line()
        self.document._init_import_states()
        self.line.write({"product_id": self.product.id})
        self.line.write({"import_state": "resolved"})
        user = self._plain_user("test_line_accountant")
        self.line.with_user(user).write({"product_id": self.product.id})
