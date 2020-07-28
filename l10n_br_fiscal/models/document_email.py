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
        string="Name",
        readonly=True,
        store=True,
        copy=False,
        compute="_compute_name",
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
        string="Fiscal Document Type",
        help="Select the type of document that will be applied "
             "to the email templates definitions."
    )

    state_edoc = fields.Selection(
        selection=SITUACAO_EDOC,
        string="Situação e-doc",
        copy=False,
        required=True,
        company_dependent=True,
        track_visibility="onchange",
        index=True,
    )

    email_template = fields.Many2one(
        comodel_name="mail.template",
        string="Fiscal Document E-mail Template",
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
        'This name is already used by another email definition!'
        )]


class Document(models.Model):
    _inherit = 'l10n_br_fiscal.document'

    def _after_change_state(self, old_state, new_state):
        super()._after_change_state(
            old_state, new_state
        )
        self.send_email(new_state)

    def send_email(self, new_state):
        email_template = self._get_email_template(new_state)
        if email_template:
            email_template.send_mail(self.id)

        # if not mail:
        #     raise UserError(_('Modelo de email padrão não configurado'))
        # # atts = self._find_attachment_ids_email()
        # _logger.info('Sending e-mail for e-doc %s (number: %s)' % (
        #     self.id, self.number))
        #
        # values = mail.generate_email([self.id])[self.id]
        # subject = values.pop('subject')
        # values.pop('body')
        # # values.pop('attachment_ids')
        # # Hack - Those attachments are being encoded twice,
        # # so lets decode to message_post encode again
        # new_items = []
        # # for item in values.get('attachments', []):
        # #     new_items.append((item[0], base64.b64decode(item[1])))
        # # values['attachments'] = new_items
        # self.document_id.message_post(
        #     body=values['body_html'], subject=subject,
        #     message_type='email', subtype='mt_comment',
        #     # attachment_ids=atts + mail.attachment_ids.ids, **values
        # )

    def _get_email_template(self, new_state):
        email_template = \
            self.document_type_id\
                .document_email_ids.filtered(
                    lambda e: e.state_edoc == new_state)\
                .mapped('email_template')
        return email_template
