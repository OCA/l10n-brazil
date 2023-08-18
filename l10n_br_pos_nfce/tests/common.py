# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.models import BaseModel

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.l10n_br_fiscal.constants.fiscal import MODELO_FISCAL_NFCE
from odoo.addons.point_of_sale.tests.common import Form, TestPoSCommon


class TestNFCePosOrderCommon(TestPoSCommon):
    @classmethod
    def setUpClass(cls, **kw):
        cls._apply_monkey_patches()

        super().setUpClass(
            chart_template_ref="l10n_br_coa_generic.l10n_br_coa_generic_template", **kw
        )

        cls.config = cls.basic_config
        cls.config.simplified_document_type = MODELO_FISCAL_NFCE
        cls.config.nfce_document_serie_sequence_number_next = 1000

        cls.product1 = cls.create_product("Product 1", cls.categ_basic, 10.0, 5)
        cls.product2 = cls.create_product("Product 2", cls.categ_basic, 20.0, 10)
        cls.adjust_inventory([cls.product1, cls.product2], [50, 50])

    @classmethod
    def _apply_monkey_patches(cls):
        """Monkey patch to add fiscal group to user and setup company data"""

        def _form_setattr__(self, field, value):
            descr = self._view["fields"].get(field)
            assert descr is not None, "%s was not found in the view" % field
            assert descr["type"] not in (
                "many2many",
                "one2many",
            ), "Can't set an o2m or m2m field, manipulate the corresponding proxies"

            if descr["type"] == "many2one":
                assert isinstance(value, BaseModel) and value._name == descr["relation"]
                # store just the id: that's the output of default_get & (more
                # or less) onchange.
                value = value.id

            self._values[field] = value
            self._perform_onchange([field])

        Form.__setattr__ = _form_setattr__

        superSetUpClass = AccountTestInvoicingCommon.setUpClass

        @classmethod
        def setUpClass(cls, **kw):
            superSetUpClass(**kw)
            cls.env.user.write(
                {"groups_id": [(4, cls.env.ref("l10n_br_fiscal.group_manager").id)]}
            )

        AccountTestInvoicingCommon.setUpClass = setUpClass

        super_setup_company_data = AccountTestInvoicingCommon.setup_company_data

        @classmethod
        def setup_company_data(cls, company_name, chart_template=None, **kwargs):
            company_data = super_setup_company_data(
                company_name, chart_template=chart_template, **kwargs
            )

            # Create stock config.
            if not company_data.get("default_account_stock_in"):
                company_data["default_account_stock_in"] = cls.env[
                    "account.account"
                ].create(
                    {
                        "name": "default_account_stock_in",
                        "code": "STOCKIN",
                        "reconcile": True,
                        "user_type_id": cls.env.ref(
                            "account.data_account_type_current_assets"
                        ).id,
                        "company_id": company_data["company"].id,
                    }
                )
            if not company_data.get("default_account_stock_out"):
                company_data["default_account_stock_out"] = cls.env[
                    "account.account"
                ].create(
                    {
                        "name": "default_account_stock_out",
                        "code": "STOCKOUT",
                        "reconcile": True,
                        "user_type_id": cls.env.ref(
                            "account.data_account_type_current_assets"
                        ).id,
                        "company_id": company_data["company"].id,
                    }
                )
            if not company_data.get("default_account_stock_valuation"):
                company_data["default_account_stock_valuation"] = cls.env[
                    "account.account"
                ].create(
                    {
                        "name": "default_account_stock_valuation",
                        "code": "STOCKVAL",
                        "reconcile": True,
                        "user_type_id": cls.env.ref(
                            "account.data_account_type_current_assets"
                        ).id,
                        "company_id": company_data["company"].id,
                    }
                )
            if not company_data.get("default_warehouse"):
                company_data["default_warehouse"] = cls.env["stock.warehouse"].search(
                    [("company_id", "=", company_data["company"].id)],
                    limit=1,
                )
            return company_data

        AccountTestInvoicingCommon.setup_company_data = setup_company_data
