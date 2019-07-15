# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import datetime

from odoo import models, fields, api


class DocumentEvent(models.Model):
    _name = 'l10n_br_fiscal.document.event'

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
