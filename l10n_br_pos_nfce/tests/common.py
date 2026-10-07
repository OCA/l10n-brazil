# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.models import BaseModel

from odoo.addons.l10n_br_fiscal.constants.fiscal import MODELO_FISCAL_NFCE
from odoo.addons.point_of_sale.tests.common import Form, TestPoSCommon


class TestNFCePosOrderCommon(TestPoSCommon):
    @classmethod
    def setUpClass(cls, **kwargs):
        cls._apply_form_patch()

        super().setUpClass(
            chart_template_ref="l10n_br_coa_generic.l10n_br_coa_generic_template",
            **kwargs,
        )

        cls.env.user.write(
            {
                "groups_id": [
                    (4, cls.env.ref("l10n_br_fiscal.group_manager").id),
                ],
            }
        )

        cls.config = cls.basic_config
        cls.config.simplified_document_type = MODELO_FISCAL_NFCE

        cls.cash_journal = cls.env["account.journal"].create(
            {
                "name": "POS Cash",
                "code": "POSCASH",
                "type": "cash",
                "company_id": cls.company.id,
            }
        )

        payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "Cash",
                "payment_type": "inbound",
                "company_id": cls.company.id,
                "payment_method_id": cls.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "bank_account_link": "fixed",
                "fixed_journal_id": cls.cash_journal.id,
                "fiscal_payment_mode": "01",
            }
        )

        cls.cash_pm = cls.env["pos.payment.method"].create(
            {
                "name": "Cash",
                "journal_id": cls.cash_journal.id,
                "company_id": cls.company.id,
                "payment_mode_id": payment_mode.id,
            }
        )

        cls.config.write(
            {
                "payment_method_ids": [(4, cls.cash_pm.id)],
            }
        )

        cls._setup_nfce_serie()

        cls.product1 = cls.create_product("Product 1", cls.categ_basic, 10.0, 5)
        cls.product2 = cls.create_product("Product 2", cls.categ_basic, 20.0, 10)
        cls.adjust_inventory([cls.product1, cls.product2], [50, 50])

    @classmethod
    def _apply_form_patch(cls):
        if getattr(Form, "_l10n_br_nfce_patched", False):
            return

        Form._l10n_br_nfce_patched = True

        def form_setattr(self, field, value):
            descr = self._view["fields"].get(field)
            assert descr is not None, "%s was not found in the view" % field
            assert descr["type"] not in (
                "many2many",
                "one2many",
            ), "Can't set an o2m or m2m field, manipulate the corresponding proxies"

            if descr["type"] == "many2one":
                assert isinstance(value, BaseModel)
                assert value._name == descr["relation"]
                value = value.id

            self._values[field] = value
            self._perform_onchange([field])

        Form.__setattr__ = form_setattr

    @classmethod
    def _setup_nfce_serie(cls):
        document_type = cls.env.ref("l10n_br_fiscal.document_65")

        serie = cls.env["l10n_br_fiscal.document.serie"].search(
            [
                ("code", "=", "2"),
                ("document_type_id", "=", document_type.id),
                ("company_id", "=", cls.company.id),
            ],
            limit=1,
        )

        if not serie:
            sequence = cls.env["ir.sequence"].create(
                {
                    "name": "NFC-e série 2",
                    "code": "l10n_br_fiscal.document.serie",
                    "prefix": "",
                    "padding": 0,
                    "number_next": 1000,
                    "implementation": "no_gap",
                    "company_id": cls.company.id,
                }
            )

            serie = cls.env["l10n_br_fiscal.document.serie"].create(
                {
                    "code": "2",
                    "name": "Série 2",
                    "document_type_id": document_type.id,
                    "company_id": cls.company.id,
                    "active": True,
                    "internal_sequence_id": sequence.id,
                }
            )
        elif not serie.internal_sequence_id:
            serie.internal_sequence_id = cls.env["ir.sequence"].create(
                {
                    "name": "NFC-e série 2",
                    "code": "l10n_br_fiscal.document.serie",
                    "prefix": "",
                    "padding": 0,
                    "number_next": 1000,
                    "implementation": "no_gap",
                    "company_id": cls.company.id,
                }
            )

        cls.config.nfce_document_serie_id = serie
