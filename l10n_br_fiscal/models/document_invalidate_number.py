# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.exceptions import UserError


class DocumentInvalidateNumber(models.Model):
    _name = "l10n_br_fiscal.document.invalidate.number"
    _description = "Fiscal Document Invalidate Number Record"

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
            'l10n_br_fiscal.document.invalidate.number'))

    fiscal_document_id = fields.Many2one(
        'l10n_br_fiscal.document', 'Documento Fiscal',
        readonly=True, states={'draft': [('readonly', False)]},
        required=True)

    document_serie_id = fields.Many2one(
        'l10n_br_fiscal.document.serie', 'Série',
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
        'l10n_br_fiscal.document.event', 'invalid_number_document_event_id',
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
        return super(InvalidateNumber, self).unlink()
