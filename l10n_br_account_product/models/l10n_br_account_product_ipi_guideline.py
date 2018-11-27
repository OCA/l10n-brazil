# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class L10nBrIPIGuideline(models.Model):
    _name = 'l10n_br_account_product.ipi_guideline'
    _description = 'IPI Guidelines'

    code = fields.Char(
        string=u'Código',
        size=3,
        required=True)

    name = fields.Text(
        string=u'Descrição Enquadramento Legal do IPI',
        required=True)

    cst_group = fields.Selection(
        selection=[('imunidade', u'Imunidade'),
                   ('suspensao', u'Suspensão'),
                   ('isencao', u'Isenção'),
                   ('reducao', u'Redução'),
                   ('outros', u'Outros')],
        string='Grupo CST',
        required=True)

    cst_in_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cst',
        string=u'CST Entrada')

    cst_out_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cst',
        string=u'CST Saída')
