# Copyright (C) KMEE 2023
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

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
