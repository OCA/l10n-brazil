# Copyright (C) 2020  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from . import test_l10n_br_purchase


class TestL10nBrPurchaseSN(test_l10n_br_purchase.L10nBrPurchaseBaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.po_products = cls.env.ref("l10n_br_purchase.sn_po_only_products")
