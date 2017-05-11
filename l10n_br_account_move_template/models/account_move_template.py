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

# OPERATION_PURPOSE = [
#     ('operacional', u'Operacional'),
#     ('financeiro', u'Financeiro'),
# ]


TYPE = [
    ('receipt', u'Receita'),
    ('tax', u'Imposto'),
    # ('client', u'Cliente')
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
    move_template_ids = fields.One2many(
        'account.move.line.template',
        inverse_name='template_id',
    )

    @api.constrains('fiscal_category_ids')
    def _constraints_fiscal_categories(self):
        for category in self.fiscal_category_ids:
            if len(category.move_template_ids) >= 2:
                raise Warning(u'A categoria %s já tem roteiro' %category.name)

    # @api.onchange('fiscal_category_ids')
    # def _compute_tem_account_template(self):
    #     for category in self.env['l10n_br_account.fiscal.category'].search([]):
    #         if category in self.fiscal_category_ids:
    #             print "true"
    #             category.write({'tem_account_template': True})
    #         else:
    #             print 'False'
    #             category.write({'tem_account_template': False})


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
    # TODO: qual a melhor forma de estruturar?
    # operation_purpose = fields.Selection(selection=OPERATION_PURPOSE)
    # account_move_type = fields.Selection(selection=MOVE_TYPE)
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

    # tem_account_template = fields.Boolean(
    #     string=u'Tem account template?',
    #     # compute='_compute_tem_account_template',
    #     # store=True,
    # )

    # @api.depends('move_template_ids.fiscal_category_ids')
    # def _compute_tem_account_template(self):
    #     for category in self:
    #         if category.move_template_ids and len(category.move_template_ids)\
    #                 > 0:
    #             print "true"
    #             category.tem_account_template = True
    #         else:
    #             print 'False'
    #             category.tem_account_template = False
