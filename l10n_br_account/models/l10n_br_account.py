# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import datetime

from odoo import models, fields, api, _
from odoo.exceptions import Warning as UserError

TYPE = [
    ('input', u'Entrada'),
    ('output', u'Saída'),
]

PRODUCT_FISCAL_TYPE = [
    ('service', u'Serviço'),
]

PRODUCT_FISCAL_TYPE_DEFAULT = None


class L10nBrAccountCce(models.Model):
    _name = 'l10n_br_account.invoice.cce'
    _description = u'Carta de Correção no Sefaz'

    # TODO nome de campos devem ser em ingles
    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string=u'Fatura')

    motivo = fields.Text(
        string=u'Motivo',
        readonly=True,
        required=True)

    sequencia = fields.Char(
        string=u'Sequência',
        help=u"Indica a sequência da carta de correcão")

    cce_document_event_ids = fields.One2many(
        comodel_name='l10n_br_account.document_event',
        inverse_name='document_event_ids',
        string=u'Eventos')

    display_name = fields.Char(
        string='Name',
        compute='_compute_display_name')

    @api.multi
    @api.depends('invoice_id.number', 'invoice_id.partner_id.name')
    def _compute_display_name(self):
        self.ensure_one()
        names = ['Fatura', self.invoice_id.number,
                 self.invoice_id.partner_id.name]
        self.display_name = ' / '.join(filter(None, names))


class L10nBrAccountInvoiceCancel(models.Model):
    _name = 'l10n_br_account.invoice.cancel'
    _description = u'Documento Eletrônico no Sefaz'

    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string=u'Fatura')

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        related='invoice_id.partner_id',
        string='Cliente')

    justificative = fields.Char(
        string='Justificativa',
        size=255,
        readonly=True,
        required=True)

    cancel_document_event_ids = fields.One2many(
        comodel_name='l10n_br_account.document_event',
        inverse_name='cancel_document_event_id',
        string=u'Eventos')

    display_name = fields.Char(
        string=u'Nome',
        compute='_compute_display_name',
    )

    @api.multi
    @api.depends('invoice_id.number', 'invoice_id.partner_id.name')
    def _compute_display_name(self):
        self.ensure_one()
        names = ['Fatura', self.invoice_id.number,
                 self.invoice_id.partner_id.name]
        self.display_name = ' / '.join(filter(None, names))

    @api.multi
    def _check_justificative(self):
        for invalid in self:
            if len(invalid.justificative) < 15:
                return False
        return True

    _constraints = [(
        _check_justificative,
        u'Justificativa deve ter tamanho mínimo de 15 caracteres.',
        ['justificative'])]


class L10nBrDocumentEvent(models.Model):
    _name = 'l10n_br_account.document_event'

    type = fields.Selection(
        selection=[('-1', u'Exception'),
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
                   ('13', u'Manifestação')],
        string='Serviço')

    response = fields.Char(
        string=u'Descrição',
        size=64,
        readonly=True)

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Empresa',
        readonly=True,
        states={'draft': [('readonly', False)]})

    origin = fields.Char(
        string=u'Documento de Origem',
        size=64,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help=u"Referência ao documento que gerou o evento.")

    file_sent = fields.Char(
        string='Envio',
        readonly=True)

    file_returned = fields.Char(
        string='Retorno',
        readonly=True)

    status = fields.Char(
        string=u'Código',
        readonly=True)

    message = fields.Char(
        string=u'Mensagem',
        readonly=True)

    create_date = fields.Datetime(
        string=u'Data Criação',
        readonly=True)

    write_date = fields.Datetime(
        string=u'Data Alteração',
        readonly=True)

    end_date = fields.Datetime(
        string=u'Data Finalização',
        readonly=True)

    state = fields.Selection(
        selection=[('draft', 'Rascunho'),
                   ('send', 'Enviado'),
                   ('wait', 'Aguardando Retorno'),
                   ('done', 'Recebido Retorno')],
        string=u'Status',
        index=True,
        readonly=True,
        default='draft')

    document_event_ids = fields.Many2one(
        comodel_name='account.invoice',
        string=u'Documentos')

    cancel_document_event_id = fields.Many2one(
        comodel_name='l10n_br_account.invoice.cancel',
        string='Cancelamento')

    invalid_number_document_event_id = fields.Many2one(
        comodel_name='l10n_br_account.invoice.invalid.number',
        string=u'Inutilização')

    display_name = fields.Char(
        string='Nome',
        compute='_compute_display_name')

    _order = 'write_date desc'

    @api.multi
    @api.depends('company_id.name', 'origin')
    def _compute_display_name(self):
        self.ensure_one()
        names = ['Evento', self.company_id.name, self.origin]
        self.display_name = ' / '.join(filter(None, names))

    @api.multi
    def set_done(self):
        self.write({'state': 'done',
                    'end_date': datetime.datetime.now()})
        return True


class L10nBrAccountInvoiceInvalidNumber(models.Model):
    _name = 'l10n_br_account.invoice.invalid.number'
    _description = u'Inutilização de Faixa de Numeração'

    @api.multi
    def name_get(self):
        return [(r.id,
                 u"{0} ({1}): {2} - {3}".format(
                     r.fiscal_document_id.name,
                     r.document_serie_id.name,
                     r.number_start, r.number_end)
                 ) for r in self]

    company_id = fields.Many2one(
        comodel_name='res.company',
        string=u'Empresa',
        readonly=True,
        states={'draft': [('readonly', False)]},
        required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'l10n_br_account.invoice.invalid.number'))

    fiscal_document_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.document',
        string=u'Documento Fiscal',
        readonly=True,
        states={'draft': [('readonly', False)]},
        required=True)

    document_serie_id = fields.Many2one(
        comodel_name='l10n_br_account.document.serie',
        string=u'Série',
        readonly=True,
        states={'draft': [('readonly', False)]},
        domain="[('fiscal_document_id', '=', fiscal_document_id), "
               "('company_id', '=', company_id)]",
        required=True)

    number_start = fields.Integer(
        string=u'Número Inicial',
        readonly=True,
        states={'draft': [('readonly', False)]},
        required=True)

    number_end = fields.Integer(
        string=u'Número Final',
        readonly=True,
        states={'draft': [('readonly', False)]},
        required=True)

    state = fields.Selection(
        selection=[('draft', 'Rascunho'),
                   ('cancel', 'Cancelado'),
                   ('done', u'Concluído')],
        string='Status',
        required=True,
        default='draft')

    justificative = fields.Char(
        string=u'Justificativa',
        size=255,
        readonly=True,
        states={'draft': [('readonly', False)]},
        required=True)

    invalid_number_document_event_ids = fields.One2many(
        comodel_name='l10n_br_account.document_event',
        inverse_name='invalid_number_document_event_id',
        string=u'Eventos',
        states={'done': [('readonly', True)]})

    _sql_constraints = [
        ('number_uniq',
         'unique(document_serie_id, number_start, number_end, state)',
         u'Sequência existente!'),
    ]

    @api.multi
    @api.constrains('justificative')
    def _check_justificative(self):
        for record in self:
            if len(record.justificative) < 15:
                raise UserError(_(
                    'Justificativa deve ter tamanho minimo de 15 caracteres.'))
            return True

    @api.multi
    @api.constrains('number_start', 'number_end')
    def _check_range(self):
        for record in self:
            where = []
            if record.number_start:
                where.append("((number_end>='%s') or (number_end is null))" % (
                    record.number_start,))
            if record.number_end:
                where.append(
                    "((number_start<='%s') or (number_start is null))" % (
                        record.number_end,))

            record._cr.execute(
                'SELECT id \
                FROM l10n_br_account_invoice_invalid_number \
                WHERE ' + ' and '.join(where) + (where and ' and ' or '') +
                "document_serie_id = %s \
                AND state = 'done' \
                AND id <> %s" % (record.document_serie_id.id, record.id))
            if (record._cr.fetchall() or
                    (record.number_start > record.number_end)):
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
        return super(L10nBrAccountInvoiceInvalidNumber, self).unlink()
