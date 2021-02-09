# Copyright 2017 KMEE INFORMATICA LTDA
#   Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)


from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    l10n_br_pos_config_id = fields.Many2one(
        string="Terminal POS",
        comodel_name="l10n_br_fiscal.pos_config",
    )
