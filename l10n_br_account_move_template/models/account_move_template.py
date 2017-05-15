# -*- coding: utf-8 -*-
# Copyright (C) 2017 - Daniel Sadamo - KMEE INFORMATICA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models
from openerp.addons.l10n_br_account_product.models.product import \
    PRODUCT_ORIGIN
from openerp.addons.l10n_br_account_product.models.l10n_br_account_product \
    import PRODUCT_FISCAL_TYPE

TERM = [
    ('curto', 'Curto prazo'),
    ('longo', 'Longo prazo')
]

OPERATION_DESTINATION = [
    ('1', u'Operação interna'),
    ('2', u'Operação interestadual'),
    ('3', u'Operação com exterior')
]

TYPE = [
    ('receipt', u'Receita'),
    ('tax', u'Imposto'),
    ('cost', u'Custo')
]


class AccountMoveTemplate(models.Model):
    _name = 'account.move.template'


    company_id = fields.Many2one(
        comodel_name='res.company',
    )

    fiscal_category_ids = fields.Many2many(
        'l10n_br_account.fiscal.category',
        'account_move_template_fiscal_category',
        'template_id',
        'category_id',
        string=u'Categoria da operação',
        # domain="[('tem_account_template', '=', False)]",
    )
    use_cost = fields.Boolean(
        default=False,
        string=u'Usar custo'
    )
    move_template_ids = fields.One2many(
        'account.move.line.template',
        inverse_name='template_id',
    )

    purchase_installed = fields.Boolean(
        compute='compute_purchase',
        default=False,
    )

    def compute_purchase(self):
        is_installed = self.env['ir.module.module'].search(['&', ('state', '=',
                                                                  'installed'),
                                                            ('name', '=',
                                                             'purchase')])
        if is_installed:
            self.purchase_installed = True

    @api.constrains('fiscal_category_ids')
    def _constraints_fiscal_categories(self):
        for category in self.fiscal_category_ids:
            if len(category.move_template_ids) >= 2:
                raise Warning(u'A categoria %s já tem roteiro' % category.name)


class AccountMoveLineTemplate(models.Model):
    _name = 'account.move.line.template'
    _order = 'sequence asc'

    sequence = fields.Integer(
        string=u'Sequence',
    )

    template_id = fields.Many2one(
        comodel_name='account.move.template',
        required=True,
        ondelete='cascade',
    )

    type = fields.Selection(
        selection=TYPE,
        string=u'Tipo do lançamento'
    )

    product_fiscal_type = fields.Selection(
        selection=PRODUCT_FISCAL_TYPE,
        selection_add=[('service', u'Serviço')],
        string=u'Tipo fiscal do produto'
    )
    product_origin = fields.Selection(
        selection=PRODUCT_ORIGIN,
        string=u'Origem do produto'
    )
    term = fields.Selection(selection=TERM)
    credit_account_id = fields.Many2one(
        comodel_name='account.account', string=u'Conta de credito'
    )
    debit_account_id = fields.Many2one(
        comodel_name='account.account', string=u'Conta de debito'
    )
    debit_compensation_account_id = fields.Many2one(
        comodel_name='account.account', string=u'Conta de compensaçao de '
                                               u'debito'
    )


class L10nBrAccountFiscalCategory(models.Model):
    _inherit = 'l10n_br_account.fiscal.category'
    _description = 'Categoria Fiscal'

    move_template_ids = fields.Many2many(
        'account.move.template',
        'account_move_template_fiscal_category',
        'category_id',
        'template_id',
        string=u'Modelos de contabilização',
    )
