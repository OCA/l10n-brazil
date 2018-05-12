# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

TYPE = [
    ('input', u'Entrada'),
    ('output', u'Saída'),
]

PRODUCT_FISCAL_TYPE = [
    ('service', u'Serviço'),
]

PRODUCT_FISCAL_TYPE_DEFAULT = None


class L10nBrAccountFiscalCategory(models.Model):
    """Fiscal Category to apply fiscal and account parameters in documents."""
    _name = 'l10n_br_account.fiscal.category'
    _description = 'Categoria Fiscal'

    code = fields.Char(
        string=u'Código',
        size=254,
        required=True)

    name = fields.Char(
        string=u'Descrição',
        size=254,
        help="Natureza da operação informada no XML")

    type = fields.Selection(
        selection=TYPE,
        string='Tipo',
        default='output')

    fiscal_type = fields.Selection(
        selection=PRODUCT_FISCAL_TYPE,
        string='Tipo Fiscal',
        default=PRODUCT_FISCAL_TYPE_DEFAULT)

    property_journal = fields.Many2one(
        comodel_name='account.journal',
        string=u"Diário Contábil",
        company_dependent=True,
        help=u"Diário utilizado para esta categoria de operação fiscal")

    journal_type = fields.Selection(
        selection=[('sale', u'Saída'),
                   ('sale_refund', u'Devolução de Saída'),
                   ('purchase', u'Entrada'),
                   ('purchase_refund', u'Devolução de Entrada')],
        string=u'Tipo do Diário',
        size=32,
        required=True,
        default='sale')

    refund_fiscal_category_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string=u'Categoria Fiscal de Devolução',
        domain="[('type', '!=', type), ('fiscal_type', '=', fiscal_type),"
               "('journal_type', 'like', journal_type),"
               "('state', '=', 'approved')]")

    reverse_fiscal_category_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string=u'Categoria Fiscal Inversa',
        domain="[('type', '!=', type), ('fiscal_type', '=', fiscal_type),"
               "('state', '=', 'approved')]")

    fiscal_position_ids = fields.One2many(
        comodel_name='account.fiscal.position',
        inverse_name='fiscal_category_id',
        string=u'Posições Fiscais')

    note = fields.Text(
        string=u'Observações')

    state = fields.Selection(
        selection=[('draft', u'Rascunho'),
                   ('review', u'Revisão'),
                   ('approved', u'Aprovada'),
                   ('unapproved', u'Não Aprovada')],
        string='Status',
        readonly=True,
        track_visibility='onchange',
        index=True,
        default='draft')

    _sql_constraints = [
        ('l10n_br_account_fiscal_category_code_uniq', 'unique (code)',
         u'Já existe uma categoria fiscal com esse código!')
    ]

    @api.multi
    def action_unapproved_draft(self):
        """Set state to draft and create a new workflow instance"""
        self.write({'state': 'draft'})
        self.delete_workflow()
        self.create_workflow()
        return True

    @api.multi
    def onchange_journal_type(self, journal_type):
        """Clear property_journal"""
        return {'value': {'property_journal': None}}
