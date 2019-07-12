# Copyright (C) 2009  Renato Lima - Akretion <renato.lima@akretion.com.br>
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

from ..constants.fiscal import FISCAL_IN_OUT, FISCAL_IN_OUT_DEFAULT


class DocumentSerie(models.Model):
    _name = 'l10n_br_fiscal.document.serie'
    _description = 'Fiscal Document Serie'
    _inherit = 'l10n_br_fiscal.data.abstract'

    code = fields.Char(
        size=3)

    name = fields.Char(
        string='Name',
        required=True)

    active = fields.Boolean(
        string='Active',
        default=True)

    fiscal_type = fields.Selection(
        selection=FISCAL_IN_OUT,
        string=u'Type',
        default=FISCAL_IN_OUT_DEFAULT)

    fiscal_document_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document.type',
        string='Fiscal Document',
        required=True)

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env['res.company']._company_default_get(
                'l10n_br_fiscal.document.serie'))

    internal_sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        domain="[('company_id', '=', company_id)]",
        string='Sequence')

    sequence_number_next = fields.Integer(
        related='internal_sequence_id.number_next')

    @api.model
    def _create_sequence(self, values):
        """ Create new no_gap entry sequence for every
        new document serie """
        sequence = {
            'name': values['name'],
            'implementation': 'no_gap',
            'padding': 1,
            'number_increment': 1}
        if 'company_id' in values:
            sequence['company_id'] = values['company_id']
        return self.env['ir.sequence'].create(sequence).id

    @api.model
    def create(self, values):
        """ Overwrite method to create a new ir.sequence if
         this field is null """
        if not values.get('internal_sequence_id'):
            values.update(
                {'internal_sequence_id': self._create_sequence(values)})
        return super(DocumentSerie, self).create(values)
