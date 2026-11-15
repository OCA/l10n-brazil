# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _load_pos_data_fields(self, config_id):
        return super()._load_pos_data_fields(config_id) + [
            "is_anonymous_consumer",
            "l10n_br_ie_code",
            "legal_name",
            "street_number",
            "district",
            "city_id",
        ]
