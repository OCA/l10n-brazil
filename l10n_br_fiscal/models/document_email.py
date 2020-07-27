# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class DocumentEmail(models.Model):

    _name = 'l10n_br_fiscal.document.email'
    _description = 'Fiscal Document Email'

    name = fields.Char()

    active = fields.Boolean(
        string='Active',
        default=True)

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        readonly=True,
    )

    document_type_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document.type',
        string="Fiscal Document Type",
        help="Select the type of document that will be applied "
             "to the email templates definitions."
    )

    email_template_authorized_id = fields.Many2one(
        comodel_name="mail.template",
        string="Fiscal Document Autorizado E-mail Template",
        help="Select the email template that will be sent when "
        "this document authorized."
    )

    email_template_canceled_id = fields.Many2one(
        comodel_name="mail.template",
        string="Fiscal Document Canceled E-mail Template",
        help="Select the email template that will be sent when "
        "this document canceled."
    )

    email_template_denied_id = fields.Many2one(
        comodel_name="mail.template",
        string="Fiscal Document Denied E-mail Template",
        help="Select the email template that will be sent when "
        "this document denied."
    )

    email_template_correction_id = fields.Many2one(
        comodel_name="mail.template",
        string="Fiscal Document Correction E-mail Template",
        help="Select the email template that will be sent when "
             "this document correction."
    )
