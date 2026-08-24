# Copyright (C) 2026  KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_INUTILIZADA,
    SITUACAO_EDOC_REJEITADA,
)
from odoo.addons.l10n_br_fiscal_closing.models.closing import SITUACAO_EDOC


class TestClosingStates(TransactionCase):
    def test_closing_exported_states(self):
        """The fiscal closing exports the documents the tax authority knows.

        'inutilizada' must be exported (an invalidated number has to be
        declared) and 'rejeitada' must not (a rejected document does not
        exist for the tax authority).
        """
        self.assertIn(SITUACAO_EDOC_INUTILIZADA, SITUACAO_EDOC)
        self.assertNotIn(SITUACAO_EDOC_REJEITADA, SITUACAO_EDOC)
        self.assertIn(SITUACAO_EDOC_AUTORIZADA, SITUACAO_EDOC)
        self.assertIn(SITUACAO_EDOC_CANCELADA, SITUACAO_EDOC)
        self.assertIn(SITUACAO_EDOC_DENEGADA, SITUACAO_EDOC)
