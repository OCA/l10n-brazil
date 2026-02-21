# Copyright (C) 2023 KMEE Informatica LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models

from ..constants.dfe import (
    DFE_ENVIRONMENT_DEFAULT,
    DFE_ENVIRONMENTS,
    DFE_VERSION_DEFAULT,
    DFE_VERSIONS,
)


class ResCompany(models.Model):
    _inherit = "res.company"

    dfe_version = fields.Selection(selection=DFE_VERSIONS, default=DFE_VERSION_DEFAULT)

    dfe_environment = fields.Selection(
        selection=DFE_ENVIRONMENTS,
        default=DFE_ENVIRONMENT_DEFAULT,
    )

    last_nsu = fields.Char(string="Last NSU", size=25, default="0")
