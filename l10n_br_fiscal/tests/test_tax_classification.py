from odoo.tests import Form, TransactionCase
from odoo.tests.common import tagged
from odoo.tools import DotDict


@tagged("post_install", "-at_install")
class TestTaxClassification(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Create company with required fields
        cls.company = cls.env["res.company"].create(
            {
                "name": "Test Company Tax Classification",
                "vat": "97.231.608/0001-69",
                "l10n_br_ie_code": "454.504.604.553",
                "state_id": cls.env.ref("base.state_br_sp").id,
                "city_id": cls.env.ref("l10n_br_base.city_3550308").id,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner Tax Classification",
                "vat": "81.583.054/0001-29",
                "l10n_br_ie_code": "078.016.350.838",
                "state_id": cls.env.ref("base.state_br_sp").id,
                "city_id": cls.env.ref("l10n_br_base.city_3550308").id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product Tax Classification",
                "type": "consu",
                "ncm_id": cls.env.ref("l10n_br_fiscal.ncm_85030010").id,
            }
        )

        # Use a stable operation line already referenced in existing test suites.
        cls.operation_line = cls.env.ref("l10n_br_fiscal.fo_venda_venda")

        # Pick classifications with CBS/IBS taxes set in the provided CSV.
        cls.classification_company = cls.env.ref(
            "l10n_br_fiscal.tax_classification_000001"
        )
        cls.classification_line = cls.env.ref(
            "l10n_br_fiscal.tax_classification_200001"
        )

    def _map_kwargs(self):
        return {
            "company": self.company,
            "partner": self.partner,
            "product": self.product,
            "ncm": self.product.ncm_id,
            "nbm": self.env["l10n_br_fiscal.nbm"],
            "nbs": self.env["l10n_br_fiscal.nbs"],
            "cest": self.env["l10n_br_fiscal.cest"],
            "city_taxation_code": self.env["l10n_br_fiscal.city.taxation.code"],
            "national_taxation_code": self.env["l10n_br_fiscal.national.taxation.code"],
            "service_type": self.env["l10n_br_fiscal.service.type"],
            "ind_final": "1",
        }

    def test_map_fiscal_taxes_tax_classification_from_company(self):
        """Operation line must fallback to company tax classification when empty."""
        self.company.tax_classification_id = self.classification_company
        self.operation_line.tax_classification_id = False

        result = self.operation_line.map_fiscal_taxes(**self._map_kwargs())

        self.assertEqual(result["tax_classification"], self.classification_company)
        self.assertEqual(
            result["taxes"][self.classification_company.tax_cbs_id.tax_domain],
            self.classification_company.tax_cbs_id,
        )
        self.assertEqual(
            result["taxes"][self.classification_company.tax_ibs_id.tax_domain],
            self.classification_company.tax_ibs_id,
        )

    def test_map_fiscal_taxes_tax_classification_from_operation_line(self):
        """Operation line tax classification must override company default."""
        self.company.tax_classification_id = self.classification_company
        self.operation_line.tax_classification_id = self.classification_line

        result = self.operation_line.map_fiscal_taxes(**self._map_kwargs())

        self.assertEqual(result["tax_classification"], self.classification_line)
        self.assertEqual(
            result["taxes"][self.classification_line.tax_cbs_id.tax_domain],
            self.classification_line.tax_cbs_id,
        )
        self.assertEqual(
            result["taxes"][self.classification_line.tax_ibs_id.tax_domain],
            self.classification_line.tax_ibs_id,
        )

    def test_document_line_receives_cbs_ibs_from_tax_classification(self):
        """Fiscal document line must receive tax classification and CBS/IBS taxes."""
        self.company.tax_classification_id = self.classification_company
        self.operation_line.tax_classification_id = False

        doc_form = Form(
            self.env["l10n_br_fiscal.document"].with_context(
                default_fiscal_operation_type="out",
                default_company_id=self.company.id,
            )
        )
        doc_form.partner_id = self.partner
        doc_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        doc_form.ind_final = "1"

        with doc_form.fiscal_line_ids.new() as line_form:
            line_form.product_id = self.product
            # Ensure we map on a predictable operation line for this assertion.
            line_form.fiscal_operation_line_id = self.operation_line

            self.assertEqual(
                line_form.tax_classification_id, self.classification_company
            )
            self.assertEqual(
                line_form.cbs_tax_id, self.classification_company.tax_cbs_id
            )
            self.assertEqual(
                line_form.ibs_tax_id, self.classification_company.tax_ibs_id
            )

            self.assertIn(
                self.classification_company.tax_cbs_id, line_form.fiscal_tax_ids
            )
            self.assertIn(
                self.classification_company.tax_ibs_id, line_form.fiscal_tax_ids
            )

    def _ibscbs_binding(self, c_class_trib):
        """The XML IBSCBS group, as the document parser yields it."""
        return DotDict(
            {
                "CST": "000",
                "cClassTrib": c_class_trib,
                "gIBSCBS": {
                    "vBC": "2767.46",
                    "gIBSUF": {"pIBSUF": "0.1000", "vIBSUF": "2.77"},
                    "gCBS": {"pCBS": "0.9000", "vCBS": "24.91"},
                },
            }
        )

    def test_import_ibscbs_sets_tax_classification_from_cclasstrib(self):
        """The cClassTrib sent in the document must fill the line classification."""
        vals = {}
        self.env["l10n_br_fiscal.document.line"]._add_imported_ibscbs_vals(
            self._ibscbs_binding("000001"), vals
        )

        self.assertEqual(
            vals.get("tax_classification_id"), self.classification_company.id
        )

    def test_import_ibscbs_ignores_unknown_cclasstrib(self):
        """An unregistered classification code must not break the import."""
        vals = {}
        self.env["l10n_br_fiscal.document.line"]._add_imported_ibscbs_vals(
            self._ibscbs_binding("999999"), vals
        )

        self.assertNotIn("tax_classification_id", vals)

    def _load_classification(self, code, values):
        """Load a classification as a module update does."""
        self.env["l10n_br_fiscal.tax.classification"].with_context(
            install_module="l10n_br_fiscal"
        )._load_records(
            [{"xml_id": f"l10n_br_fiscal.tax_classification_{code}", "values": values}],
            update=True,
        )

    def test_module_update_keeps_user_taxes(self):
        """A data file reload fills empty taxes and keeps the user's ones."""
        classification = self.env.ref("l10n_br_fiscal.tax_classification_200028")
        user_tax = self.env.ref("l10n_br_fiscal.tax_ibs_0_1_red_40")
        classification.write({"tax_ibs_id": user_tax.id, "tax_cbs_id": False})
        file_cbs = self.env.ref("l10n_br_fiscal.tax_cbs_0_9_red_60")

        self._load_classification(
            "200028",
            {
                "name": "Updated name",
                "tax_ibs_id": self.env.ref("l10n_br_fiscal.tax_ibs_0_1_red_60").id,
                "tax_cbs_id": file_cbs.id,
            },
        )

        self.assertEqual(classification.name, "Updated name")
        # the tax chosen by the user stays, the empty one is filled
        self.assertEqual(classification.tax_ibs_id, user_tax)
        self.assertEqual(classification.tax_cbs_id, file_cbs)

    def _ensure_account_tax_group(self, fiscal_group):
        """Give the current company an account tax group for ``fiscal_group``.

        Odoo 19 scopes account.tax.group per company and country, and the
        Brazilian ones are only created for companies carrying a chart. The
        test copies a fiscal tax, which creates its account.tax in the current
        company: without a mapped group the create fails on the NOT NULL
        tax_group_id the core computes.
        """
        account_group = self.env["account.tax.group"].search(
            [("fiscal_tax_group_id", "=", fiscal_group.id)], limit=1
        )
        if account_group:
            return account_group
        # Odoo 19 validates the group country against the tax country, which
        # follows the fiscal country of the company.
        return self.env["account.tax.group"].create(
            {
                "name": fiscal_group.name,
                "company_id": self.env.company.id,
                "country_id": self.env.company.account_fiscal_country_id.id,
                "fiscal_tax_group_id": fiscal_group.id,
            }
        )

    def test_module_update_fixes_tax_of_another_cst(self):
        """Only a tax carrying the cClassTrib CST replaces one that does not."""
        classification = self.env.ref("l10n_br_fiscal.tax_classification_011002")
        cst_011 = self.env.ref("l10n_br_fiscal.cst_ibs_011")
        wrong_cst_tax = classification.tax_ibs_id  # CST 200 in the data file
        self.assertEqual(wrong_cst_tax.cst_out_id.code, "200")
        self._ensure_account_tax_group(wrong_cst_tax.tax_group_id)
        right_cst_tax = wrong_cst_tax.copy(
            {"name": "IBS CST 011", "cst_in_id": cst_011.id, "cst_out_id": cst_011.id}
        )

        self._load_classification("011002", {"tax_ibs_id": right_cst_tax.id})
        self.assertEqual(classification.tax_ibs_id, right_cst_tax)

        # and from then on the file no longer touches it
        self._load_classification("011002", {"tax_ibs_id": wrong_cst_tax.id})
        self.assertEqual(classification.tax_ibs_id, right_cst_tax)

    def test_classification_taxes_match_cst(self):
        """Every IBS/CBS tax of a classification carries the cClassTrib CST."""
        imd = self.env["ir.model.data"].search(
            [
                ("module", "=", "l10n_br_fiscal"),
                ("model", "=", "l10n_br_fiscal.tax.classification"),
            ]
        )
        classifications = self.env["l10n_br_fiscal.tax.classification"].browse(
            imd.mapped("res_id")
        )
        for classification in classifications:
            if classification.code.startswith("011"):
                # The 011xxx classifications still point to CST 200 and 000
                # taxes, fixed in OCA/l10n-brazil#5133. The line CST comes
                # from the classification anyway.
                continue
            for tax in classification.tax_ibs_id | classification.tax_cbs_id:
                self.assertEqual(
                    tax.cst_out_id.code,
                    classification.code[:3],
                    f"{classification.code}: {tax.name} has CST {tax.cst_out_id.code}",
                )

    def test_document_line_cst_from_tax_classification(self):
        """The line IBS/CBS CST comes from the cClassTrib, not from the tax."""
        # the data file points this CST 011 classification to CST 200 taxes
        classification = self.env.ref("l10n_br_fiscal.tax_classification_011002")
        self.assertEqual(classification.tax_ibs_id.cst_out_id.code, "200")
        self.company.tax_classification_id = self.classification_company
        self.operation_line.tax_classification_id = False

        doc_form = Form(
            self.env["l10n_br_fiscal.document"].with_context(
                default_fiscal_operation_type="out",
                default_company_id=self.company.id,
            )
        )
        doc_form.partner_id = self.partner
        doc_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        doc_form.ind_final = "1"

        with doc_form.fiscal_line_ids.new() as line_form:
            line_form.product_id = self.product
            line_form.fiscal_operation_line_id = self.operation_line
            line_form.tax_classification_id = classification

            # the line CST follows the classification, whatever the tax CST
            self.assertEqual(
                line_form.ibs_cst_id, self.env.ref("l10n_br_fiscal.cst_ibs_011")
            )
            self.assertEqual(
                line_form.cbs_cst_id, self.env.ref("l10n_br_fiscal.cst_cbs_011")
            )
