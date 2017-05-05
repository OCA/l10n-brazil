# -*- coding: utf-8 -*-
# Copyright (C) 2017 - Daniel Sadamo - KMEE INFORMATICA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import fields, models
from openerp.addons.l10n_br_account_product.models.product import \
    PRODUCT_ORIGIN

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

PRODUCT_TYPE = [
    ('product', u'Produto'),
    ('service', u'Serviço')
]

TYPE = [
    ('receipt', u'Receita'),
    ('tax', u'Imposto'),
    ('client', u'Cliente')
]


class AccountMoveTemplate(models.Model):
    _name = 'account.move.template'


    company_id = fields.Many2one(
        comodel_name='res.company',
    )

    fiscal_category_ids = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string=u'Categoria da operação',
    )


class AccountMoveLineTemplate(models.Model):
    _name = 'account.move.line.template'
    _order = 'sequence asc'

    sequence = fields.Integer(
        string=u'Sequence',
    )

    type = fields.Selection(
        selection=TYPE,
        string=u'Tipo do lançamento'
    )

    product_fiscal_type = fields.Selection(
        selection=PRODUCT_TYPE,
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

    move_template_id = fields.One2many(
        'account.move.template', 'fiscal_category_ids',
    )
