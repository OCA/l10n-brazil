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


class ImportDeclaration(models.Model):
    _name = 'l10n_br_account_product.import.declaration'

    invoice_line_id = fields.Many2one(
        'account.invoice.line', u'Linha de Documento Fiscal',
        ondelete='cascade', select=True)
    name = fields.Char(u'Número da DI', size=10, required=True)
    date_registration = fields.Date(u'Data de Registro', required=True)
    exporting_code = fields.Char(
        u'Código do Exportador', required=True, size=60)
    state_id = fields.Many2one(
        'res.country.state', u'Estado',
        domain="[('country_id.code', '=', 'BR')]")
    location = fields.Char(u'Local', required=True, size=60)
    date_release = fields.Date(u'Data de Liberação', required=True)
    type_transportation = fields.Selection([
        ('1', u'1 - Marítima'),
        ('2', u'2 - Fluvial'),
        ('3', u'3 - Lacustre'),
        ('4', u'4 - Aérea'),
        ('5', u'5 - Postal'),
        ('6', u'6 - Ferroviária'),
        ('7', u'7 - Rodoviária'),
        ('8', u'8 - Conduto / Rede Transmissão'),
        ('9', u'9 - Meios Próprios'),
        ('10', u'10 - Entrada / Saída ficta'),
    ], u'Transporte Internacional')
    afrmm_value = fields.Float(
        'Valor da AFRMM', digits=dp.get_precision('Account'), default=0.00)
    type_import = fields.Selection([
        ('1', u'1 - Importação por conta própria'),
        ('2', u'2 - Importação por conta e ordem'),
        ('3', u'3 - Importação por encomenda'),
    ], u'Tipo de Importação', default='1')
    thirdparty_cnpj = fields.Char('CNPJ', size=18)
    thirdparty_state_id = fields.Many2one(
        'res.country.state', u'Estado',
        domain="[('country_id.code', '=', 'BR')]")
    line_ids = fields.One2many(
        'l10n_br_account_product.import.declaration.line',
        'import_declaration_id', 'Linhas da DI')

    @api.multi
    def onchange_mask_cnpj_cpf(self, thirdparty_cnpj):
        result = {'value': {}}
        if thirdparty_cnpj:
            val = re.sub('[^0-9]', '', thirdparty_cnpj)
            if len(val) == 14:
                thirdparty_cnpj = "%s.%s.%s/%s-%s"\
                    % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
        result['value'].update({'thirdparty_cnpj': thirdparty_cnpj})
        return result


class ImportDeclarationLine(models.Model):
    _name = 'l10n_br_account_product.import.declaration.line'

    import_declaration_id = fields.Many2one(
        'l10n_br_account_product.import.declaration', u'DI',
        ondelete='cascade', select=True)
    sequence = fields.Integer(u'Sequência', default=1, required=True)
    name = fields.Char(u'Adição', size=3, required=True)
    manufacturer_code = fields.Char(
        u'Código do Fabricante', size=60, required=True)
    amount_discount = fields.Float(u'Valor',
                                   digits=dp.get_precision('Account'),
                                   default=0.00)


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
