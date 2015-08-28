# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
# Copyright (C) 2014  KMEE - www.kmee.com.br                                  #
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

from openerp import api, models, fields, _
from openerp import netsvc
import datetime

TYPE = [
    ('input', u'Entrada'),
    ('output', u'Saída'),
]

PRODUCT_FISCAL_TYPE = [
    ('service', u'Serviço'),
]

PRODUCT_FISCAL_TYPE_DEFAULT = PRODUCT_FISCAL_TYPE[0][0]


class L10n_brAccountCce(models.Model):
    _name = 'l10n_br_account.invoice.cce'
    _description = u'Cartão de Correção no Sefaz'

    invoice_id = fields.Many2one(
        'account.invoice', 'Fatura')
    motivo = fields.Text('Motivo', readonly=True
        , required=True)
    sequencia = fields.Char('Sequencia', help=u"Indica a sequencia da carta de correcão")
    cce_document_event_ids = fields.One2many(
        'l10n_br_account.document_event', 'document_event_ids', u'Eventos')

class L10n_brAccountInvoiceCancel(models.Model):
    _name = 'l10n_br_account.invoice.cancel'
    _description = u'Cancelar Documento Eletrônico no Sefaz'

    invoice_id = fields.Many2one(
        'account.invoice', 'Fatura')
    justificative = fields.Char('Justificativa', size=255, readonly=True,
        states={'draft': [('readonly', False)]}, required=True)
    cancel_document_event_ids = fields.One2many(
        'l10n_br_account.document_event', 'document_event_ids', u'Eventos')
    state = fields.Selection(
        [('draft', 'Rascunho'), ('cancel', 'Cancelado'),
        ('done', u'Concluído')], 'Status', required=True)

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


class L10n_brDocumentEvent(models.Model):
    _name = 'l10n_br_account.document_event'

    type = fields.Selection(
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
        ('11', u'Consulta Destinadas'),
        ('12', u'Distribuição DFe'),
        ('13', u'Manifestação')], 'Serviço')
    response = fields.Char(u'Descrição', size=64, readonly=True)
    company_id = fields.Many2one(
        'res.company', 'Empresa', readonly=True,
        states={'draft': [('readonly', False)]})
    origin = fields.Char('Documento de Origem', size=64,
        readonly=True, states={'draft': [('readonly', False)]},
        help="Reference of the document that produced event.")
    file_sent = fields.Char('Envio', readonly=True)
    file_returned = fields.Char('Retorno', readonly=True)
    status = fields.Char('Codigo', readonly=True)
    message = fields.Char('Mensagem', readonly=True)
    create_date = fields.Datetime(u'Data Criação', readonly=True)
    write_date = fields.Datetime(u'Data Alteração', readonly=True)
    end_date = fields.Datetime(u'Data Finalização', readonly=True)
    state = fields.Selection(
        [('draft', 'Rascunho'), ('send', 'Enviado'),
        ('wait', 'Aguardando Retorno'), ('done', 'Recebido Retorno')],
        'Status', select=True, readonly=True, default='draft')
    document_event_ids = fields.Many2one(
        'account.invoice', 'Documentos')

    _order = "write_date desc"

    def set_done(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        self.write(cr, uid, ids,
            {'state': 'done', 'end_date': datetime.datetime.now()},
            context=context)
        return True


class L10n_brAccountFiscalCategory(models.Model):
    _name = 'l10n_br_account.fiscal.category'
    _description = 'Categoria Fiscal'

    code = fields.Char(u'Código', size=254, required=True)
    name = fields.Char(u'Descrição', size=254)
    type = fields.Selection(TYPE, string='Tipo', default='output')
    fiscal_type = fields.Selection(PRODUCT_FISCAL_TYPE, 'Tipo Fiscal',
                                   default=PRODUCT_FISCAL_TYPE_DEFAULT)
    property_journal = fields.Many2one('account.journal',
        string=u"Diário Contábil", method=True, company_dependent=True,
        help=u"Diário utilizado para esta categoria de operação fiscal")
    journal_type = fields.Selection(
        [('sale', 'Venda'), ('sale_refund', u'Devolução de Venda'),
        ('purchase', 'Compras'),
        ('purchase_refund', u'Devolução de Compras')], u'Tipo do Diário',
        size=32, required=True, default='sale')
    refund_fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', u'Categoria Fiscal de Devolução',
        domain="""[('type', '!=', type), ('fiscal_type', '=', fiscal_type),
            ('journal_type', 'like', journal_type),
            ('state', '=', 'approved')]""")
    reverse_fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', u'Categoria Fiscal Inversa',
        domain="""[('type', '!=', type), ('fiscal_type', '=', fiscal_type),
            ('state', '=', 'approved')]""")
    fiscal_position_ids = fields.One2many('account.fiscal.position',
        'fiscal_category_id', u'Posições Fiscais')
    note = fields.Text(u'Observações')
    state = fields.Selection([('draft', u'Rascunho'),
        ('review', u'Revisão'), ('approved', u'Aprovada'),
        ('unapproved', u'Não Aprovada')], 'Status', readonly=True,
        track_visibility='onchange', select=True, default='draft')

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


class L10n_brAccountServiceType(models.Model):
    _name = 'l10n_br_account.service.type'
    _description = u'Cadastro de Operações Fiscais de Serviço'

    code = fields.Char(u'Código', size=16, required=True)
    name = fields.Char(u'Descrição', size=256, required=True)
    parent_id = fields.Many2one(
        'l10n_br_account.service.type', 'Tipo de Serviço Pai')
    child_ids = fields.One2many(
        'l10n_br_account.service.type', 'parent_id',
        u'Tipo de Serviço Filhos')
    internal_type = fields.Selection(
        [('view', u'Visualização'), ('normal', 'Normal')],
        'Tipo Interno', required=True, default='normal')

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


class L10n_brAccountFiscalDocument(models.Model):
    _name = 'l10n_br_account.fiscal.document'
    _description = 'Tipo de Documento Fiscal'

    code = fields.Char(u'Codigo', size=8, required=True)
    name = fields.Char(u'Descrição', size=64)
    electronic = fields.Boolean(u'Eletrônico')


class L10n_brAccountDocumentSerie(models.Model):
    _name = 'l10n_br_account.document.serie'
    _description = 'Serie de documentos fiscais'

    code = fields.Char(u'Código', size=3, required=True)
    name = fields.Char(u'Descrição', size=64, required=True)
    fiscal_type = fields.Selection(PRODUCT_FISCAL_TYPE, 'Tipo Fiscal',
                                   default=PRODUCT_FISCAL_TYPE_DEFAULT)
    fiscal_document_id = fields.Many2one(
        'l10n_br_account.fiscal.document',
        'Documento Fiscal', required=True)
    company_id = fields.Many2one(
        'res.company', 'Empresa', required=True)
    active = fields.Boolean('Ativo', default=True)
    internal_sequence_id = fields.Many2one(
        'ir.sequence', u'Sequência Interna')

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


class L10n_brAccountInvoiceInvalidNumber(models.Model):
    _name = 'l10n_br_account.invoice.invalid.number'
    _description = u'Inutilização de Faixa de Numeração'

    company_id = fields.Many2one(
        'res.company', 'Empresa', readonly=True,
        states={'draft': [('readonly', False)]}, required=True,
        default=lambda self : self.env['res.company']._company_default_get(
            'account.invoice')
        )
    fiscal_document_id = fields.Many2one(
        'l10n_br_account.fiscal.document', 'Documento Fiscal',
        readonly=True, states={'draft': [('readonly', False)]},
        required=True)
    document_serie_id = fields.Many2one(
        'l10n_br_account.document.serie', u'Série',
        domain="[('fiscal_document_id', '=', fiscal_document_id), "
        "('company_id', '=', company_id)]", readonly=True,
        states={'draft': [('readonly', False)]}, required=True)
    number_start = fields.Integer(
        u'Número Inicial', readonly=True,
        states={'draft': [('readonly', False)]}, required=True)
    number_end = fields.Integer(
        u'Número Final', readonly=True,
        states={'draft': [('readonly', False)]}, required=True)
    state = fields.Selection(
        [('draft', 'Rascunho'), ('cancel', 'Cancelado'),
        ('done', u'Concluído')], 'Status', required=True, default='draft')
    justificative = fields.Char('Justificativa', size=255,
        readonly=True, states={'draft': [('readonly', False)]},
        required=True)
    invalid_number_document_event_ids = fields.One2many(
        'l10n_br_account.document_event', 'document_event_ids',
        u'Eventos')

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
        models.Model.unlink(self, cr, uid, unlink_ids, context=context)
        return True


class L10n_brAccountPartnerFiscalType(models.Model):
    _name = 'l10n_br_account.partner.fiscal.type'
    _description = 'Tipo Fiscal de Parceiros'

    code = fields.Char(u'Código', size=16, required=True)
    name = fields.Char(u'Descrição', size=64)
    is_company = fields.Boolean(string='Pessoa Juridica?')
    default = fields.Boolean(u'Tipo Fiscal Padrão',
                             help="Tipo padrão utilizado ao se registrar um novo parceiro!")
    icms = fields.Boolean('Recupera ICMS')
    ipi = fields.Boolean('Recupera IPI')

    @api.one
    @api.constrains('default')
    def _check_default(self):
        if self.default:
            if len(self.search([('default', '=', 'True')])) > 1:
                raise Warning(_(u'Mantenha apenas um tipo fiscal padrão!'))
        return True

class L10n_brAccountCNAE(models.Model):
    _name = 'l10n_br_account.cnae'
    _description = 'Cadastro de CNAE'

    code = fields.Char(u'Código', size=16, required=True)
    name = fields.Char(u'Descrição', size=64, required=True)
    version = fields.Char(u'Versão', size=16, required=True)
    parent_id = fields.Many2one('l10n_br_account.cnae', 'CNAE Pai')
    child_ids = fields.One2many(
        'l10n_br_account.cnae', 'parent_id', 'CNAEs Filhos')
    internal_type = fields.Selection(
        [('view', u'Visualização'), ('normal', 'Normal')],
        'Tipo Interno', required=True, default='normal')

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


class L10n_brTaxDefinitionTemplate(models.Model):
    _name = 'l10n_br_tax.definition.template'

    tax_id = fields.Many2one(
        'account.tax.template', 'Imposto', required=True)
    tax_domain = fields.Char(related='tax_id.domain')
    tax_code_id = fields.Many2one(
        'account.tax.code.template', u'Código de Imposto')

    def onchange_tax_id(self, cr, uid, ids, tax_id=False, context=None):
        tax_domain = False
        if tax_id:
            tax_domain = self.pool.get('account.tax').read(
                cr, uid, tax_id, ['domain'], context=context)['domain']
        return {'value': {'tax_domain': tax_domain}}


class L10n_brTaxDefinition(models.Model):
    _name = 'l10n_br_tax.definition'

    tax_id = fields.Many2one('account.tax', 'Imposto', required=True)
    tax_domain = fields.Char(related='tax_id.domain')
    tax_code_id = fields.Many2one(
        'account.tax.code', u'Código de Imposto')
    company_id = fields.Many2one(
        related='tax_id.company_id', readonly=True,
        store=True, string='Empresa')

    def onchange_tax_id(self, cr, uid, ids, tax_id=False, context=None):
        tax_domain = False
        if tax_id:
            tax_domain = self.pool.get('account.tax').read(
                cr, uid, tax_id, ['domain'], context=context)['domain']
        return {'value': {'tax_domain': tax_domain}}
