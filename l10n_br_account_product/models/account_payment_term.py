# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    indPag = fields.Selection(
        [('0', u'Pagamento à Vista'), ('1', u'Pagamento à Prazo'),
         ('2', 'Outros')], 'Indicador de Pagamento', default='1')
