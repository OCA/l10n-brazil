# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest import mock

import odoo.tests


@odoo.tests.tagged("post_install", "-at_install")
class TestPosNfceTour(odoo.tests.HttpCase):
    def test_pos_nfce_tour(self):
        admin = self.env.ref("base.user_admin")
        config = self.env.ref("l10n_br_pos.pos_config_presumido")
        admin.write(
            {
                "company_ids": [(4, config.company_id.id)],
                "company_id": config.company_id.id,
            }
        )
        config.nfce_document_serie_id = self.env.ref(
            "l10n_br_pos_nfce.document_65_serie_2"
        )
        config.with_user(admin).open_ui()
        # The transmission to the SEFAZ is not part of this test.
        document_class = type(self.env["l10n_br_fiscal.document"])
        with mock.patch.object(
            document_class, "action_document_confirm"
        ), mock.patch.object(document_class, "action_document_send"):
            self.start_tour(
                f"/pos/ui?config_id={config.id}",
                "l10n_br_pos_nfce_tour",
                login="admin",
            )
