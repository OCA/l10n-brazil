# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
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

from l10n_br_base.tools import fiscal
from openerp.osv import orm, fields


class l10n_br_account_cfop(orm.Model):
    """ CFOP - Código Fiscal de Operações e Prestações """
    _name = 'l10n_br_account.cfop'
    _description = 'CFOP'
    _columns = {
        'code': fields.char(u'Código', size=4, required=True),
        'name': fields.char('Nome', size=256, required=True),
        'small_name': fields.char('Nome Reduzido', size=32, required=True),
        'description': fields.text(u'Descrição'),
        'type': fields.selection(
            [('input', 'Entrada'), ('output', u'Saída')], 'Tipo',
            required=True),
        'parent_id': fields.many2one('l10n_br_account.cfop', 'CFOP Pai'),
        'child_ids': fields.one2many(
            'l10n_br_account.cfop', 'parent_id', 'CFOP Filhos'),
        'internal_type': fields.selection(
            [('view', u'Visualização'), ('normal', 'Normal')],
            'Tipo Interno', required=True),
    }
    _defaults = {
        'internal_type': 'normal',
    }

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


class l10n_br_account_service_type(orm.Model):
    _name = 'l10n_br_account.service.type'
    _description = u'Cadastro de Operações Fiscais de Serviço'
    _columns = {
        'code': fields.char(u'Código', size=16, required=True),
        'name': fields.char(u'Descrição', size=256, required=True),
        'parent_id': fields.many2one(
            'l10n_br_account.service.type', 'Tipo de Serviço Pai'),
        'child_ids': fields.one2many(
            'l10n_br_account.service.type', 'parent_id',
            u'Tipo de Serviço Filhos'),
        'internal_type': fields.selection(
            [('view', u'Visualização'), ('normal', 'Normal')],
            'Tipo Interno', required=True),
    }
    _defaults = {
        'internal_type': 'normal'
    }

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        reads = self.read(cr, uid, ids, ['name', 'code'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['code']:
                name = record['code'] + ' - ' + name
            res.append((record['id'], name))
        return res


class l10n_br_account_fiscal_document(orm.Model):
    _name = 'l10n_br_account.fiscal.document'
    _description = 'Tipo de Documento Fiscal'
    _columns = {
        'code': fields.char(u'Codigo', size=8, required=True),
        'name': fields.char(u'Descrição', size=64),
        'electronic': fields.boolean(u'Eletrônico')
    }


class l10n_br_account_fiscal_category(orm.Model):
    _name = 'l10n_br_account.fiscal.category'
    _description = 'Categoria Fiscail'
    _columns = {
        'code': fields.char(u'Código', size=254, required=True),
        'name': fields.char(u'Descrição', size=254),
        'type': fields.selection(
            [('input', 'Entrada'), ('output', u'Saída')], 'Tipo'),
        'property_journal': fields.property(
            'account.journal', type='many2one', relation='account.journal',
            string=u"Diário Contábil", method=True, view_load=True,
            help=u"Diário utilizado para esta categoria de operação fiscal"),
        'fiscal_type': fields.selection(
            [('product', 'Produto'), ('service', u'Serviço')],
            'Tipo Fiscal', required=True),
        'journal_type': fields.selection(
            [('sale', 'Venda'), ('sale_refund', u'Devolução de Venda'),
            ('purchase', 'Compras'),
            ('purchase_refund', u'Devolução de Compras')], u'Tipo do Diário',
            size=32, required=True),
        'refund_fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category',
            u'Categoria Fiscal de Devolução',
            domain="[('type', '!=', type), ('fiscal_type', '=', fiscal_type), "
            "('journal_type', 'like', journal_type)]"),
        'fiscal_position_ids': fields.one2many('account.fiscal.position',
                                               'fiscal_category_id',
                                               u'Posições Fiscais'),
        'note': fields.text(u'Observações')
    }
    _defaults = {
        'type': 'output',
        'fiscal_type': 'product',
        'journal_type': 'sale'
    }


class l10n_br_account_document_serie(orm.Model):
    _name = 'l10n_br_account.document.serie'
    _description = 'Serie de documentos fiscais'
    _columns = {
        'code': fields.char(u'Código', size=3, required=True),
        'name': fields.char(u'Descrição', size=64, required=True),
        'fiscal_document_id': fields.many2one(
            'l10n_br_account.fiscal.document',
            'Documento Fiscal', required=True),
        'company_id': fields.many2one('res.company', 'Empresa',
                                      required=True),
        'active': fields.boolean('Ativo'),
        'fiscal_type': fields.selection([('product', 'Produto'),
                                         ('service', u'Serviço')],
                                        'Tipo Fiscal', required=True),
        'internal_sequence_id': fields.many2one('ir.sequence',
                                                u'Sequência Interna')
    }
    _defaults = {
        'active': True,
        'fiscal_type': 'product'
    }

    def create_sequence(self, cr, uid, vals, context=None):
        """ Create new no_gap entry sequence for every
         new document serie """
        seq = {
            'name': vals['name'],
            'implementation': 'no_gap',
            'padding': 1,
            'number_increment': 1}
        if 'company_id' in vals:
            seq['company_id'] = vals['company_id']
        return self.pool.get('ir.sequence').create(cr, uid, seq)

    def create(self, cr, uid, vals, context=None):
        """ Overwrite method to create a new ir.sequence if
         this field is null """
        if not 'internal_sequence_id' in vals or \
        not vals['internal_sequence_id']:
            vals.update({'internal_sequence_id': self.create_sequence(
                cr, uid, vals, context)})
        return super(l10n_br_account_document_serie, self).create(
            cr, uid, vals, context)


class l10n_br_account_invoice_invalid_number(orm.Model):
    _name = 'l10n_br_account.invoice.invalid.number'
    _description = u'Inutilização de Faixa de Numeração'

    def _name_get(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for record in self.browse(cr, uid, ids, context):
            result[record.id] = record.fiscal_document_id.name + ' (' + \
            record.document_serie_id.name + '): ' + \
            str(record.number_start) + ' - ' + str(record.number_end)
        return result

    _columns = {
        'name': fields.function(
            _name_get, method=True, type="char",
            size=64, string="Nome"),
        'company_id': fields.many2one(
            'res.company', 'Empresa', readonly=True,
            states={'draft': [('readonly', False)]}, required=True),
        'fiscal_document_id': fields.many2one(
            'l10n_br_account.fiscal.document', 'Documento Fiscal',
            readonly=True, states={'draft': [('readonly', False)]},
            required=True),
        'document_serie_id': fields.many2one(
            'l10n_br_account.document.serie', u'Série',
            domain="[('fiscal_document_id', '=', fiscal_document_id), "
            "('company_id', '=', company_id)]", readonly=True,
            states={'draft': [('readonly', False)]}, required=True),
        'number_start': fields.integer(
            u'Número Inicial', readonly=True,
            states={'draft': [('readonly', False)]}, required=True),
        'number_end': fields.integer(
            u'Número Final', readonly=True,
            states={'draft': [('readonly', False)]}, required=True),
        'state': fields.selection(
            [('draft', 'Rascunho'), ('cancel', 'Cancelado'),
            ('done', u'Concluído')], 'Status', required=True),
        'justificative': fields.char('Justificativa', size=255,
            readonly=True, states={'draft': [('readonly', False)]}, required=True),        
    }
    _defaults = {
        'state': 'draft',
        'company_id': lambda self, cr, uid,
            c: self.pool.get('res.company')._company_default_get(
                cr, uid, 'account.invoice', context=c)
    }
    _sql_constraints = [
        ('number_uniq',
         'unique(document_serie_id, number_start, number_end, state)',
         u'Sequência existente!'),
    ]

    def _check_justificative(self, cr,uid, ids):
        for invalid in self.browse(cr, uid, ids):
            if len(invalid.justificative) < 15:return  False
        return True

    def _check_range(self, cursor, user, ids, context=None):
        for invalid_number in self.browse(cursor, user, ids, context=context):
            where = []
            if invalid_number.number_start:
                where.append("((number_end>='%s') or (number_end is null))" % (
                    invalid_number.number_start,))
            if invalid_number.number_end:
                where.append("((number_start<='%s') or (number_start is null))" % (invalid_number.number_end,))

            cursor.execute('SELECT id ' \
                    'FROM l10n_br_account_invoice_invalid_number ' \
                    'WHERE '+' and '.join(where) + (where and ' and ' or '') +
                        'document_serie_id = %s ' \
                        "AND state = 'done'" \
                        'AND id <> %s' % (invalid_number.document_serie_id.id, invalid_number.id))
            if cursor.fetchall() or (invalid_number.number_start > invalid_number.number_end):
                return False
        return True

    _constraints = [
        (_check_range, u'Não é permitido faixas sobrepostas!',
            ['number_start', 'number_end']),
        (_check_justificative,'Justificativa deve ter tamanho minimo de 15 caracteres.', ['justificative'])
    ]

    def action_draft_done(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'done'})
        return True

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invalid_numbers = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for invalid_number in invalid_numbers:
            if invalid_number['state'] in ('draft'):
                unlink_ids.append(invalid_number['id'])
            else:
                raise orm.except_orm(
                    (u'Ação Inválida!'),
                    (u'Você não pode excluir uma sequência concluída.'))
        orm.Model.unlink(self, cr, uid, unlink_ids, context=context)
        return True


class l10n_br_account_partner_fiscal_type(orm.Model):
    _name = 'l10n_br_account.partner.fiscal.type'
    _description = 'Tipo Fiscal de Parceiros'
    _columns = {
        'code': fields.char(u'Código', size=16, required=True),
        'name': fields.char(u'Descrição', size=64),
        'is_company': fields.boolean('Pessoa Juridica?'),
        'icms': fields.boolean('Recupera ICMS'),
        'ipi': fields.boolean('Recupera IPI')
    }


class l10n_br_account_cnae(orm.Model):
    _name = 'l10n_br_account.cnae'
    _description = 'Cadastro de CNAE'
    _columns = {
        'code': fields.char(u'Código', size=16, required=True),
        'name': fields.char(u'Descrição', size=64, required=True),
        'version': fields.char(u'Versão', size=16, required=True),
        'parent_id': fields.many2one('l10n_br_account.cnae', 'CNAE Pai'),
        'child_ids': fields.one2many(
            'l10n_br_account.cnae', 'parent_id', 'CNAEs Filhos'),
        'internal_type': fields.selection(
            [('view', u'Visualização'), ('normal', 'Normal')],
            'Tipo Interno', required=True),
    }
    _defaults = {
        'internal_type': 'normal'
    }

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        reads = self.read(cr, uid, ids, ['name', 'code'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['code']:
                name = record['code'] + ' - ' + name
            res.append((record['id'], name))
        return res


class l10n_br_tax_definition_template(orm.Model):
    _name = 'l10n_br_tax.definition.template'
    _columns = {
        'tax_id': fields.many2one(
            'account.tax.template', 'Imposto', required=True),
        'tax_domain': fields.related(
            'tax_id', 'domain', type='char'),
        'tax_code_id': fields.many2one(
            'account.tax.code.template', u'Código de Imposto')}

    def onchange_tax_id(self, cr, uid, ids, tax_id=False, context=None):
        tax_domain = False
        if tax_id:
            tax_domain = self.pool.get('account.tax').read(
                cr, uid, tax_id, ['domain'], context=context)['domain']
        return {'value': {'tax_domain': tax_domain}}


class l10n_br_tax_definition(orm.Model):
    _name = 'l10n_br_tax.definition'
    _columns = {
        'tax_id': fields.many2one('account.tax', 'Imposto', required=True),
        'tax_domain': fields.related('tax_id', 'domain',
                                     type='char'),
        'tax_code_id': fields.many2one(
            'account.tax.code', u'Código de Imposto'),
        'company_id': fields.related(
            'tax_id', 'company_id', type='many2one', readonly=True,
            relation='res.company', store=True, string='Empresa'),
    }

    def onchange_tax_id(self, cr, uid, ids, tax_id=False, context=None):
        tax_domain = False
        if tax_id:
            tax_domain = self.pool.get('account.tax').read(
                cr, uid, tax_id, ['domain'], context=context)['domain']
        return {'value': {'tax_domain': tax_domain}}


class l10n_br_account_document_related(orm.Model):
    _name = 'l10n_br_account.document.related'
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
        'cpfcpnj_type': fields.selection(
            [('cpf', 'CPF'), ('cnpj', 'CNPJ')], 'Tipo Doc.'),
        'inscr_est': fields.char('Inscr. Estadual/RG', size=16),
        'date': fields.date('Data'),
        'fiscal_document_id': fields.many2one(
            'l10n_br_account.fiscal.document', 'Documento'),
    }
    _defaults = {
        'cpfcpnj_type': 'cnpj',
    }

    def _check_cnpj_cpf(self, cr, uid, ids):

        for inv_related in self.browse(cr, uid, ids):
            if not inv_related.cnpj_cpf:
                continue

            if inv_related.cpfcpnj_type == 'cnpj':
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
            result['value']['cpfcpnj_type'] = False
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
                result['value']['cpfcpnj_type'] = 'cnpj'
            else:
                result['value']['cpfcpnj_type'] = 'cpf'

            result['value']['date'] = inv_related.date_invoice
            result['value']['fiscal_document_id'] = inv_related.fiscal_document_id and \
            inv_related.fiscal_document_id.id or False

        if inv_related.fiscal_document_id.code == '04':
            result['value']['inscr_est'] = inv_related.partner_id and \
            inv_related.partner_id.inscr_est or False

        return result

    def onchange_mask_cnpj_cpf(self, cr, uid, ids, cpfcpnj_type, cnpj_cpf,
                            context=None):
        result = {'value': {}}
        if cnpj_cpf:
            val = re.sub('[^0-9]', '', cnpj_cpf)
            if cpfcpnj_type == 'cnpj' and len(val) == 14:
                cnpj_cpf = "%s.%s.%s/%s-%s"\
                % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
            elif cpfcpnj_type == 'cpf' and len(val) == 11:
                cnpj_cpf = "%s.%s.%s-%s"\
                % (val[0:3], val[3:6], val[6:9], val[9:11])
            result['value'].update({'cnpj_cpf': cnpj_cpf})
        return result
