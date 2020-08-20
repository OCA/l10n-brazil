# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..constants.fiscal import (
    SITUACAO_EDOC,
)


class DocumentEmail(models.Model):
    _name = 'l10n_br_fiscal.document.email'
    _description = 'Fiscal Document Email'

    name = fields.Char(
        string='Name',
        readonly=True,
        store=True,
        copy=False,
        compute='_compute_name',
    )

    active = fields.Boolean(
        string='Active',
        default=True,
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        readonly=True,
    )

    document_type_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document.type',
        string='Fiscal Document Type',
        help="Select the type of document that will be applied "
             "to the email templates definitions."
    )

    state_edoc = fields.Selection(
        selection=SITUACAO_EDOC,
        string='Situação e-doc',
        copy=False,
        required=True,
        index=True,
    )

    email_template = fields.Many2one(
        comodel_name='mail.template',
        string='Fiscal Document E-mail Template',
        required=True,
        help="Select the email template that will be sent when "
             "this document state change.",
    )

    @api.multi
    @api.depends('document_type_id', 'state_edoc')
    def _compute_name(self):
        for record in self:
            document_type = record.document_type_id.name
            if not document_type:
                document_type = "Others Document Types"
            if record.state_edoc:
                record.name = document_type + ' - ' + record.state_edoc

    _sql_constraints = [(
        'name_company_unique',
        'unique(name)',
        'This name is already used by another email definition !'
    )]
