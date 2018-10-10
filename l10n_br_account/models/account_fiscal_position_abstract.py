# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, api

from .l10n_br_account import TYPE


class AccountFiscalPositionAbstract(object):

    fiscal_category_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string=u'Categoria Fiscal')

    type = fields.Selection(
        selection=TYPE,
        related='fiscal_category_id.type',
        readonly=True,
        store=True,
        string=u'Fiscal Type')

    inv_copy_note = fields.Boolean(
        string=u'Copiar Observação na Nota Fiscal')

    asset_operation = fields.Boolean(
        string=u'Operação de Aquisição de Ativo',
        help=u"Caso seja marcada essa opção, será "
             "incluido o IPI na base de calculo do ICMS.")

    state = fields.Selection(
        selection=[('draft', u'Rascunho'),
                   ('review', u'Revisão'),
                   ('approved', u'Aprovada'),
                   ('unapproved', u'Não Aprovada')],
        string=u'Status',
        readonly=True,
        track_visibility='onchange',
        index=True,
        default='draft')


class AccountFiscalPositionTaxAbstract(object):

    tax_group_id = fields.Many2one(
        comodel_name='account.tax.group',
        string=u'Grupo de Impostos',
    )

    @api.onchange('tax_src_id',
                  'tax_group_id',
                  'position_id')
    def _onchange_tax_group(self):
        type_tax_use = {'input': 'purchase', 'output': 'sale'}
        domain = []

        if self.position_id.type:
            domain = [('type_tax_use', '=',
                      (type_tax_use.get(self.position_id.type)))]

        if self.tax_group_id:
            domain.append(('tax_group_id', '=', self.tax_group_id.id))

        if self.tax_src_id:
            domain.append(('tax_group_id', '=',
                           self.tax_src_id.tax_group_id.id))

        return {'domain': {'tax_dest_id': domain, 'tax_src_id': domain}}
