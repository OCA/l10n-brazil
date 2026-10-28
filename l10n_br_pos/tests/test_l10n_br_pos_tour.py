# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import odoo.tests


@odoo.tests.tagged("post_install", "-at_install")
class TestL10nBrPosTour(odoo.tests.HttpCase):
    def test_l10n_br_pos_tour(self):
        admin = self.env.ref("base.user_admin")
        config = self.env.ref("l10n_br_pos.pos_config_presumido")
        admin.write(
            {
                "company_ids": [(4, config.company_id.id)],
                "company_id": config.company_id.id,
            }
        )
        # Other fiscal modules may turn this demo config into an NFC-e one.
        config.simplified_document_type_id = self.env.ref("l10n_br_fiscal.document_59")
        config.with_user(admin).open_ui()
        self.start_tour(
            f"/pos/ui?config_id={config.id}", "l10n_br_pos_tour", login="admin"
        )
