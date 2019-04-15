# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

from odoo.addons.l10n_br_account.models.l10n_br_account import TYPE


class L10nbrAccountCFOP(models.Model):
    """CFOP - Código Fiscal de Operações e Prestações"""
    _name = 'l10n_br_account_product.cfop'
    _description = 'CFOP'

    code = fields.Char(
        string=u'Código',
        size=4,
        required=True)

    name = fields.Char(
        string=u'Nome',
        size=256,
        required=True)

    small_name = fields.Char(
        string=u'Nome Reduzido',
        size=32,
        required=True)

    description = fields.Text(
        string=u'Descrição')

    type = fields.Selection(
        selection=TYPE,
        string=u'Tipo',
        required=True)

    parent_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cfop',
        string=u'CFOP Pai')

    child_ids = fields.One2many(
        comodel_name='l10n_br_account_product.cfop',
        inverse_name='parent_id',
        string=u'CFOP Filhos')

    internal_type = fields.Selection(
        selection=[('view', u'Visualização'),
                   ('normal', 'Normal')],
        string=u'Tipo Interno',
        required=True, default='normal')

    id_dest = fields.Selection(
        selection=[('1', u'Operação interna'),
                   ('2', u'Operação interestadual'),
                   ('3', u'Operação com exterior')],
        string=u'Local de destino da operação',
        help=u'Identificador de local de destino da operação.')

    _sql_constraints = [
        ('l10n_br_account_cfop_code_uniq', 'unique (code)',
         u'Já existe um CFOP com esse código !')
    ]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    @api.multi
    def name_get(self):
        return [(r.id,
                u"{0} - {1}".format(r.code, r.name))
                for r in self]
