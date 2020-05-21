# Copyright (C) 2013  Renato Lima - Akretion
# Copyright (C) 2019  KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from ast import literal_eval
from erpbrasil.base import misc

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants.fiscal import (
    TAX_FRAMEWORK,
    DOCUMENT_ISSUER,
    DOCUMENT_ISSUER_COMPANY,
    DOCUMENT_ISSUER_PARTNER,
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

    # used mostly to enable _inherits of account.invoice on
    # fiscal_document when existing invoices have no fiscal document.
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    fiscal_operation_id = fields.Many2one(
        domain="[('state', '=', 'approved'), "
               "'|', ('operation_type', '=', operation_type),"
               " ('operation_type', '=', 'all')]",
    )

    operation_type = fields.Selection(
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
    )

    partner_name = fields.Char(
        string='Name',
    )

    partner_cnpj_cpf = fields.Char(
        string='CNPJ',
    )

    partner_inscr_est = fields.Char(
        string='State Tax Number',
    )

    partner_inscr_mun = fields.Char(
        string='Municipal Tax Number',
    )

    partner_suframa = fields.Char(
        string='Suframa',
    )

    partner_cnae_main_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cnae',
        string='Main CNAE',
    )

    partner_tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        string='Tax Framework',
    )

    partner_shipping_id = fields.Many2one(
        comodel_name='res.partner',
        string='Shipping Address',
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'l10n_br_fiscal.document'),
    )

    processador_edoc = fields.Selection(
        related='company_id.processador_edoc',
        store=True,
    )

    company_legal_name = fields.Char(
        string='Company Legal Name',
    )

    company_name = fields.Char(
        string='Company Name',
        size=128,
    )

    company_cnpj_cpf = fields.Char(
        string='Company CNPJ',
    )

    company_inscr_est = fields.Char(
        string='Company State Tax Number',
    )

    company_inscr_mun = fields.Char(
        string='Company Municipal Tax Number',
    )

    company_suframa = fields.Char(
        string='Company Suframa',
    )

    company_cnae_main_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cnae',
        string='Company Main CNAE',
    )

    company_tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        string='Company Tax Framework',
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

    line_ids = fields.One2many(
        comodel_name='l10n_br_fiscal.document.line',
        inverse_name='document_id',
        string='Document Lines',
    )

    comment_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.comment',
        relation='l10n_br_fiscal_document_comment_rel',
        column1='document_id',
        column2='comment_id',
        string='Comments',
    )

    additional_data = fields.Text(
        string='Additional Data',
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

    @api.model
    def _create_serie_number(self, document_serie_id, document_date):
        document_serie = self.env['l10n_br_fiscal.document.serie'].browse(
            document_serie_id)
        number = document_serie.internal_sequence_id.with_context(
            ir_sequence_date=document_date)._next()
        invalids = \
            self.env['l10n_br_fiscal.document.invalidate.number'].search([
                ('state', '=', 'done'),
                ('document_serie_id', '=', document_serie_id)])
        invalid_numbers = []
        for invalid in invalids:
            invalid_numbers += range(
                invalid.number_start, invalid.number_end + 1)
        if int(number) in invalid_numbers:
            return self._create_serie_number(document_serie_id, document_date)
        return number

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

        if values.get('document_serie_id') and not values.get('number'):
            values['number'] = self._create_serie_number(
                values.get('document_serie_id'), values['date'])

        return super(Document, self).create(values)

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

    @api.multi
    @api.constrains('number')
    def _check_number(self):
        for record in self:
            domain = [
                ('id', '!=', record.id),
                ('active', '=', True),
                ('company_id', '=', record.company_id.id),
                ('issuer', '=', record.issuer),
                ('document_type_id', '=', record.document_type_id.id),
                ('document_serie', '=', record.document_serie),
                ('number', '=', record.number)]

            if not record.issuer == DOCUMENT_ISSUER_PARTNER:
                domain.append(('partner_id', '=', record.partner_id.id))

            if record.env["l10n_br_fiscal.document"].search(domain):
                raise ValidationError(_(
                    "There is already a fiscal document with this "
                    "Serie: {0}, Number: {1} !".format(
                        record.document_serie, record.number)))

    # TODO Este método deveria estar no fiscal document abstract
    def document_number(self):
        super(Document, self).document_number()
        for record in self:
            if record.issuer == "company" and record.document_electronic and \
                    not record.key:
                record._generate_key()

    # TODO - este método deveria estar no l10n_br_nfe e o calculo da chave
    # Deveria estar no erpbrasil.base.fiscal
    def _generate_key(self):
        company = self.company_id.partner_id
        chave = str(company.state_id and
                    company.state_id.ibge_code or "").zfill(2)

        chave += self.date.strftime("%y%m").zfill(4)

        chave += str(misc.punctuation_rm(
            self.company_id.partner_id.cnpj_cpf)).zfill(14)
        chave += str(self.document_type_id.code or "").zfill(2)
        chave += str(self.document_serie or "").zfill(3)
        chave += str(self.number or "").zfill(9)

        #
        # A inclusão do tipo de emissão na chave já torna a chave válida também
        # para a versão 2.00 da NF-e
        #
        chave += str(1).zfill(1)

        #
        # O código numério é um número aleatório
        #
        # chave += str(random.randint(0, 99999999)).strip().rjust(8, '0')

        #
        # Mas, por segurança, é preferível que esse número não seja
        # aleatório de todo
        #
        soma = 0
        for c in chave:
            soma += int(c) ** 3 ** 2

        codigo = str(soma)
        if len(codigo) > 8:
            codigo = codigo[-8:]
        else:
            codigo = codigo.rjust(8, "0")

        chave += codigo

        soma = 0
        m = 2
        for i in range(len(chave) - 1, -1, -1):
            c = chave[i]
            soma += int(c) * m
            m += 1
            if m > 9:
                m = 2

        digito = 11 - (soma % 11)
        if digito > 9:
            digito = 0

        chave += str(digito)
        # FIXME: Fazer sufixo depender do modelo
        self.key = 'NFe' + chave

    def _create_return(self):
        return_ids = self.env[self._name]
        for record in self:
            if record.fiscal_operation_id.return_fiscal_operation_id:
                new = record.copy()
                new.fiscal_operation_id = (
                    record.fiscal_operation_id.return_fiscal_operation_id)
                if record.operation_type == 'out':
                    new.operation_type = 'in'
                else:
                    new.operation_type = 'out'
                new._onchange_fiscal_operation_id()
                new.line_ids.write({'fiscal_operation_id': new.fiscal_operation_id.id})

                for item in new.line_ids:
                    item._onchange_fiscal_operation_id()

                return_ids |= new
        return return_ids

    def action_create_return(self):
        self.ensure_one()
        return_id = self._create_return()
        if return_id.operation_type == 'out':
            return_id.operation_type = 'in'
            action = self.env.ref('l10n_br_fiscal.document_in_action').read()[0]
        else:
            return_id.operation_type = 'out'
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

    def _exec_after_SITUACAO_EDOC_A_ENVIAR(self, old_state, new_state):
        super(Document, self)._exec_after_SITUACAO_EDOC_A_ENVIAR(
            old_state, new_state
        )
        self.document_comment()

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.company_legal_name = self.company_id.legal_name
            self.company_name = self.company_id.name
            self.company_cnpj_cpf = self.company_id.cnpj_cpf
            self.company_inscr_est = self.company_id.inscr_est
            self.company_inscr_mun = self.company_id.inscr_mun
            self.company_suframa = self.company_id.suframa
            self.company_cnae_main_id = self.company_id.cnae_main_id
            self.company_tax_framework = self.company_id.tax_framework

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.partner_legal_name = self.partner_id.legal_name
            self.partner_name = self.partner_id.name
            self.partner_cnpj_cpf = self.partner_id.cnpj_cpf
            self.partner_inscr_est = self.partner_id.inscr_est
            self.partner_inscr_mun = self.partner_id.inscr_mun
            self.partner_suframa = self.partner_id.suframa
            self.partner_cnae_main_id = self.partner_id.cnae_main_id
            self.partner_tax_framework = self.partner_id.tax_framework

    @api.onchange('fiscal_operation_id')
    def _onchange_fiscal_operation_id(self):
        if self.fiscal_operation_id:
            self.operation_name = self.fiscal_operation_id.name

        for comment_id in self.fiscal_operation_id.comment_ids:
            self.comment_ids += comment_id

    @api.onchange('document_serie_id')
    def _onchange_document_serie_id(self):
        if self.document_serie_id and self.issuer == DOCUMENT_ISSUER_COMPANY:
            self.document_serie = self.document_serie_id.code
