# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    revenue_expense = fields.Boolean(
        string=u'Gera Financeiro'
    )
