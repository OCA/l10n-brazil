# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009 - TODAY Renato Lima - Akretion                           #
# Copyright (C) 2014  KMEE - www.kmee.com.br
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

import datetime

from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError

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

    # TODO nome de campos devem ser em ingles
    invoice_id = fields.Many2one('account.invoice', 'Fatura')
    motivo = fields.Text('Motivo', readonly=True, required=True)
    sequencia = fields.Char(
        'Sequencia', help=u"Indica a sequencia da carta de correcão")
    cce_document_event_ids = fields.One2many(
        'l10n_br_account.document_event', 'document_event_ids', u'Eventos')


class L10n_brAccountInvoiceCancel(models.Model):
    _name = 'l10n_br_account.invoice.cancel'
    _description = u'Cancelar Documento Eletrônico no Sefaz'

    invoice_id = fields.Many2one('account.invoice', 'Fatura')
    justificative = fields.Char(
        'Justificativa', size=255, readonly=True, required=True,
        states={'draft': [('readonly', False)]})
    cancel_document_event_ids = fields.One2many(
        'l10n_br_account.document_event', 'cancel_document_event_id',
        u'Eventos')
    state = fields.Selection(
        [('draft', 'Rascunho'), ('cancel', 'Cancelado'),
         ('done', u'Concluído')], 'Status', required=True, default='draft')

    def _check_justificative(self, cr, uid, ids):
        for invalid in self.browse(cr, uid, ids):
            if len(invalid.justificative) < 15:
                return False
        return True

    _constraints = [(
        _check_justificative,
        'Justificativa deve ter tamanho minimo de 15 caracteres.',
        ['justificative'])]

    def action_draft_done(self):
        self.write({'state': 'done'})
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
         ('13', u'Manifestação'), ], 'Serviço')
    response = fields.Char(u'Descrição', size=64, readonly=True)
    company_id = fields.Many2one(
        'res.company', 'Empresa', readonly=True,
        states={'draft': [('readonly', False)]})
    origin = fields.Char(
        'Documento de Origem', size=64,
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
    cancel_document_event_id = fields.Many2one(
        'l10n_br_account.invoice.cancel', 'Cancelamento')
    invalid_number_document_event_id = fields.Many2one(
        'l10n_br_account.invoice.invalid.number', u'Inutilização')

    _order = 'write_date desc'

    @api.multi
    def set_done(self):
        self.write({'state': 'done', 'end_date': datetime.datetime.now()})
        return True


class L10n_brAccountFiscalCategory(models.Model):
    """Fiscal Category to apply fiscal and account parameters in documents."""
    _name = 'l10n_br_account.fiscal.category'
    _description = 'Categoria Fiscal'

    code = fields.Char(u'Código', size=254, required=True)
    name = fields.Char(u'Descrição', size=254)
    type = fields.Selection(TYPE, 'Tipo', default='output')
    fiscal_type = fields.Selection(
        PRODUCT_FISCAL_TYPE, 'Tipo Fiscal',
        default=PRODUCT_FISCAL_TYPE_DEFAULT)
    property_journal = fields.Many2one(
        'account.journal', string=u"Diário Contábil", company_dependent=True,
        help=u"Diário utilizado para esta categoria de operação fiscal")
    journal_type = fields.Selection(
        [('sale', u'Saída'), ('sale_refund', u'Devolução de Saída'),
         ('purchase', u'Entrada'),
         ('purchase_refund', u'Devolução de Entrada')], u'Tipo do Diário',
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
    fiscal_position_ids = fields.One2many(
        'account.fiscal.position',
        'fiscal_category_id', string=u'Posições Fiscais')
    note = fields.Text(u'Observações')
    state = fields.Selection(
        [('draft', u'Rascunho'),
         ('review', u'Revisão'), ('approved', u'Aprovada'),
         ('unapproved', u'Não Aprovada')],
        'Status', readonly=True,
        track_visibility='onchange', select=True, default='draft')

    _sql_constraints = [
        ('l10n_br_account_fiscal_category_code_uniq', 'unique (code)',
         u'Já existe uma categoria fiscal com esse código !')
    ]

    @api.multi
    def action_unapproved_draft(self):
        """Set state to draft and create a new workflow instance"""
        self.write({'state': 'draft'})
        self.delete_workflow()
        self.create_workflow()
        return True

    @api.multi
    def onchange_journal_type(self, journal_type):
        """Clear property_journal"""
        return {'value': {'property_journal': None}}


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
        [('view', u'Visualização'), ('normal', 'Normal')], 'Tipo Interno',
        required=True, default='normal')

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record['name']
            if record['code']:
                name = record['code'] + ' - ' + name
            result.append((record['id'], name))
        return result


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

    name = fields.Char(u'Descrição', required=True)

    active = fields.Boolean('Ativo')

    fiscal_type = fields.Selection(PRODUCT_FISCAL_TYPE, 'Tipo Fiscal',
                                   default=PRODUCT_FISCAL_TYPE_DEFAULT)

    fiscal_document_id = fields.Many2one('l10n_br_account.fiscal.document',
                                         'Documento Fiscal', required=True)

    company_id = fields.Many2one('res.company', 'Empresa',
                                 required=True)

    internal_sequence_id = fields.Many2one('ir.sequence',
                                           u'Sequência Interna')

    @api.model
    def _create_sequence(self, vals):
        """ Create new no_gap entry sequence for every
         new document serie """
        seq = {
            'name': vals['name'],
            'implementation': 'no_gap',
            'padding': 1,
            'number_increment': 1}
        if 'company_id' in vals:
            seq['company_id'] = vals['company_id']
        return self.env['ir.sequence'].create(seq).id

    @api.model
    def create(self, vals):
        """ Overwrite method to create a new ir.sequence if
         this field is null """
        if not vals.get('internal_sequence_id'):
            vals.update({'internal_sequence_id': self._create_sequence(vals)})
        return super(L10n_brAccountDocumentSerie, self).create(vals)


class L10n_brAccountInvoiceInvalidNumber(models.Model):
    _name = 'l10n_br_account.invoice.invalid.number'
    _description = u'Inutilização de Faixa de Numeração'

    @api.multi
    def name_get(self):
        return [(rec.id,
                 u"{0} ({1}): {2} - {3}".format(
                     rec.fiscal_document_id.name,
                     rec.document_serie_id.name,
                     rec.number_start, rec.number_end)
                 ) for rec in self]

    company_id = fields.Many2one(
        'res.company', 'Empresa', readonly=True,
        states={'draft': [('readonly', False)]}, required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'l10n_br_account.invoice.invalid.number'))

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

    justificative = fields.Char(
        'Justificativa', size=255, readonly=True,
        states={'draft': [('readonly', False)]}, required=True)

    invalid_number_document_event_ids = fields.One2many(
        'l10n_br_account.document_event', 'invalid_number_document_event_id',
        u'Eventos', states={'done': [('readonly', True)]})

    _sql_constraints = [
        ('number_uniq',
         'unique(document_serie_id, number_start, number_end, state)',
         u'Sequência existente!'),
    ]

    @api.one
    @api.constrains('justificative')
    def _check_justificative(self):
        if len(self.justificative) < 15:
            raise UserError(
                _('Justificativa deve ter tamanho minimo de 15 caracteres.'))
        return True

    @api.one
    @api.constrains('number_start', 'number_end')
    def _check_range(self):
        where = []
        if self.number_start:
            where.append("((number_end>='%s') or (number_end is null))" % (
                self.number_start,))
        if self.number_end:
            where.append(
                "((number_start<='%s') or (number_start is null))" % (
                    self.number_end,))

        self._cr.execute(
            'SELECT id \
            FROM l10n_br_account_invoice_invalid_number \
            WHERE ' + ' and '.join(where) + (where and ' and ' or '') +
            "document_serie_id = %s \
            AND state = 'done' \
            AND id <> %s" % (self.document_serie_id.id, self.id))
        if self._cr.fetchall() or (self.number_start > self.number_end):
            raise UserError(_(u'Não é permitido faixas sobrepostas!'))
        return True

    _constraints = [
        (_check_range, u'Não é permitido faixas sobrepostas!',
            ['number_start', 'number_end']),
        (_check_justificative,
            'Justificativa deve ter tamanho minimo de 15 caracteres.',
            ['justificative'])
    ]

    def action_draft_done(self):
        self.write({'state': 'done'})
        return True

    @api.multi
    def unlink(self):
        unlink_ids = []
        for invalid_number in self:
            if invalid_number['state'] in ('draft'):
                unlink_ids.append(invalid_number['id'])
            else:
                raise UserError(_(
                    u'Você não pode excluir uma sequência concluída.'))
        return super(L10n_brAccountInvoiceInvalidNumber, self).unlink()


class L10n_brAccountPartnerFiscalType(models.Model):
    _name = 'l10n_br_account.partner.fiscal.type'
    _description = 'Tipo Fiscal de Parceiros'

    code = fields.Char(u'Código', size=16, required=True)

    name = fields.Char(u'Descrição', size=64)

    is_company = fields.Boolean('Pessoa Juridica?')

    default = fields.Boolean(u'Tipo Fiscal Padrão', default=True)

    icms = fields.Boolean('Recupera ICMS')

    ipi = fields.Boolean('Recupera IPI')

    @api.one
    @api.constrains('default')
    def _check_default(self):
        if self.default:
            if len(self.search([('default', '=', 'True')])) > 1:
                raise UserError(_(u'Mantenha apenas um tipo fiscal padrão!'))
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

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record['name']
            if record['code']:
                name = record['code'] + ' - ' + name
            result.append((record['id'], name))
        return result


class L10n_brTaxDefinitionTemplate(object):
    _name = 'l10n_br_tax.definition.template'

    tax_template_id = fields.Many2one('account.tax.template', u'Imposto',
                                      required=True)

    tax_domain = fields.Char('Tax Domain', related='tax_template_id.domain',
                             store=True)

    tax_code_template_id = fields.Many2one('account.tax.code.template',
                                           u'Código de Imposto')


class L10n_brTaxDefinition(object):
    _name = 'l10n_br_tax.definition'

    tax_id = fields.Many2one('account.tax', string='Imposto', required=True)

    tax_domain = fields.Char('Tax Domain', related='tax_id.domain',
                             store=True)

    tax_code_id = fields.Many2one('account.tax.code', u'Código de Imposto')

    company_id = fields.Many2one('res.company', string='Company',
                                 related='tax_id.company_id',
                                 store=True, readonly=True)


class AccountInvoiceTax(models.Model):

    _inherit = "account.invoice.tax"
    
    deduction_account_id = fields.Many2one('account.account','Tax Account for Deduction')
    
     
    @api.v8
    def compute(self, invoice):
        result = super(AccountInvoiceTax,self).compute(invoice)
        for line in invoice.invoice_line:
            taxes = line.invoice_line_tax_id.compute_all(
                (line.price_unit * (1 - (line.discount or 0.0) / 100.0)),
                line.quantity, line.product_id, invoice.partner_id)['taxes']
            for tax in taxes:
                key = (tax['tax_code_id'], tax['base_code_id'], tax['account_collected_id'] or line.account_id.id)
                if key in result.keys():
                    if invoice.type in ('out_invoice','in_invoice'):
                        result[key]['deduction_account_id'] = tax.get('account_deduced_id',False)
                    else:
                        result[key]['deduction_account_id'] = tax.get('account_paid_deduced_id',False)
        return result
     
    @api.v7
    def compute(self, cr, uid, invoice_id, context=None):
        recs = self.browse(cr, uid, [], context)
        invoice = recs.env['account.invoice'].browse(invoice_id)
        return recs.compute(invoice)
    
    @api.model
    #create counterpart credit tax
    def move_line_get(self, invoice_id):
        res = super(AccountInvoiceTax, self).move_line_get(invoice_id)
        inv = self.env['account.invoice'].browse(invoice_id)
        self._cr.execute(
            'SELECT * FROM account_invoice_tax WHERE invoice_id = %s',
            (invoice_id,)
        )
        for row in self._cr.dictfetchall():
            if row['amount'] and row['tax_code_id'] and row['tax_amount'] and row['deduction_account_id']:
                res.append({
                    'type': 'tax',
                    'name': row['name'],
                    'price_unit': row['amount'],
                    'quantity': 1,
                    'price': -row['amount'] or 0.0,
                    'account_id': row['deduction_account_id'],
                    'tax_code_id': False,
                    'tax_amount': False,
                    'account_analytic_id': row['account_analytic_id'],
                })
        return res