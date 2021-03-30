# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class Cfop(models.Model):
    _inherit = 'l10n_br_fiscal.cfop'
    _nfe_search_keys = ['code', 'code_unmasked']
