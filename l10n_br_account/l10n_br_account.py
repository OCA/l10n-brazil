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

from openerp.osv import orm, fields
from openerp import netsvc
import datetime

TYPE = [
    ('input', 'Entrada'),
    ('output', u'Saída'),
]

PRODUCT_FISCAL_TYPE = [
    ('service', u'Serviço'),
]

PRODUCT_FISCAL_TYPE_DEFAULT = PRODUCT_FISCAL_TYPE[0][0]


class L10n_brAccountInvoiceCancel(orm.Model):
    _name = 'l10n_br_account.invoice.cancel'
    _description = u'Cancelar Documento Eletrônico no Sefaz'
    _columns = {
        'invoice_id': fields.many2one(
            'account.invoice', 'Fatura'),
        'justificative': fields.char('Justificativa', size=255, readonly=True,
            states={'draft': [('readonly', False)]}, required=True),
        'cancel_document_event_ids': fields.one2many(
            'l10n_br_account.document_event', 'document_event_ids', u'Eventos'),
        'state': fields.selection(
            [('draft', 'Rascunho'), ('cancel', 'Cancelado'),
            ('done', u'Concluído')], 'Status', required=True),
    }
    _defaults = {
        'state': 'draft',
    }

    def _check_justificative(self, cr, uid, ids):
        for invalid in self.browse(cr, uid, ids):
            if len(invalid.justificative) < 15:
                return False
        return True

    _constraints = [(
        _check_justificative,
        'Justificativa deve ter tamanho minimo de 15 caracteres.',
        ['justificative'])]

    def action_draft_done(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'done'})
        return True


class L10n_brDocumentEvent(orm.Model):
    _name = 'l10n_br_account.document_event'
    _columns = {
        'type': fields.selection(
            [('-1', u'Exception'),
            ('0', u'Envio Lote'),
            ('1', u'Consulta Recibo'),
            ('2', u'Cancelamento'),
            ('3', u'Inutilização'),
            ('4', u'Consulta NFE'),
            ('5', u'Consulta Situação'),
            ('6', u'Consulta Cadastro'),
            ('7', u'DPEC Recepção'),
            ('8', u'DPEC Consulta'),
            ('9', u'Recepção Evento'),
            ('10', u'Download'),
            ('11', u'Consulta Destinadas'), ], 'Serviço'),
        'response': fields.char(u'Descrição', size=64, readonly=True),
        'company_id': fields.many2one(
            'res.company', 'Empresa', readonly=True,
            states={'draft': [('readonly', False)]}),
        'origin': fields.char('Documento de Origem', size=64,
            readonly=True, states={'draft': [('readonly', False)]},
            help="Reference of the document that produced event."),
        'file_sent': fields.char('Envio', readonly=True),
        'file_returned': fields.char('Retorno', readonly=True),
        'status': fields.char('Codigo', readonly=True),
        'message': fields.char('Mensagem', readonly=True),
        'create_date': fields.datetime(u'Data Criação', readonly=True),
        'write_date': fields.datetime(u'Data Alteração', readonly=True),
        'end_date': fields.datetime(u'Data Finalização', readonly=True),
        'state': fields.selection(
            [('draft', 'Rascunho'), ('send', 'Enviado'),
            ('wait', 'Aguardando Retorno'), ('done', 'Recebido Retorno')],
            'Status', select=True, readonly=True),
        'document_event_ids': fields.many2one(
            'account.invoice', 'Documentos', ondelete='cascade')
    }
    _defaults = {
        'state': 'draft',
    }

    def set_done(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        self.write(cr, uid, ids,
            {'state': 'done', 'end_date': datetime.datetime.now()},
            context=context)
        return True


class L10n_brAccountFiscalCategory(orm.Model):
    _name = 'l10n_br_account.fiscal.category'
    _description = 'Categoria Fiscal'
    _columns = {
        'code': fields.char(u'Código', size=254, required=True),
        'name': fields.char(u'Descrição', size=254),
        'type': fields.selection(TYPE, 'Tipo'),
        'fiscal_type': fields.selection(PRODUCT_FISCAL_TYPE, 'Tipo Fiscal'),
        'property_journal': fields.property(
            'account.journal', type='many2one', relation='account.journal',
            string=u"Diário Contábil", method=True, view_load=True,
            help=u"Diário utilizado para esta categoria de operação fiscal"),
        'journal_type': fields.selection(
            [('sale', 'Venda'), ('sale_refund', u'Devolução de Venda'),
            ('purchase', 'Compras'),
            ('purchase_refund', u'Devolução de Compras')], u'Tipo do Diário',
            size=32, required=True),
        'refund_fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', u'Categoria Fiscal de Devolução',
            domain="""[('type', '!=', type), ('fiscal_type', '=', fiscal_type),
                ('journal_type', 'like', journal_type),
                ('state', '=', 'approved')]"""),
        'reverse_fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', u'Categoria Fiscal Inversa',
            domain="""[('type', '!=', type), ('fiscal_type', '=', fiscal_type),
                ('state', '=', 'approved')]"""),
        'fiscal_position_ids': fields.one2many('account.fiscal.position',
            'fiscal_category_id', u'Posições Fiscais'),
        'note': fields.text(u'Observações'),
        'state': fields.selection([('draft', u'Rascunho'),
            ('review', u'Revisão'), ('approved', u'Aprovada'),
            ('unapproved', u'Não Aprovada')], 'Status', readonly=True,
            track_visibility='onchange', select=True),
    }
    _defaults = {
        'state': 'draft',
        'type': 'output',
        'fiscal_type': PRODUCT_FISCAL_TYPE_DEFAULT,
        'journal_type': 'sale',
    }
    _sql_constraints = [
        ('l10n_br_account_fiscal_category_code_uniq', 'unique (code)',
         u'Já existe uma categoria fiscal com esse código !')
    ]

    def action_unapproved_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'draft'})
        wf_service = netsvc.LocalService("workflow")
        for fc_id in ids:
            wf_service.trg_delete(
                uid, 'l10n_br_account.fiscal.category', fc_id, cr)
            wf_service.trg_create(
                uid, 'l10n_br_account.fiscal.category', fc_id, cr)
        return True


class L10n_brAccountServiceType(orm.Model):
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


class L10n_brAccountFiscalDocument(orm.Model):
    _name = 'l10n_br_account.fiscal.document'
    _description = 'Tipo de Documento Fiscal'
    _columns = {
        'code': fields.char(u'Codigo', size=8, required=True),
        'name': fields.char(u'Descrição', size=64),
        'electronic': fields.boolean(u'Eletrônico')
    }


class L10n_brAccountDocumentSerie(orm.Model):
    _name = 'l10n_br_account.document.serie'
    _description = 'Serie de documentos fiscais'
    _columns = {
        'code': fields.char(u'Código', size=3, required=True),
        'name': fields.char(u'Descrição', size=64, required=True),
        'fiscal_type': fields.selection(PRODUCT_FISCAL_TYPE, 'Tipo Fiscal'),
        'fiscal_document_id': fields.many2one(
            'l10n_br_account.fiscal.document',
            'Documento Fiscal', required=True),
        'company_id': fields.many2one(
            'res.company', 'Empresa', required=True),
        'active': fields.boolean('Ativo'),
        'internal_sequence_id': fields.many2one(
            'ir.sequence', u'Sequência Interna')
    }
    _defaults = {
        'active': True,
        'fiscal_type': PRODUCT_FISCAL_TYPE_DEFAULT,
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
        result = super(L10n_brAccountDocumentSerie, self).create(
            cr, uid, vals, context)
        if result:
            company = self.pool.get('res.company').browse(
                cr, uid, vals.get('company_id'), context=context)
            value = {}
            if vals.get('fiscal_type') == 'product':
                series = [doc_serie.id for doc_serie in
                    company.document_serie_product_ids]
                series.append(result)
                value = {
                    'document_serie_product_ids': [(6, 0, list(set(series)))]}
            else:
                value = {'document_serie_service_id': result}
            self.pool.get('res.company').write(
                cr, uid, vals.get('company_id'), value, context=context)
        return result


class L10n_brAccountInvoiceInvalidNumber(orm.Model):
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
            readonly=True, states={'draft': [('readonly', False)]},
            required=True),
        'invalid_number_document_event_ids': fields.one2many(
            'l10n_br_account.document_event', 'document_event_ids',
            u'Eventos'),
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

    def _check_justificative(self, cr, uid, ids):
        for invalid in self.browse(cr, uid, ids):
            if len(invalid.justificative) < 15:
                return False
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


class L10n_brAccountPartnerFiscalType(orm.Model):
    _name = 'l10n_br_account.partner.fiscal.type'
    _description = 'Tipo Fiscal de Parceiros'
    _columns = {
        'code': fields.char(u'Código', size=16, required=True),
        'name': fields.char(u'Descrição', size=64),
        'is_company': fields.boolean('Pessoa Juridica?'),
        'icms': fields.boolean('Recupera ICMS'),
        'ipi': fields.boolean('Recupera IPI')
    }


class L10n_brAccountCNAE(orm.Model):
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


class L10n_brTaxDefinitionTemplate(orm.Model):
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


class L10n_brTaxDefinition(orm.Model):
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
