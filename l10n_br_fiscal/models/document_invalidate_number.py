# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from ..constants.fiscal import SITUACAO_EDOC_INUTILIZADA


class DocumentInvalidateNumber(models.Model):
    _name = "l10n_br_fiscal.document.invalidate.number"
    _inherit = "l10n_br_fiscal.event.abstract"
    _description = "Fiscal Document Invalidate Number Record"

    @api.multi
    def name_get(self):
        return [(rec.id,
                 u"({0}): {1} - {2}".format(
                     rec.document_serie_id.name,
                     rec.number_start, rec.number_end)
                 ) for rec in self]

    company_id = fields.Many2one(
        readonly=True, related=False,
        states={'draft': [('readonly', False)]}, required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'l10n_br_fiscal.document.invalidate.number'))

    document_serie_id = fields.Many2one(
        'l10n_br_fiscal.document.serie', 'Série',
        domain="[('company_id', '=', company_id)]", readonly=True,
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

    invalid_number_document_event_ids = fields.One2many(
        'l10n_br_fiscal.document.event', 'invalid_number_document_event_id',
        u'Eventos', states={'done': [('readonly', True)]})

    _sql_constraints = [
        ('number_uniq',
         'unique(document_serie_id, number_start, number_end, state)',
         u'Sequência existente!'),
    ]

    @api.multi
    @api.constrains('number_start', 'number_end')
    def _check_range(self):
        for record in self:
            if record.company_id:
                domain = [
                    ('id', '!=', record.id),
                    ('state', '=', 'done'),
                    ('document_serie_id', '=', record.document_serie_id.id),
                    '|',
                    ('number_end', '>=', record.number_end),
                    ('number_end', '=', False),
                    '|',
                    ('number_start', '<=', record.number_start),
                    ('number_start', '=', False)]

                if self.search_count(domain):
                    raise ValidationError(_(
                        "Não é permitido faixas sobrepostas!"))
        return True

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
        return super(DocumentInvalidateNumber, self).unlink()

    @api.multi
    def action_invalidate(self):
        for record in self:
            event_id = self.env['l10n_br_fiscal.document.event'].create({
                'type': '3',
                'response': 'Inutilização do número %s ao número %s' % (
                    record.number_start, record.number_end),
                'company_id': record.company_id.id,
                'origin': 'Inutilização de faixa',
                'create_date': fields.Datetime.now(),
                'write_date': fields.Datetime.now(),
                'end_date': fields.Datetime.now(),
                'state': 'draft',
                'invalid_number_document_event_id': record.id,
            })

            record.invalidate(event_id)

    @api.multi
    def invalidate(self, event_id):
        for record in self:
            event_id.state = 'done'
            record.state = 'done'
            if record.document_id:
                record.document_id.state_edoc = SITUACAO_EDOC_INUTILIZADA
            else:
                for number in range(record.number_start,
                                    record.number_end + 1):
                    record.env['l10n_br_fiscal.document'].create({
                        'document_serie_id': record.document_serie_id.id,
                        'document_type_id':
                            record.document_serie_id.document_type_id.id,
                        'company_id': record.company_id.id,
                        'state_edoc': SITUACAO_EDOC_INUTILIZADA,
                        'issuer': 'company',
                        'number': str(number),
                    })
