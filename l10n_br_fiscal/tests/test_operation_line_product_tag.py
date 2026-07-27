# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from psycopg2 import IntegrityError

from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestOperationLineProductTag(TransactionCase):
    """Automatic operation line match by product fiscal tag.

    The tag discriminates groups of products that need their own CFOP and
    that no other operation line criterion tells apart. The reference case
    is tax substitution: 5401/6401 (substitute) and 5405/6404 (substituted)
    share the same fiscal item type, partner IE indicator and tax framework,
    so only a product level marker can select between them.

    These tests exercise the resolver itself (``_line_domain`` and
    ``_select_best_line``), which the document level tests reach only
    indirectly.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        # Same partner as the demo ST documents: ICMS contributor in another
        # state, so the external CFOP applies and the lines, which require
        # ind_ie_dest=1, are eligible.
        cls.partner = cls.env.ref("l10n_br_base.res_partner_cliente5_pe")
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_venda")

        cls.tag_6401 = cls.env.ref("l10n_br_fiscal.product_tag_st_6401")
        cls.tag_6404 = cls.env.ref("l10n_br_fiscal.product_tag_st_6404")

        cls.line_st_substituto = cls.env.ref(
            "l10n_br_fiscal.fo_venda_venda_st_substituto"
        )
        cls.line_st_substituido = cls.env.ref(
            "l10n_br_fiscal.fo_venda_revenda_st_substituido"
        )
        cls.tag_6403 = cls.env.ref("l10n_br_fiscal.product_tag_st_6403")
        cls.line_st_substituto_revenda = cls.env.ref(
            "l10n_br_fiscal.fo_venda_revenda_st_substituto"
        )
        cls.line_venda = cls.env.ref("l10n_br_fiscal.fo_venda_venda")
        cls.line_revenda = cls.env.ref("l10n_br_fiscal.fo_venda_revenda")

    def _create_product(self, fiscal_type, tags=None):
        """Product with a company dependent fiscal type and optional tags."""
        product = self.env["product.product"].create(
            {"name": "Product fiscal tag test"}
        )
        product = product.with_company(self.company)
        product.fiscal_type = fiscal_type
        if tags:
            product.fiscal_product_tag_ids = [(6, 0, tags.ids)]
        return product

    def _resolve(self, product):
        return self.operation.with_company(self.company).line_definition(
            self.company, self.partner, product
        )

    def test_tagged_product_selects_st_substituto_line(self):
        """Own production tagged as ST substitute resolves to CFOP 6401."""
        product = self._create_product("04", self.tag_6401)
        line = self._resolve(product)
        self.assertEqual(line, self.line_st_substituto)
        self.assertEqual(line.cfop_external_id.code, "6401")

    def test_tagged_product_selects_st_substituido_line(self):
        """Resale tagged as ST substituted resolves to CFOP 6404."""
        product = self._create_product("00", self.tag_6404)
        line = self._resolve(product)
        self.assertEqual(line, self.line_st_substituido)
        self.assertEqual(line.cfop_external_id.code, "6404")

    def test_tagged_product_selects_st_substituto_resale_line(self):
        """Resale as the substitute taxpayer resolves to CFOP 6403.

        The three ST lines share the partner IE indicator and the tax
        framework; 6401 differs from 6403 by the fiscal item type, but 6403
        and 6404 differ only by the tag.
        """
        product = self._create_product("00", self.tag_6403)
        line = self._resolve(product)
        self.assertEqual(line, self.line_st_substituto_revenda)
        self.assertEqual(line.cfop_external_id.code, "6403")

    def test_untagged_product_never_selects_a_tagged_line(self):
        """A product without tags must not fall into an ST line.

        This is the isolation guarantee of the feature: tagging a line
        restricts it, it never widens the match.
        """
        product = self._create_product("00")
        line = self._resolve(product)
        self.assertFalse(
            line.fiscal_product_tag_ids,
            "An untagged product selected a tagged operation line.",
        )

    def test_unknown_tag_falls_back_to_untagged_line(self):
        """A tag used by no line degrades to the plain line, not to nothing."""
        orphan_tag = self.env["l10n_br_fiscal.product.tag"].create(
            {"name": "Tag used by no operation line"}
        )
        product = self._create_product("00", orphan_tag)
        line = self._resolve(product)
        self.assertTrue(line, "Resolution returned no line at all.")
        self.assertFalse(line.fiscal_product_tag_ids)

    def test_product_with_several_tags_matches_line_sharing_one(self):
        """Matching is by intersection: one tag in common is enough."""
        orphan_tag = self.env["l10n_br_fiscal.product.tag"].create(
            {"name": "Extra tag with no line"}
        )
        product = self._create_product("00", orphan_tag | self.tag_6404)
        line = self._resolve(product)
        self.assertEqual(line, self.line_st_substituido)

    def test_tagged_line_outscores_untagged_line(self):
        """Documented preference: on equal terms, the tagged line wins.

        Checked on ``_select_best_line`` directly so the assertion does not
        depend on which lines the domain happens to return.
        """
        candidates = self.line_revenda | self.line_st_substituido
        best = self.operation._select_best_line(candidates)
        self.assertEqual(best, self.line_st_substituido)

    def test_select_best_line_without_candidates(self):
        """No candidate returns an empty recordset, not an error."""
        empty = self.env["l10n_br_fiscal.operation.line"]
        self.assertEqual(self.operation._select_best_line(empty), empty)

    def test_line_domain_includes_the_tag_clause(self):
        """The domain offers the line either sharing a tag or having none."""
        product = self._create_product("00", self.tag_6404)
        domain = self.operation._line_domain(self.company, self.partner, product)
        self.assertIn(("fiscal_product_tag_ids", "in", self.tag_6404.ids), domain)
        self.assertIn(("fiscal_product_tag_ids", "=", False), domain)

    @mute_logger("odoo.sql_db")
    def test_tag_name_is_unique(self):
        """Tags are keyed by name, so duplicates must be rejected."""
        self.env["l10n_br_fiscal.product.tag"].create({"name": "Duplicated tag"})
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.env["l10n_br_fiscal.product.tag"].create({"name": "Duplicated tag"})
            self.env["l10n_br_fiscal.product.tag"].flush()

    @mute_logger("odoo.sql_db")
    def test_tag_name_is_required(self):
        """A nameless tag would defeat the unique constraint.

        Postgres allows any number of NULLs in a unique index, so without
        ``required`` the tag list could fill up with unnamed entries.
        """
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.env["l10n_br_fiscal.product.tag"].create({})

    def test_inactive_tag_is_not_offered(self):
        """Archiving a tag takes it out of the resolution silently.

        Documents the consequence of ``active``: an archived tag no longer
        pulls its line, so the product falls back to the generic line.
        """
        tag = self.env["l10n_br_fiscal.product.tag"].create({"name": "To archive"})
        product = self._create_product("00", tag | self.tag_6404)
        self.assertEqual(self._resolve(product), self.line_st_substituido)
        self.tag_6404.active = False
        product.invalidate_cache()
        line = self._resolve(product)
        self.assertFalse(line.fiscal_product_tag_ids)
