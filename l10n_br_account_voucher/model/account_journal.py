# -*- coding: utf-8 -*-
# (c) 2016 Kmee - Fernando Marcato
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    automatic_conciliation = fields.Boolean('Efetuar baixa automaticamente')
    conciliation_journal = fields.Many2one(
        'account.journal', 'Diário de Baixa')
