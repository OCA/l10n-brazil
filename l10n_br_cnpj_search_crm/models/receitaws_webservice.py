# Copyright 2022 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ReceitawsWebserviceCRM(models.AbstractModel):
    _inherit = "l10n_br_cnpj_search.webservice.abstract"

    @api.model
    def _receitaws_import_data(self, data):
        res = super()._receitaws_import_data(data)
        keys_to_remove = ["email", "legal_nature", "equity_capital"]
        for key in keys_to_remove:
            res.pop(key, None)
        return res
