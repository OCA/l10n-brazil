# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class DocumentCorrection(models.Model):
    _name = 'l10n_br_fiscal.document.correction'
    _description = 'Carta de Correção no Sefaz'

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
