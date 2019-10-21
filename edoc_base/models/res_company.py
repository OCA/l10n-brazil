# -*- coding: utf-8 -*-
# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class ResCompany(models.Model):

    _inherit = 'res.company'

    processador_edoc = fields.Selection(
        selection=[],
        string=u'Processador documentos eletrônicos',
    )
