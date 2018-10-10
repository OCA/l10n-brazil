# -*- coding: utf-8 -*-
# Copyright (C) 2018 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields

class AccountTaxGroup(models.Model):

    _inherit = 'account.tax.group'

    domain = fields.Selection(
        selection=[('icms', 'ICMS'),
                   ('icmsst', 'ICMS ST'),
                   ('icmsfcp', 'ICMS FCP'),
                   ('icmsinter', 'ICMS Inter'),
                   ('ipi', 'IPI'),
                   ('cofins', 'COFINS'),
                   ('pis', 'PIS'),
                   ('issqn', 'ISSQN'),
                   ('irpf', 'IRPF'),
                   ('irpj', 'IRPJ'),
                   ('ii', 'II'),
                   ('csll', 'CSLL'),
                   ('other', 'Outra')],
        string='Tax Domain')
