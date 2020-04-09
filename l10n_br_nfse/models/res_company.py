# -*- coding: utf-8 -*-
# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _

PROCESSADOR = 'erpbrasil_edoc'


class ResCompany(models.Model):

    _inherit = 'res.company'
    processador_edoc = fields.Selection(
        selection_add=[(PROCESSADOR, 'erpbrasil.edoc')]
    )
