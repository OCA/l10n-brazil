# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import re

from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError
from openerp.addons import decimal_precision as dp

from openerp.addons.l10n_br_base.tools import fiscal
from openerp.addons.l10n_br_account.models.l10n_br_account import TYPE

PRODUCT_FISCAL_TYPE = [
    ('product', 'Produto')
]

PRODUCT_FISCAL_TYPE_DEFAULT = PRODUCT_FISCAL_TYPE[0][0]

NFE_IND_IE_DEST = [
    ('1', '1 - Contribuinte do ICMS'),
    ('2', '2 - Contribuinte Isento do ICMS'),
    ('9', '9 - Não Contribuinte')
]

NFE_IND_IE_DEST_DEFAULT = NFE_IND_IE_DEST[0][0]


class L10nBrIcmsRelief(models.Model):

    _name = 'l10n_br_account_product.icms_relief'
    _description = 'Icms Relief'

    code = fields.Char(u'Código', size=2, required=True)
    name = fields.Char('Nome', size=256, required=True)
    active = fields.Boolean('Ativo', default=True)


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


class L10nBrTaxIcmsPartition(models.Model):

    _name = 'l10n_br_tax.icms_partition'
    _description = 'Icms Partition'

    date_start = fields.Date(
        u'Data Inicial',
        required=True
    )
    date_end = fields.Date(
        u'Data Final',
        required=True
    )
    rate = fields.Float(
        u'Percentual Interestadual de Rateio',
        required=True
    )


class L10nBrAccountProductCest(models.Model):

    _name = 'l10n_br_account_product.cest'

    code = fields.Char(
        u'Código',
        size=9
    )
    name = fields.Char(
        u'Nome'
    )
    segment = fields.Char(
        u'Segmento',
        size=32
    )
    item = fields.Char(
        u'Item',
        size=4
    )

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
        result = []
        for cest in self:
            name = cest.code + ' - ' + cest.name
            result.append((cest.id, name))
        return result
