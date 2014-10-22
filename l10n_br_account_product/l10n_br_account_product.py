# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

import re

from openerp.osv import orm, fields

from l10n_br_base.tools import fiscal
from openerp.addons import decimal_precision as dp
from openerp.addons.l10n_br_account.l10n_br_account import TYPE

PRODUCT_FISCAL_TYPE = [
    ('product', 'Produto')
]

PRODUCT_FISCAL_TYPE_DEFAULT = PRODUCT_FISCAL_TYPE[0][0]


class L10n_brAccountCFOP(orm.Model):
    """CFOP - Código Fiscal de Operações e Prestações"""
    _name = 'l10n_br_account_product.cfop'
    _description = 'CFOP'
    _columns = {
        'code': fields.char(u'Código', size=4, required=True),
        'name': fields.char('Nome', size=256, required=True),
        'small_name': fields.char('Nome Reduzido', size=32, required=True),
        'description': fields.text(u'Descrição'),
        'type': fields.selection(TYPE, 'Tipo', required=True),
        'parent_id': fields.many2one(
            'l10n_br_account_product.cfop', 'CFOP Pai'),
        'child_ids': fields.one2many(
            'l10n_br_account_product.cfop', 'parent_id', 'CFOP Filhos'),
        'internal_type': fields.selection(
            [('view', u'Visualização'), ('normal', 'Normal')],
            'Tipo Interno', required=True),
    }
    _defaults = {
        'internal_type': 'normal',
    }
    _sql_constraints = [
        ('l10n_br_account_cfop_code_uniq', 'unique (code)',
         u'Já existe um CFOP com esse código !')
    ]

    def name_search(self, cr, user, name, args=None, operator='ilike',
                    context=None, limit=80):
        if not args:
            args = []
        if context is None:
            context = {}
        ids = self.search(cr, user, ['|', ('name', operator, name),
                                     ('code', operator, name)] + args,
                          limit=limit, context=context)
        return self.name_get(cr, user, ids, context)

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'code'], context,
                          load='_classic_write')
        return [(x['id'], (x['code'] and x['code'] or '') +
                 (x['name'] and ' - ' + x['name'] or '')) for x in reads]


class L10n_brAccountDocumentRelated(orm.Model):
    _name = 'l10n_br_account_product.document.related'
    _columns = {
        'invoice_id': fields.many2one(
            'account.invoice', 'Documento Fiscal',
            ondelete='cascade', select=True),
        'invoice_related_id': fields.many2one(
            'account.invoice', 'Documento Fiscal',
            ondelete='cascade', select=True),
        'document_type': fields.selection(
            [('nf', 'NF'), ('nfe', 'NF-e'), ('cte', 'CT-e'),
                ('nfrural', 'NF Produtor'), ('cf', 'Cupom Fiscal')],
            'Tipo Documento', required=True),
        'access_key': fields.char('Chave de Acesso', size=44),
        'serie': fields.char(u'Série', size=12),
        'internal_number': fields.char(u'Número', size=32),
        'state_id': fields.many2one(
            'res.country.state', 'Estado',
            domain="[('country_id.code', '=', 'BR')]"),
        'cnpj_cpf': fields.char('CNPJ/CPF', size=18),
        'cpfcnpj_type': fields.selection(
            [('cpf', 'CPF'), ('cnpj', 'CNPJ')], 'Tipo Doc.'),
        'inscr_est': fields.char('Inscr. Estadual/RG', size=16),
        'date': fields.date('Data'),
        'fiscal_document_id': fields.many2one(
            'l10n_br_account.fiscal.document', 'Documento'),
    }
    _defaults = {
        'cpfcnpj_type': 'cnpj',
    }

    def _check_cnpj_cpf(self, cr, uid, ids):

        for inv_related in self.browse(cr, uid, ids):
            if not inv_related.cnpj_cpf:
                continue

            if inv_related.cpfcnpj_type == 'cnpj':
                if not fiscal.validate_cnpj(inv_related.cnpj_cpf):
                    return False
            elif not fiscal.validate_cpf(inv_related.cnpj_cpf):
                    return False

        return True

    def _check_ie(self, cr, uid, ids):
        """Checks if company register number in field insc_est is valid,
        this method call others methods because this validation is State wise

        :Return: True or False.

        :Parameters:
            - 'cr': Database cursor.
            - 'uid': Current user’s ID for security checks.
            - 'ids': List of partner objects IDs.
        """
        for inv_related in self.browse(cr, uid, ids):
            if not inv_related.inscr_est \
            or inv_related.inscr_est == 'ISENTO':
                continue

            uf = inv_related.state_id and \
            inv_related.state_id.code.lower() or ''

            try:
                mod = __import__(
                'l10n_br_base.tools.fiscal', globals(), locals(), 'fiscal')

                validate = getattr(mod, 'validate_ie_%s' % uf)
                if not validate(inv_related.inscr_est):
                    return False
            except AttributeError:
                if not fiscal.validate_ie_param(uf, inv_related.inscr_est):
                    return False

        return True

    _constraints = [
        (_check_cnpj_cpf, u'CNPJ/CPF do documento relacionado é invalido!',
            ['cnpj_cpf']),
        (_check_ie, u'Inscrição Estadual do documento fiscal inválida!',
            ['inscr_est']),
    ]

    def onchange_invoice_related_id(self, cr, uid, ids,
                                    invoice_related_id=False, context=None):
        result = {'value': {}}

        if not invoice_related_id:
            return result

        inv_related = self.pool.get('account.invoice').browse(
            cr, uid, invoice_related_id)

        if not inv_related.fiscal_document_id:
            return result

        if inv_related.fiscal_document_id.code == '01':
            result['value']['document_type'] = 'nf'
        elif inv_related.fiscal_document_id.code == '04':
            result['value']['document_type'] = 'nfrural'
        elif inv_related.fiscal_document_id.code == '55':
            result['value']['document_type'] = 'nfe'
        elif inv_related.fiscal_document_id.code == '57':
            result['value']['document_type'] = 'cte'
        elif inv_related.fiscal_document_id.code in ('2B', '2C', '2D'):
            result['value']['document_type'] = 'cf'
        else:
            result['value']['document_type'] = False

        if inv_related.fiscal_document_id.code in ('55', '57'):
            result['value']['access_key'] = inv_related.nfe_access_key
            result['value']['serie'] = False
            result['value']['serie'] = False
            result['value']['internal_number'] = False
            result['value']['state_id'] = False
            result['value']['cnpj_cpf'] = False
            result['value']['cpfcnpj_type'] = False
            result['value']['date'] = False
            result['value']['fiscal_document_id'] = False
            result['value']['inscr_est'] = False

        if inv_related.fiscal_document_id.code in ('01', '04'):
            result['value']['access_key'] = False
            if inv_related.issuer == '0':
                result['value']['serie'] = inv_related.document_serie_id and \
                inv_related.document_serie_id.code or False
            else:
                result['value']['serie'] = inv_related.vendor_serie

            result['value']['internal_number'] = inv_related.internal_number
            result['value']['state_id'] = inv_related.partner_id and \
            inv_related.partner_id.state_id and \
            inv_related.partner_id.state_id.id or False
            result['value']['cnpj_cpf'] = inv_related.partner_id and \
            inv_related.partner_id.cnpj_cpf or False

            if inv_related.partner_id.is_company:
                result['value']['cpfcnpj_type'] = 'cnpj'
            else:
                result['value']['cpfcnpj_type'] = 'cpf'

            result['value']['date'] = inv_related.date_invoice
            result['value']['fiscal_document_id'] = inv_related.fiscal_document_id and \
            inv_related.fiscal_document_id.id or False

        if inv_related.fiscal_document_id.code == '04':
            result['value']['inscr_est'] = inv_related.partner_id and \
            inv_related.partner_id.inscr_est or False

        return result

    def onchange_mask_cnpj_cpf(self, cr, uid, ids, cpfcnpj_type, cnpj_cpf,
                            context=None):
        result = {'value': {}}
        if cnpj_cpf:
            val = re.sub('[^0-9]', '', cnpj_cpf)
            if cpfcnpj_type == 'cnpj' and len(val) == 14:
                cnpj_cpf = "%s.%s.%s/%s-%s"\
                % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
            elif cpfcnpj_type == 'cpf' and len(val) == 11:
                cnpj_cpf = "%s.%s.%s-%s"\
                % (val[0:3], val[3:6], val[6:9], val[9:11])
            result['value'].update({'cnpj_cpf': cnpj_cpf})
        return result


class ImportDeclaration(orm.Model):
    _name = 'l10n_br_account_product.import.declaration'
    _columns = {
        'invoice_line_id': fields.many2one(
            'account.invoice.line', u'Linha de Documento Fiscal',
            ondelete='cascade', select=True),
        'name': fields.char(u'Número da DI', size=10, required=True),
        'date_registration': fields.date(u'Data de Registro', required=True),
        'exporting_code': fields.char(u'Código do Exportador', size=60),
        'state_id': fields.many2one(
        'res.country.state', u'Estado',
            domain="[('country_id.code', '=', 'BR')]"),
        'location': fields.char(u'Local', size=60),
        'date_release': fields.date(u'Data de Liberação'),
        'line_ids': fields.one2many(
            'l10n_br_account_product.import.declaration.line',
            'import_declaration_id', 'Linhas da DI'),
    }


class ImportDeclarationLine(orm.Model):
    _name = 'l10n_br_account_product.import.declaration.line'
    _columns = {
        'import_declaration_id': fields.many2one(
            'l10n_br_account_product.import.declaration', u'DI',
            ondelete='cascade', select=True),
        'sequence': fields.integer(u'Sequência'),
        'name': fields.char(u'Adição', size=3, required=True),
        'manufacturer_code': fields.char(
            u'Código do Fabricante', size=3, required=True),
        'amount_discount': fields.float(u'Valor de Desconto',
            digits_compute=dp.get_precision('Account')),
    }
    _defaults = {
        'amount_discount': 0.00,
    }
