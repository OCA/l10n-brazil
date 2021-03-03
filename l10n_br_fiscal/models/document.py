# Copyright (C) 2013  Renato Lima - Akretion
# Copyright (C) 2019  KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from ast import literal_eval

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

from ..constants.fiscal import (
    DOCUMENT_ISSUER,
    DOCUMENT_ISSUER_COMPANY,
    DOCUMENT_ISSUER_PARTNER,
    SITUACAO_EDOC_AUTORIZADA,
)


class Document(models.Model):
    """ Implementação base dos documentos fiscais

    Devemos sempre ter em mente que o modelo que vai usar este módulo abstrato
     tem diversos metodos importantes e a intenção que os módulos da OCA que
     extendem este modelo, funcionem se possível sem a necessidade de
     codificação extra.

    É preciso também estar atento que o documento fiscal tem dois estados:

    - Estado do documento eletrônico / não eletônico: state_edoc
    - Estado FISCAL: state_fiscal

    O estado fiscal é um campo que é alterado apenas algumas vezes pelo código
    e é de responsabilidade do responsável fiscal pela empresa de manter a
    integridade do mesmo, pois ele não tem um fluxo realmente definido e
    interfere no lançamento do registro no arquivo do SPED FISCAL.
    """
    _name = 'l10n_br_fiscal.document'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin',
        'l10n_br_fiscal.document.mixin',
        'l10n_br_fiscal.document.electronic',
        'l10n_br_fiscal.document.invoice.mixin']
    _description = 'Fiscal Document'

    # used mostly to enable _inherits of account.invoice on
    # fiscal_document when existing invoices have no fiscal document.
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    fiscal_operation_id = fields.Many2one(
        domain="[('state', '=', 'approved'), "
               "'|', ('fiscal_operation_type', '=', fiscal_operation_type),"
               " ('fiscal_operation_type', '=', 'all')]",
    )

    fiscal_operation_type = fields.Selection(
        related=False,
    )

    is_edoc_printed = fields.Boolean(
        string='Printed',
        readonly=True,
    )

    number = fields.Char(
        string='Number',
        copy=False,
        index=True,
    )

    key = fields.Char(
        string='key',
        copy=False,
        index=True,
    )

    issuer = fields.Selection(
        selection=DOCUMENT_ISSUER,
        default=DOCUMENT_ISSUER_COMPANY,
        required=True,
        string='Issuer',
    )

    date = fields.Datetime(
        string='Date',
        copy=False,
    )

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        index=True,
        default=lambda self: self.env.user,
    )

    document_type_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document.type',
    )

    operation_name = fields.Char(
        string='Operation Name',
        copy=False,
    )

    document_electronic = fields.Boolean(
        related='document_type_id.electronic',
        string='Electronic?',
        store=True,
    )

    date_in_out = fields.Datetime(
        string='Date Move',
        copy=False,
    )

    document_serie_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document.serie',
        domain="[('active', '=', True),"
               "('document_type_id', '=', document_type_id)]",
    )

    document_serie = fields.Char(
        string='Serie Number',
    )

    fiscal_document_related_ids = fields.One2many(
        comodel_name='l10n_br_fiscal.document.related',
        inverse_name='fiscal_document_id',
        string='Fiscal Document Related',
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
    )

    partner_shipping_id = fields.Many2one(
        comodel_name='res.partner',
        string='Shipping Address',
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'l10n_br_fiscal.document'),
    )

    processador_edoc = fields.Selection(
        related='company_id.processador_edoc',
        store=True,
    )
    line_ids = fields.One2many(
        comodel_name='l10n_br_fiscal.document.line',
        inverse_name='document_id',
        string='Document Lines',
        copy=True,
    )

    # TODO esse campo deveria ser calculado de
    # acordo com o fiscal_document_id
    document_section = fields.Selection(
        selection=[
            ('nfe', 'NF-e'),
            ('nfse_recibos', 'NFS-e e Recibos'),
            ('nfce_cfe', 'NFC-e e CF-e'),
            ('cte', 'CT-e'),
            ('todos', 'Todos'),
        ],
        string='Document Section',
        readonly=True,
        copy=True,
    )

    edoc_purpose = fields.Selection(
        selection=[
            ('1', 'Normal'),
            ('2', 'Complementar'),
            ('3', 'Ajuste'),
            ('4', 'Devolução de mercadoria'),
        ],
        string='Finalidade',
        default='1',
    )

    document_event_ids = fields.One2many(
        comodel_name='l10n_br_fiscal.document.event',
        inverse_name='fiscal_document_id',
        string='Events',
        copy=False,
        readonly=True,
    )

    close_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.closing',
        string='Close ID')

    document_type = fields.Char(
        related='document_type_id.code',
        stored=True,
    )

    dfe_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.dfe',
        string='DF-e Consult',
    )

    # Você não vai poder fazer isso em modelos que já tem state
    # TODO Porque não usar o campo state do fiscal.document???
    state = fields.Selection(
        related="state_edoc",
        string='State'
    )

    document_subsequent_ids = fields.One2many(
        comodel_name='l10n_br_fiscal.subsequent.document',
        inverse_name='source_document_id',
        copy=True,
    )

    document_subsequent_generated = fields.Boolean(
        string='Subsequent documents generated?',
        compute='_compute_document_subsequent_generated',
        default=False,
    )

    @api.multi
    @api.constrains('number')
    def _check_number(self):
        for record in self:
            if not record.number:
                return
            domain = [
                ('id', '!=', record.id),
                ('active', '=', True),
                ('company_id', '=', record.company_id.id),
                ('issuer', '=', record.issuer),
                ('document_type_id', '=', record.document_type_id.id),
                ('document_serie', '=', record.document_serie),
                ('number', '=', record.number)]

            if record.issuer == DOCUMENT_ISSUER_PARTNER:
                domain.append(('partner_id', '=', record.partner_id.id))

            if record.env["l10n_br_fiscal.document"].search(domain):
                raise ValidationError(_(
                    "There is already a fiscal document with this "
                    "Serie: {0}, Number: {1} !".format(
                        record.document_serie, record.number)))

    @api.multi
    def name_get(self):
        return [(r.id, '{0} - Série: {1} - Número: {2}'.format(
            r.document_type_id.name,
            r.document_serie,
            r.number)) for r in self]

    @api.model
    def create(self, values):
        if not values.get('date'):
            values['date'] = self._date_server_format()
        return super().create(values)

    @api.multi
    def unlink(self):
        if self.env.ref('l10n_br_fiscal.fiscal_document_dummy') in self:
            raise UserError(_("You cannot unlink Fiscal Document Dummy !"))
        return super().unlink()

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.currency_id = self.company_id.currency_id

    @api.multi
    @api.onchange('document_section')
    def _onchange_document_section(self):
        if self.document_section:
            domain = dict()
            if self.document_section == 'nfe':
                domain['document_type_id'] = [('code', '=', '55')]
                self.document_type_id = \
                    self.env['l10n_br_fiscal.document.type'].search([
                        ('code', '=', '55')
                    ])[0]
            elif self.document_section == 'nfse_recibos':
                domain['document_type_id'] = [('code', '=', 'SE')]
                self.document_type_id = \
                    self.env['l10n_br_fiscal.document.type'].search([
                        ('code', '=', 'SE')
                    ])[0]
            elif self.document_section == 'nfce_cfe':
                domain['document_type_id'] = [('code', 'in', ('59', '65'))]
                self.document_type_id = \
                    self.env['l10n_br_fiscal.document.type'].search([
                        ('code', '=', '59')
                    ])[0]
            elif self.document_section == 'cte':
                domain['document_type_id'] = [('code', '=', '57')]
                self.document_type_id = \
                    self.env['l10n_br_fiscal.document.type'].search([
                        ('code', '=', '57')
                    ])[0]

            return {'domain': domain}

    def _create_return(self):
        return_docs = self.env[self._name]
        for record in self:
            fsc_op = record.fiscal_operation_id.return_fiscal_operation_id
            if not fsc_op:
                raise ValidationError(_(
                    "The fiscal operation {} has no return Fiscal "
                    "Operation defined".format(record.fiscal_operation_id)))

            new_doc = record.copy()
            new_doc.fiscal_operation_id = fsc_op
            new_doc._onchange_fiscal_operation_id()

            for l in new_doc.line_ids:
                fsc_op_line = l.fiscal_operation_id.return_fiscal_operation_id
                if not fsc_op_line:
                    raise ValidationError(_(
                        "The fiscal operation {} has no return Fiscal "
                        "Operation defined".format(l.fiscal_operation_id)))
                l.fiscal_operation_id = fsc_op_line
                l._onchange_fiscal_operation_id()
                l._onchange_fiscal_operation_line_id()

            return_docs |= new_doc
        return return_docs

    @api.multi
    def action_create_return(self):
        action = self.env.ref('l10n_br_fiscal.document_all_action').read()[0]
        return_docs = self._create_return()

        if return_docs:
            action['domain'] = literal_eval(action['domain'] or '[]')
            action['domain'].append(('id', 'in', return_docs.ids))

        return action

    def _get_email_template(self, state):
        self.ensure_one()
        return self.document_type_id.document_email_ids.search(
            ['|',
             ('state_edoc', '=', False),
             ('state_edoc', '=', state),
             ('issuer', '=', self.issuer),
             '|',
             ('document_type_id', '=', False),
             ('document_type_id', '=', self.document_type_id.id)],
            limit=1, order='state_edoc, document_type_id').mapped('email_template_id')

    def send_email(self, state):
        email_template = self._get_email_template(state)
        if email_template:
            email_template.send_mail(self.id)

    def _after_change_state(self, old_state, new_state):
        super()._after_change_state(old_state, new_state)
        self.send_email(new_state)

    def _exec_after_SITUACAO_EDOC_A_ENVIAR(self, old_state, new_state):
        super()._exec_after_SITUACAO_EDOC_A_ENVIAR(old_state, new_state)
        self.document_comment()

    @api.onchange('fiscal_operation_id')
    def _onchange_fiscal_operation_id(self):
        super()._onchange_fiscal_operation_id()
        if self.fiscal_operation_id:
            self.fiscal_operation_type = (
                self.fiscal_operation_id.fiscal_operation_type)
            self.ind_final = self.fiscal_operation_id.ind_final

        if self.issuer == DOCUMENT_ISSUER_COMPANY and not self.document_type_id:
            self.document_type_id = self.company_id.document_type_id

        subsequent_documents = [(6, 0, {})]
        for subsequent_id in self.fiscal_operation_id.mapped(
                'operation_subsequent_ids'):
            subsequent_documents.append((0, 0, {
                'source_document_id': self.id,
                'subsequent_operation_id': subsequent_id.id,
                'fiscal_operation_id':
                    subsequent_id.subsequent_operation_id.id,
            }))
        self.document_subsequent_ids = subsequent_documents

    @api.onchange('document_type_id')
    def _onchange_document_type_id(self):
        if self.document_type_id and self.issuer == DOCUMENT_ISSUER_COMPANY:
            self.document_serie_id = self.document_type_id.get_document_serie(
                self.company_id, self.fiscal_operation_id)

    @api.onchange('document_serie_id')
    def _onchange_document_serie_id(self):
        if self.document_serie_id and self.issuer == DOCUMENT_ISSUER_COMPANY:
            self.document_serie = self.document_serie_id.code

    def _exec_after_SITUACAO_EDOC_AUTORIZADA(self, old_state, new_state):
        super(Document, self)._exec_after_SITUACAO_EDOC_AUTORIZADA(
            old_state, new_state
        )
        self._generates_subsequent_operations()

    def _prepare_referenced_subsequent(self):
        vals = {
            'fiscal_document_id': self.id,
            'partner_id': self.partner_id.id,
            'document_type_id': self.document_type,
            'serie': self.document_serie,
            'number': self.number,
            'date': self.date,
            'document_key': self.key,
        }
        reference_id = self.env['l10n_br_fiscal.document.related'].create(vals)
        return reference_id

    def _document_reference(self, reference_ids):
        for referenced_item in reference_ids:
            referenced_item.fiscal_document_related_ids = self.id
            self.fiscal_document_related_ids |= referenced_item

    @api.depends('document_subsequent_ids.subsequent_document_id')
    def _compute_document_subsequent_generated(self):
        for document in self:
            if not document.document_subsequent_ids:
                continue
            document.document_subsequent_generated = all(
                subsequent_id.operation_performed
                for subsequent_id in document.document_subsequent_ids
            )

    def _generates_subsequent_operations(self):
        for record in self.filtered(lambda doc:
                                    not doc.document_subsequent_generated):
            for subsequent_id in record.document_subsequent_ids.filtered(
                    lambda doc_sub: doc_sub._confirms_document_generation()):
                subsequent_id.generate_subsequent_document()

    def cancel_edoc(self):
        self.ensure_one()
        if any(doc.state_edoc == SITUACAO_EDOC_AUTORIZADA
               for doc in self.document_subsequent_ids.mapped(
                'document_subsequent_ids')):
            message = _("Canceling the document is not allowed: one or more "
                        "associated documents have already been authorized.")
            raise UserWarning(message)

    @api.multi
    def action_send_email(self):
        """ Open a window to compose an email, with the fiscal document_type
        template message loaded by default
        """
        self.ensure_one()
        template = self._get_email_template(self.state)
        compose_form = self.env.ref(
            'mail.email_compose_message_wizard_form', False)
        lang = self.env.context.get('lang')
        if template and template.lang:
            lang = template._render_template(
                template.lang, self._name, self.id)
        self = self.with_context(lang=lang)
        ctx = dict(
            default_model='l10n_br_fiscal.document',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            model_description=self.document_type_id.name or self._name,
            force_email=True
        )
        return {
            'name': _('Send Fiscal Document Email Notification'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }
