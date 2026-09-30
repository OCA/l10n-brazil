# (c) 2014 Kmee - Rafael da Silva Lima <rafael.lima@kmee.com.br>
# (c) 2014 Kmee - Matheus Felix <matheus.felix@kmee.com.br>
# (c) 2016 KMEE Informática - Daniel Sadamo <daniel.sadamo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class HrVersion(models.Model):
    _inherit = "hr.version"

    @api.model
    def _get_marital_status_selection(self):
        return super()._get_marital_status_selection() + [
            ("common_law_marriage", self.env._("Common law marriage")),
            ("separated", self.env._("Separated")),
        ]
