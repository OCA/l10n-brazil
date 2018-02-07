# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import re

from openerp import models, fields, api


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
