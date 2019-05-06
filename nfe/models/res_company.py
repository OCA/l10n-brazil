# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

from .constants.nfe import (
    NFE_VERSIONS,
    NFE_VERSION,
    NFE_ENVIRONMENTS,
    NFE_ENVIRONMENT)


class ResCompany(models.Model):
    _inherit = 'res.company'

    nfe_version = fields.Selection(
        selection=NFE_VERSIONS,
        string='NFe Version',
        required=True,
        default=NFE_VERSION)

    nfe_environment = fields.Selection(
        selection=NFE_ENVIRONMENTS,
        string='NFe Environment',
        default=NFE_ENVIRONMENT)
