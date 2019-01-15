# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    crc_number = fields.Char(
        string='Número do registro CRC'
    )
