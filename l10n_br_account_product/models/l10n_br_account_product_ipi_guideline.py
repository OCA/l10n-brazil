# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class L10nBrIPIGuideline(models.Model):

    _name = 'l10n_br_account_product.ipi_guideline'
    _description = 'IPI Guidelines'

    code = fields.Char(u'Código', size=3, required=True)
    name = fields.Text(u'Descrição Enquadramento Legal do IPI', required=True)
    cst_group = fields.Selection([('imunidade', u'Imunidade'),
                                  ('suspensao', u'Suspensão'),
                                  ('isencao', u'Isenção'),
                                  ('reducao', u'Redução'),
                                  ('outros', u'Outros'),
                                  ], string='Grupo CST', required=True)
    tax_code_in_id = fields.Many2one(
        'account.tax.code.template', string=u'CST Entrada')
    tax_code_out_id = fields.Many2one(
        'account.tax.code.template', string=u'CST Saída')
