# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase

# Incoming CFOPs whose official name states where the goods are headed. The
# destination decides whether the input tax may be credited (own use blocks
# the ICMS credit until 2033 by LC 87/96 art. 33, I; fixed assets block the
# IPI credit by RIPI art. 226), so a wrong type_move here silently turns a
# non-creditable purchase into a creditable one.
#
# This is a closed list on purpose: a new CFOP added to the data file with a
# name that mentions own use or fixed assets must be classified explicitly,
# and the test below fails until it is.
DESTINATION_BY_CODE = {
    # own use and consumption
    "1407": "purchase_ownuse",
    "1556": "purchase_ownuse",
    "1557": "purchase_ownuse",
    "1653": "purchase_ownuse",
    "2407": "purchase_ownuse",
    "2556": "purchase_ownuse",
    "2557": "purchase_ownuse",
    "2653": "purchase_ownuse",
    "3552": "purchase_ownuse",
    "3556": "purchase_ownuse",
    "3653": "purchase_ownuse",
    "3667": "purchase_ownuse",
    # fixed assets
    "1406": "purchase_asset",
    "1551": "purchase_asset",
    "1552": "purchase_asset",
    "2406": "purchase_asset",
    "2551": "purchase_asset",
    "2552": "purchase_asset",
    "3551": "purchase_asset",
}

# Words that make a CFOP name state its destination. Used to catch new CFOPs
# that arrive in the data file without an entry in DESTINATION_BY_CODE.
DESTINATION_WORDS = (
    "uso ou consumo",
    "uso e consumo",
    "ativo imobilizado",
    "consumo final",
    "consumo de bordo",
)

# Incoming CFOPs that name a restricted destination but are not acquisitions,
# so they carry no input credit of their own and keep their current type.
NOT_AN_ACQUISITION = {
    "1553",  # devolucao de venda de bem do ativo imobilizado
    "1554",  # retorno de bem do ativo remetido para uso fora do estabelecimento
    "1555",  # entrada de bem do ativo de terceiro
    "1604",  # lancamento do credito relativo a compra de bem para o ativo
    "2553",
    "2554",
    "2555",
    "3553",
}


class TestCfopTypeMove(TransactionCase):
    """The CFOP already carries the destination of the goods in type_move."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cfop = cls.env["l10n_br_fiscal.cfop"]

    def test_destination_classification(self):
        """Each listed CFOP declares the destination its name states."""
        for code, expected in DESTINATION_BY_CODE.items():
            cfop = self.cfop.search([("code", "=", code)], limit=1)
            if not cfop:
                continue
            self.assertEqual(
                cfop.type_move,
                expected,
                f"CFOP {code} ({cfop.name}) should be {expected}",
            )

    def test_no_unclassified_destination(self):
        """A CFOP naming own use or fixed assets is never left unclassified.

        Guards the data file against a new CFOP whose name states a
        destination the law restricts but whose type_move says otherwise.
        """
        unclassified = []
        for cfop in self.cfop.search([("type_in_out", "=", "in")]):
            name = (cfop.name or "").lower()
            if not any(word in name for word in DESTINATION_WORDS):
                continue
            if cfop.code in DESTINATION_BY_CODE or cfop.code in NOT_AN_ACQUISITION:
                continue
            unclassified.append(f"{cfop.code} {cfop.name}")
        self.assertFalse(
            unclassified,
            "CFOPs naming a restricted destination without an explicit "
            f"classification: {unclassified}",
        )
