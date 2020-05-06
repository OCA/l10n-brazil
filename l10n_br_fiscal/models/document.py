# Copyright (C) 2013  Renato Lima - Akretion
# Copyright (C) 2019  KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from ast import literal_eval

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants.fiscal import (
    TAX_FRAMEWORK,
    DOCUMENT_ISSUER,
    DOCUMENT_ISSUER_COMPANY,
    DOCUMENT_ISSUER_PARTNER,
    SITUACAO_EDOC_AUTORIZADA,
    NFE_IND_IE_DEST,
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
        'l10n_br_fiscal.document.electronic']
    _description = 'Fiscal Document'

    @api.depends('line_ids')
    def _compute_amount(self):
        for record in self:
            record.amount_untaxed = sum(
                line.amount_untaxed for line in record.line_ids)
            record.amount_icms_base = sum(
                line.icms_base for line in record.line_ids)
            record.amount_icms_value = sum(
                line.icms_value for line in record.line_ids)
            record.amount_ipi_base = sum(
                line.ipi_base for line in record.line_ids)
            record.amount_ipi_value = sum(
                line.ipi_value for line in record.line_ids)
            record.amount_pis_base = sum(
                line.pis_base for line in record.line_ids)
            record.amount_pis_value = sum(
                line.pis_value for line in record.line_ids)
            record.amount_pis_ret_base = sum(
                line.pis_wh_base for line in record.line_ids)
            record.amount_pis_ret_value = sum(
                line.pis_wh_value for line in record.line_ids)
            record.amount_cofins_base = sum(
                line.cofins_base for line in record.line_ids)
            record.amount_cofins_value = sum(
                line.cofins_value for line in record.line_ids)
            record.amount_cofins_ret_base = sum(
                line.cofins_wh_base for line in record.line_ids)
            record.amount_cofins_ret_value = sum(
                line.cofins_wh_value for line in record.line_ids)
            record.amount_csll_base = sum(
                line.csll_base for line in record.line_ids)
            record.amount_csll_value = sum(
                line.csll_value for line in record.line_ids)
            record.amount_csll_ret_base = sum(
                line.csll_wh_base for line in record.line_ids)
            record.amount_csll_ret_value = sum(
                line.csll_wh_value for line in record.line_ids)
            record.amount_issqn_base = sum(
                line.issqn_base for line in record.line_ids)
            record.amount_issqn_value = sum(
                line.issqn_value for line in record.line_ids)
            record.amount_issqn_ret_base = sum(
                line.issqn_wh_base for line in record.line_ids)
            record.amount_issqn_ret_value = sum(
                line.issqn_wh_value for line in record.line_ids)
            record.amount_irpj_base = sum(
                line.irpj_base for line in record.line_ids)
            record.amount_irpj_value = sum(
                line.irpj_value for line in record.line_ids)
            record.amount_irpj_ret_base = sum(
                line.irpj_wh_base for line in record.line_ids)
            record.amount_irpj_ret_value = sum(
                line.irpj_wh_value for line in record.line_ids)
            record.amount_inss_base = sum(
                line.inss_base for line in record.line_ids)
            record.amount_inss_value = sum(
                line.inss_value for line in record.line_ids)
            record.amount_inss_wh_base = sum(
                line.inss_wh_base for line in record.line_ids)
            record.amount_inss_wh_value = sum(
                line.inss_wh_value for line in record.line_ids)
            record.amount_tax = sum(
                line.amount_tax for line in record.line_ids)
            record.amount_discount = sum(
                line.discount_value for line in record.line_ids)
            record.amount_insurance_value = sum(
                line.insurance_value for line in record.line_ids)
            record.amount_other_costs_value = sum(
                line.other_costs_value for line in record.line_ids)
            record.amount_freight_value = sum(
                line.freight_value for line in record.line_ids)
            record.amount_total = sum(
                line.amount_total for line in record.line_ids)

    @api.depends("fiscal_payment_ids")
    def _compute_payment_change_value(self):
        payment_value = 0
        for payment in self.fiscal_payment_ids:
            for line in payment.line_ids:
                payment_value += line.amount

        self.amount_payment_value = payment_value

        change_value = payment_value - self.amount_total
        self.amount_change_value = change_value if change_value >= 0 else 0

        missing_payment = self.amount_total - payment_value
        self.amount_missing_payment_value = missing_payment \
            if missing_payment >= 0 else 0

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

    partner_legal_name = fields.Char(
        string='Legal Name',
        related='partner_id.legal_name',
    )

    partner_name = fields.Char(
        string='Name',
        related='partner_id.name',
    )

    partner_cnpj_cpf = fields.Char(
        string='CNPJ',
        related='partner_id.cnpj_cpf',
    )

    partner_inscr_est = fields.Char(
        string='State Tax Number',
        related='partner_id.inscr_est',
    )

    partner_ind_ie_dest = fields.Selection(
        selection=NFE_IND_IE_DEST,
        string='Contribuinte do ICMS',
        related='partner_id.ind_ie_dest',
    )

    partner_inscr_mun = fields.Char(
        string='Municipal Tax Number',
        related='partner_id.inscr_mun',
    )

    partner_suframa = fields.Char(
        string='Suframa',
        related='partner_id.suframa',
    )

    partner_cnae_main_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cnae',
        string='Main CNAE',
        related='partner_id.cnae_main_id',
    )

    partner_tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        string='Tax Framework',
        related='partner_id.tax_framework',
    )

    partner_street = fields.Char(
        string='Partner Street',
        related='partner_id.street',
    )

    partner_number = fields.Char(
        string='Partner Number',
        related='partner_id.street_number',
    )

    partner_street2 = fields.Char(
        string='Partner Street2',
        related='partner_id.street2',
    )

    partner_district = fields.Char(
        string='Partner District',
        related='partner_id.district',
    )

    partner_country_id = fields.Many2one(
        comodel_name='res.country',
        string='Partner Country',
        related='partner_id.country_id',
    )

    partner_state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='Partner State',
        related='partner_id.state_id',
    )

    partner_city_id = fields.Many2one(
        comodel_name='res.city',
        string='Partner City',
        related='partner_id.city_id',
    )

    partner_zip = fields.Char(
        string='Partner Zip',
        related='partner_id.zip',
    )

    partner_phone = fields.Char(
        string='Partner Phone',
        related='partner_id.phone',
    )

    partner_is_company = fields.Boolean(
        string='Partner Is Company?',
        related='partner_id.is_company',
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

    company_legal_name = fields.Char(
        string='Company Legal Name',
        related='company_id.legal_name',
    )

    company_name = fields.Char(
        string='Company Name',
        size=128,
        related='company_id.name',
    )

    company_cnpj_cpf = fields.Char(
        string='Company CNPJ',
        related='company_id.cnpj_cpf',
    )

    company_inscr_est = fields.Char(
        string='Company State Tax Number',
        related='company_id.inscr_est',
    )

    company_inscr_mun = fields.Char(
        string='Company Municipal Tax Number',
        related='company_id.inscr_mun',
    )

    company_suframa = fields.Char(
        string='Company Suframa',
        related='company_id.suframa',
    )

    company_cnae_main_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cnae',
        string='Company Main CNAE',
        related='company_id.cnae_main_id',
    )

    company_tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        string='Company Tax Framework',
        related='company_id.tax_framework',
    )

    company_street = fields.Char(
        string='Company Street',
        related='company_id.street',
    )

    company_number = fields.Char(
        string='Company Number',
        related='company_id.street_number',
    )

    company_street2 = fields.Char(
        string='Company Street2',
        related='company_id.street2',
    )
    company_district = fields.Char(
        string='Company District',
        related='company_id.district',
    )

    company_country_id = fields.Many2one(
        comodel_name='res.country',
        string='Company Country',
        related='company_id.country_id',
    )

    company_state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='Company State',
        related='company_id.state_id',
    )

    company_city_id = fields.Many2one(
        comodel_name='res.city',
        string='Company City',
        related='company_id.city_id',
    )
    company_zip = fields.Char(
        string='Company ZIP',
        related='company_id.zip',
    )

    company_phone = fields.Char(
        string='Company Phone',
        related='company_id.phone',
    )

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        default=lambda self: self.env.user.company_id.currency_id,
        store=True,
        readonly=True,
    )

    amount_untaxed = fields.Monetary(
        string='Amount Untaxed',
        compute='_compute_amount',
    )

    amount_icms_base = fields.Monetary(
        string='ICMS Base',
        compute='_compute_amount',
    )

    amount_icms_value = fields.Monetary(
        string='ICMS Value',
        compute='_compute_amount',
    )

    amount_ipi_base = fields.Monetary(
        string='IPI Base',
        compute='_compute_amount',
    )

    amount_ipi_value = fields.Monetary(
        string='IPI Value',
        compute='_compute_amount',
    )

    amount_pis_base = fields.Monetary(
        string='PIS Base',
        compute='_compute_amount',
    )

    amount_pis_value = fields.Monetary(
        string='PIS Value',
        compute='_compute_amount',
    )

    amount_pis_ret_base = fields.Monetary(
        string='PIS Ret Base',
        compute='_compute_amount',
    )

    amount_pis_ret_value = fields.Monetary(
        string='PIS Ret Value',
        compute='_compute_amount',
    )

    amount_cofins_base = fields.Monetary(
        string='COFINS Base',
        compute='_compute_amount',
    )

    amount_cofins_value = fields.Monetary(
        string='COFINS Value',
        compute='_compute_amount',
    )

    amount_cofins_ret_base = fields.Monetary(
        string='COFINS Ret Base',
        compute='_compute_amount',
    )

    amount_cofins_ret_value = fields.Monetary(
        string='COFINS Ret Value',
        compute='_compute_amount',
    )

    amount_issqn_base = fields.Monetary(
        string='ISSQN Base',
        compute='_compute_amount',
    )

    amount_issqn_value = fields.Monetary(
        string='ISSQN Value',
        compute='_compute_amount',
    )

    amount_issqn_ret_base = fields.Monetary(
        string='ISSQN Ret Base',
        compute='_compute_amount',
    )

    amount_issqn_ret_value = fields.Monetary(
        string='ISSQN Ret Value',
        compute='_compute_amount',
    )

    amount_csll_base = fields.Monetary(
        string='CSLL Base',
        compute='_compute_amount',
    )

    amount_csll_value = fields.Monetary(
        string='CSLL Value',
        compute='_compute_amount',
    )

    amount_csll_ret_base = fields.Monetary(
        string='CSLL Ret Base',
        compute='_compute_amount',
    )

    amount_csll_ret_value = fields.Monetary(
        string='CSLL Ret Value',
        compute='_compute_amount',
    )

    amount_irpj_base = fields.Monetary(
        string='IRPJ Base',
        compute='_compute_amount',
    )

    amount_irpj_value = fields.Monetary(
        string='IRPJ Value',
        compute='_compute_amount',
    )

    amount_irpj_ret_base = fields.Monetary(
        string='IRPJ Ret Base',
        compute='_compute_amount',
    )

    amount_irpj_ret_value = fields.Monetary(
        string='IRPJ Ret Value',
        compute='_compute_amount',
    )

    amount_inss_base = fields.Monetary(
        string='INSS Base',
        compute='_compute_amount',
    )

    amount_inss_value = fields.Monetary(
        string='INSS Value',
        compute='_compute_amount',
    )

    amount_inss_wh_base = fields.Monetary(
        string='INSS Ret Base',
        compute='_compute_amount',
    )

    amount_inss_wh_value = fields.Monetary(
        string='INSS Ret Value',
        compute='_compute_amount',
    )

    amount_tax = fields.Monetary(
        string='Amount Tax',
        compute='_compute_amount',
    )

    amount_total = fields.Monetary(
        string='Amount Total',
        compute='_compute_amount',
    )

    amount_discount = fields.Monetary(
        string='Amount Discount',
        compute='_compute_amount',
    )

    amount_insurance_value = fields.Monetary(
        string='Insurance Value',
        default=0.00,
        compute='_compute_amount',
    )

    amount_other_costs_value = fields.Monetary(
        string='Other Costs',
        default=0.00,
        compute='_compute_amount',
    )

    amount_freight_value = fields.Monetary(
        string='Freight Value',
        default=0.00,
        compute='_compute_amount',
    )

    amount_change_value = fields.Monetary(
        string="Change Value",
        default=0.00,
        compute="_compute_payment_change_value"
    )

    amount_payment_value = fields.Monetary(
        string="Payment Value",
        default=0.00,
        compute="_compute_payment_change_value"
    )

    amount_missing_payment_value = fields.Monetary(
        string="Missing Payment Value",
        default=0.00,
        compute="_compute_payment_change_value"
    )

    line_ids = fields.One2many(
        comodel_name='l10n_br_fiscal.document.line',
        inverse_name='document_id',
        string='Document Lines',
        copy=True,
    )

    #
    # Duplicatas e pagamentos
    #
    payment_term_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.payment.term',
        string='Condição de pagamento',
        ondelete='restrict',
    )

    financial_ids = fields.One2many(
        comodel_name='l10n_br_fiscal.payment.line',
        inverse_name='document_id',
        string='Duplicatas',
        copy=True,
    )

    fiscal_payment_ids = fields.One2many(
        comodel_name='l10n_br_fiscal.payment',
        inverse_name='document_id',
        string='Pagamentos',
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

    ind_final = fields.Selection(
        selection=[
            ('0', 'Não'),
            ('1', 'Sim')
        ],
        string='Operação com consumidor final',
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

    def _document_comment_vals(self):
        return {
            'user': self.env.user,
            'ctx': self._context,
            'doc': self,
        }

    def document_comment(self):
        for record in self:
            record.additional_data = \
                record.additional_data and record.additional_data + ' - ' or ''
            record.additional_data += record.comment_ids.compute_message(
                record._document_comment_vals())
            record.line_ids.document_comment()

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
        return_ids = self.env[self._name]
        for record in self:
            if record.fiscal_operation_id.return_fiscal_operation_id:
                new = record.copy()
                new.fiscal_operation_id = (
                    record.fiscal_operation_id.return_fiscal_operation_id)
                if record.fiscal_operation_type == 'out':
                    new.fiscal_operation_type = 'in'
                else:
                    new.fiscal_operation_type = 'out'
                new._onchange_fiscal_operation_id()
                new.line_ids.write({'fiscal_operation_id': new.fiscal_operation_id.id})

                for item in new.line_ids:
                    item._onchange_fiscal_operation_id()

                return_ids |= new
        return return_ids

    def action_create_return(self):
        self.ensure_one()
        return_id = self._create_return()
        if return_id.fiscal_operation_type == 'out':
            return_id.fiscal_operation_type = 'in'
            action = self.env.ref('l10n_br_fiscal.document_in_action').read()[0]
        else:
            return_id.fiscal_operation_type = 'out'
            action = self.env.ref('l10n_br_fiscal.document_out_action').read()[0]

        action['domain'] = literal_eval(action['domain'])
        action['domain'].append(('id', '=', return_id.id))
        return action

    def _document_comment_vals(self):
        return {
            'user': self.env.user,
            'ctx': self._context,
            'doc': self,
        }

    def document_comment(self):
        for record in self:
            record.additional_data = \
                record.additional_data and record.additional_data + ' - ' or ''
            record.additional_data += record.comment_ids.compute_message(
                record._document_comment_vals())
            record.line_ids.document_comment()

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
        if self.issuer == DOCUMENT_ISSUER_COMPANY:
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

    def generate_financial(self):
        for record in self:
            if record.payment_term_id and self.company_id and self.currency_id:
                record.financial_ids.unlink()
                record.fiscal_payment_ids.unlink()

                vals = {
                    'payment_term_id': self.payment_term_id.id,
                    'amount': self.amount_missing_payment_value,
                    'currency_id': self.currency_id.id,
                    'company_id': self.company_id.id,
                }
                vals.update(self.fiscal_payment_ids._compute_payment_vals(
                    payment_term_id=self.payment_term_id,
                    currency_id=self.currency_id,
                    company_id=self.company_id,
                    amount=self.amount_missing_payment_value, date=self.date)
                )
                self.fiscal_payment_ids = self.fiscal_payment_ids.new(vals)
                for line in self.fiscal_payment_ids.mapped('line_ids'):
                    line.document_id = self

            elif record.fiscal_payment_ids:
                record.financial_ids.unlink()
                record.fiscal_payment_ids.unlink()

    @api.onchange("fiscal_payment_ids", "payment_term_id")
    def _onchange_fiscal_payment_ids(self):
        financial_ids = []
        for payment in self.fiscal_payment_ids:
            for line in payment.line_ids:
                financial_ids.append(line.id)
        self.financial_ids = [(6, 0, financial_ids)]

    @api.onchange("payment_term_id", "company_id", "currency_id",
                  "amount_missing_payment_value", "date")
    def _onchange_payment_term_id(self):
        if self.payment_term_id and self.company_id and self.currency_id and not self.fiscal_payment_ids:
            # vfiscal_payment_id = self.fiscal_payment_ids.new()
            # vfiscal_payment_id._onchange_payment_term_id()

            # fiscal_payment_vals = vfiscal_payment_id._convert_to_cache(
            #     vfiscal_payment_id._cache)
            # fiscal_payment_vals.update(vfiscal_payment_id._compute_payment_vals())

            vals = {
                'payment_term_id': self.payment_term_id.id,
                'amount': self.amount_missing_payment_value,
                'currency_id': self.currency_id.id,
                'company_id': self.company_id.id,
                'document_id': self.id,
             }
            vals.update(self.fiscal_payment_ids._compute_payment_vals(
                payment_term_id=self.payment_term_id, currency_id=self.currency_id,
                company_id=self.company_id,
                amount=self.amount_missing_payment_value, date=self.date)
            )
            self.fiscal_payment_ids |= self.fiscal_payment_ids.new(vals)
            for line in self.fiscal_payment_ids.mapped('line_ids'):
                line.document_id = self            #
            #
            # self.update({
            #     'fiscal_payment_ids': [
            #         (6, 0, {}),
            #         (0, 0,vals)
            #     ]
            # })

    # @api.onchange("fiscal_payment_ids", "payment_term_id")
    # def _onchange_fiscal_payment_ids(self):
    #     financial_ids = []
    #     for payment in self.fiscal_payment_ids:
    #         for line in payment.line_ids:
    #             financial_ids.append(line.id)
    #     self.financial_ids = [(6, 0, financial_ids)]
