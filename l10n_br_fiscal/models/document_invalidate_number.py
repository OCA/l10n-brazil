# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from ..constants.fiscal import SITUACAO_EDOC_INUTILIZADA


class InvalidateNumber(models.Model):
    _name = 'l10n_br_fiscal.invalidate.number'
    _description = 'Invalidate Number'

    document_serie_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document.serie',
        string='Serie',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        related='document_serie_id.company_id',
        readonly=True,
    )

    number_start = fields.Integer(
        string='Initial Number',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    number_end = fields.Integer(
        string='End Number',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    justification = fields.Char(
        string='Justification',
        size=255,
    )

    state = fields.Selection(
        selection=[
            ('draft', _('Draft')),
            ('done', _('Done')),
        ],
        string='Status',
        readonly=True,
        default='draft',
    )

    event_ids = fields.One2many(
        comodel_name='l10n_br_fiscal.event',
        inverse_name='invalidate_number_id',
        string='Events',
        readonly=True,
        states={'done': [('readonly', True)]},
    )

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
                    raise ValidationError(
                        _("Number range overlap is not allowed."))
        return True

    def action_draft_done(self):
        self.write({'state': 'done'})

    @api.multi
    def name_get(self):
        return [(rec.id,
                 '({0}): {1} - {2}'.format(
                     rec.document_serie_id.name,
                     rec.number_start,
                     rec.number_end)
                 ) for rec in self]

    @api.multi
    def unlink(self):
        invalid_number_draft = self.filtered(lambda n: n.state == 'draft')
        if invalid_number_draft:
            raise UserError(
                _('You cannot unlink a done Invalidate Number Range.'))
        return super().unlink()

    @api.multi
    def action_invalidate(self):
        for r in self:
            event_id = self.env['l10n_br_fiscal.event'].create({
                'type': '3',
                'response': 'Inutilização do número %s ao número %s' % (
                    record.number_start, record.number_end),
                'origin': 'Inutilização de faixa',
                'state': 'draft',
                'invalid_number_id': record.id,
            })
            record.invalidate(event_id)

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
