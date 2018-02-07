# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api, _

from openerp.addons.l10n_br_account.models.l10n_br_account import TYPE


class L10nbrAccountCFOP(models.Model):
    """CFOP - Código Fiscal de Operações e Prestações"""
    _name = 'l10n_br_account_product.cfop'
    _description = 'CFOP'

    code = fields.Char(u'Código', size=4, required=True)
    name = fields.Char('Nome', size=256, required=True)
    small_name = fields.Char('Nome Reduzido', size=32, required=True)
    description = fields.Text(u'Descrição')
    type = fields.Selection(TYPE, 'Tipo', required=True)
    parent_id = fields.Many2one(
        'l10n_br_account_product.cfop', 'CFOP Pai')
    child_ids = fields.One2many(
        'l10n_br_account_product.cfop', 'parent_id', 'CFOP Filhos')
    internal_type = fields.Selection(
        [('view', u'Visualização'), ('normal', 'Normal')],
        'Tipo Interno', required=True, default='normal')
    id_dest = fields.Selection(
        [('1', u'Operação interna'),
         ('2', u'Operação interestadual'),
         ('3', u'Operação com exterior')],
        u'Local de destino da operação',
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

    # TODO migrate
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'code'], context,
                          load='_classic_write')
        return [(x['id'], (x['code'] and x['code'] or '') +
                 (x['name'] and ' - ' + x['name'] or '')) for x in reads]
