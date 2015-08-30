# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

import datetime
from lxml import etree

from openerp import models, fields, api, _
from openerp.addons import decimal_precision as dp
from openerp.exceptions import except_orm, Warning, RedirectWarning

from openerp.addons.l10n_br_account.models.account_invoice import (
    OPERATION_TYPE,
    JOURNAL_TYPE)

from .l10n_br_account_product import (
    PRODUCT_FISCAL_TYPE,
    PRODUCT_FISCAL_TYPE_DEFAULT)
from .product import PRODUCT_ORIGIN
from openerp.addons.l10n_br_account_product.sped.nfe.validator import txt


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    @api.depends('invoice_line.price_subtotal', 'tax_line.amount')
    def _compute_amount(self):
        self.icms_base = 0.0
        self.icms_base_other = 0.0
        self.icms_value = 0.0
        self.icms_st_base = 0.0
        self.icms_st_value = 0.0
        self.ipi_base = sum(line.ipi_base for line in self.invoice_line)
        self.ipi_base_other = sum(line.ipi_base_other for line in self.invoice_line)
        self.ipi_value = sum(line.ipi_value for line in self.invoice_line)
        self.pis_base = sum(line.pis_base for line in self.invoice_line)
        self.pis_value = sum(line.pis_value for line in self.invoice_line)
        self.cofins_base = sum(line.cofins_base for line in self.invoice_line)
        self.cofins_value = sum(line.cofins_value for line in self.invoice_line)
        self.ii_value = sum(line.ii_value for line in self.invoice_line)
        self.amount_discount = sum(line.discount_value for line in self.invoice_line)
        self.amount_insurance = sum(line.insurance_value for line in self.invoice_line)
        self.amount_costs = sum(line.other_costs_value for line in self.invoice_line)
        self.amount_total_taxes = sum(line.total_taxes for line in self.invoice_line)
        self.amount_gross = sum(line.price_gross for line in self.invoice_line)
        self.amount_freight = sum(line.freight_value for line in self.invoice_line)
        self.amount_tax_discount = 0.0
        self.amount_untaxed = sum(line.price_total for line in self.invoice_line)
        self.amount_tax = sum(tax.amount for tax in self.tax_line if not tax.tax_code_id.tax_discount)
        self.amount_total = self.amount_tax + self.amount_untaxed

        for line in self.invoice_line:
            if line.icms_cst_id.code not in ('101', '102', '201', '202', '300', '500'):
                self.icms_base += line.icms_base
                self.icms_base_other += line.icms_base_other
                self.icms_value += line.icms_value
            else:
                self.icms_base += 0.00
                self.icms_base_other += 0.00
                self.icms_value += 0.00
            self.icms_st_base += line.icms_st_base
            self.icms_st_value += line.icms_st_value

    @api.model
    @api.returns('l10n_br_account.fiscal_category')
    def _default_fiscal_category(self):
        DEFAULT_FCATEGORY_PRODUCT = {
            'in_invoice': 'in_invoice_fiscal_category_id',
            'out_invoice': 'out_invoice_fiscal_category_id',
            'in_refund': 'in_refund_fiscal_category_id',
            'out_refund': 'out_refund_fiscal_category_id'
        }
        default_fo_category = {'product': DEFAULT_FCATEGORY_PRODUCT}
        invoice_type = self._context.get('type', 'out_invoice')
        invoice_fiscal_type = self._context.get('fiscal_type', 'product')
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company[default_fo_category[invoice_fiscal_type][invoice_type]]

    @api.model
    def _default_fiscal_document(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.product_invoice_id

    @api.model
    def _default_nfe_version(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.nfe_version

    @api.model
    def _default_fiscal_document_serie(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        fiscal_document_series = [doc_serie for doc_serie in
            company.document_serie_product_ids if
            doc_serie.fiscal_document_id.id ==
            company.product_invoice_id.id and doc_serie.active]
        #if not fiscal_document_series:
            #TODO Adicionar uma mensagem caso não tenha serie
        return fiscal_document_series[0]

    @api.one
    @api.depends('invoice_line.cfop_id')
    def _compute_cfops(self):
        lines = self.env['l10n_br_account_product.cfop']
        for line in self.invoice_line:
            if line.cfop_id:
                lines |= line.cfop_id
        self.cfop_ids = (lines).sorted()

    nfe_version = fields.Selection(
        [('1.10', '1.10'), ('2.00', '2.00'), ('3.10', '3.10')],
        u'Versão NFe', readonly=True, default=_default_nfe_version,
        states={'draft': [('readonly', False)]}, required=True)
    date_hour_invoice = fields.Datetime(
        u'Data e hora de emissão', readonly=True,
        states={'draft': [('readonly', False)]},
        select=True, help="Deixe em branco para usar a data atual")
    ind_final = fields.Selection([
        ('0', u'Não'),
        ('1', u'Consumidor final')
        ], u'Operação com Consumidor final', readonly=True,
        states={'draft': [('readonly', False)]}, required=False,
        help=u'Indica operação com Consumidor final.', default='0')
    ind_pres = fields.Selection([
        ('0', u'Não se aplica'),
        ('1', u'Operação presencial'),
        ('2', u'Operação não presencial, pela Internet'),
        ('3', u'Operação não presencial, Teleatendimento'),
        ('4', u'NFC-e em operação com entrega em domicílio'),
        ('9', u'Operação não presencial, outros'),
        ], u'Tipo de operação', readonly=True,
        states={'draft': [('readonly', False)]}, required=False,
        help=u'Indicador de presença do comprador no \
        \nestabelecimento comercial no momento \
        \nda operação.', default='0')
    fiscal_document_id = fields.Many2one(
        'l10n_br_account.fiscal.document', 'Documento', readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_document)
    document_serie_id = fields.Many2one(
        'l10n_br_account.document.serie', u'Série',
        domain="[('fiscal_document_id', '=', fiscal_document_id),\
        ('company_id','=',company_id)]", readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_document_serie)
    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal',
        readonly=True, states={'draft': [('readonly', False)]},
        default=_default_fiscal_category)
    date_in_out = fields.Datetime(u'Data de Entrada/Saida', readonly=True,
        states={'draft': [('readonly', False)]}, select=True, copy=False,
        help="Deixe em branco para usar a data atual")
    partner_shipping_id = fields.Many2one(
        'res.partner', 'Delivery Address',
        readonly=True, required=True,
        states={'draft': [('readonly', False)]},
        help="Delivery address for current sales order.")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('proforma', 'Pro-forma'),
        ('proforma2', 'Pro-forma'),
        ('sefaz_export', 'Enviar para Receita'),
        ('sefaz_exception', 'Erro de autorização da Receita'),
        ('sefaz_cancelled', u'Cancelado no Sefaz'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled')
        ], 'State', select=True, readonly=True,
        help=' * The \'Draft\' state is used when a user is encoding a new and unconfirmed Invoice. \
        \n* The \'Pro-forma\' when invoice is in Pro-forma state,invoice does not have an invoice number. \
        \n* The \'Open\' state is used when user create invoice,a invoice number is generated.Its in open state till user does not pay invoice. \
        \n* The \'Paid\' state is set automatically when invoice is paid.\
        \n* The \'sefaz_out\' Gerado aquivo de exportação para sistema daReceita.\
        \n* The \'sefaz_aut\' Recebido arquivo de autolização da Receita.\
        \n* The \'Cancelled\' state is used when user cancel invoice.')
    fiscal_type = fields.Selection(PRODUCT_FISCAL_TYPE,
        'Tipo Fiscal', required=True, default=PRODUCT_FISCAL_TYPE_DEFAULT)
    partner_shipping_id = fields.Many2one(
        'res.partner', 'Endereço de Entrega', readonly=True,
        states={'draft': [('readonly', False)]},
        help="Shipping address for current sales order.")
    shipping_state_id = fields.Many2one('res.country.state', 'Estado de Embarque')
    shipping_location = fields.Char('Local de Embarque', size=32)
    nfe_purpose = fields.Selection(
        [('1', 'Normal'),
         ('2', 'Complementar'),
         ('3', 'Ajuste')], 'Finalidade da Emissão', readonly=True,
        states={'draft': [('readonly', False)]}, default='1')
    nfe_access_key = fields.Char(
        'Chave de Acesso NFE', size=44,
        readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    nfe_protocol_number = fields.Char(
        'Protocolo', size=15, readonly=True,
        copy=False, states={'draft': [('readonly', False)]})
    nfe_status = fields.Char('Status na Sefaz', size=44, readonly=True,
        copy=False)
    nfe_date = fields.Datetime('Data do Status NFE', readonly=True,
        copy=False)
    nfe_export_date = fields.Datetime('Exportação NFE', readonly=True)
    cfop_ids = fields.Many2many(
        'l10n_br_account_product.cfop', string='CFOP',
        copy=False, compute='_compute_cfops')
    fiscal_document_related_ids = fields.One2many(
        'l10n_br_account_product.document.related', 'invoice_id',
        'Fiscal Document Related', readonly=True,
        states={'draft': [('readonly', False)]})
    carrier_name = fields.Char('Nome Transportadora', size=32)
    vehicle_plate = fields.Char('Placa do Veiculo', size=7)
    vehicle_state_id = fields.Many2one('res.country.state', 'UF da Placa')
    vehicle_l10n_br_city_id = fields.Many2one('l10n_br_base.city',
        'Municipio', domain="[('state_id', '=', vehicle_state_id)]")
    amount_untaxed = fields.Float(string='Untaxed', store=True,
        digits=dp.get_precision('Account'), compapply_fiscal_mappingute='_compute_amount')
    amount_tax = fields.Float(string='Tax', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    amount_total = fields.Float(string='Total', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    amount_gross = fields.Float(string='Vlr. Bruto', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        readonly=True)
    amount_discount = fields.Float(string='Desconto', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    icms_base = fields.Float(string='Base ICMS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    icms_base_other = fields.Float(string='Base ICMS Outras', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        readonly=True)
    icms_value = fields.Float(
        string='Valor ICMS', digits=dp.get_precision('Account'),
        compute='_compute_amount', store=True)
    icms_st_base = fields.Float(string='Base ICMS ST', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    icms_st_value = fields.Float(string='Valor ICMS ST', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    ipi_base = fields.Float(
        string='Base IPI', store=True, digits=dp.get_precision('Account'),
        compute='_compute_amount')
    ipi_base_other = fields.Float(
        string="Base IPI Outras", store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    ipi_value = fields.Float(
        string='Valor IPI', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    pis_base = fields.Float(
        string='Base PIS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    pis_value = fields.Float(
        string='Valor PIS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    cofins_base = fields.Float(
        string='Base COFINS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    cofins_value = fields.Float(
        string='Valor COFINS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        readonly=True)
    ii_value = fields.Float(
        string='Valor II', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        readonly=True)
    weight = fields.Float(
        string='Gross weight', states={'draft': [('readonly', False)]},
        help="The gross weight in Kg.", readonly=True)
    weight_net = fields.Float(
        'Net weight', help="The net weight in Kg.",
        readonly=True, states={'draft': [('readonly', False)]})
    number_of_packages = fields.Integer(
        'Volume', readonly=True, states={'draft': [('readonly', False)]})
    kind_of_packages = fields.Char(
        'Espécie', size=60, readonly=True, states={'draft': [('readonly', False)]})
    brand_of_packages = fields.Char(
        'Brand',  size=60, readonly=True, states={'draft': [('readonly', False)]})
    notation_of_packages = fields.Char(
        'Numeração', size=60, readonly=True, states={'draft': [('readonly', False)]})
    amount_insurance = fields.Float(
        string='Valor do Seguro', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    amount_freight = fields.Float(
        string='Valor do Seguro', store=True,
        digits=dp.get_precision('Account'), cfiscal_ompute='_compute_amount2')
    amount_costs = fields.Float(
        string='Outros Custos', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    amount_total_taxes = fields.Float(string='Total de Tributos', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

    #TODO não foi migrado por causa do bug github.com/odoo/odoo/issues/1711
    def fields_view_get(self, cr, uid, view_id=None, view_type=False,
                        context=None, toolbar=False, submenu=False):
        result = super(AccountInvoice, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type, context=context,
            toolbar=toolbar, submenu=submenu)

        if context is None:
            context = {}

        if not view_type:
            view_id = self.pool.get('ir.ui.view').search(
                cr, uid, [('name', '=', 'account.invoice.tree')])
            view_type = 'tree'

        if view_type == 'form':
            eview = etree.fromstring(result['arch'])

            if 'type' in context.keys():
                fiscal_types = eview.xpath("//field[@name='invoice_line']")
                for fiscal_type in fiscal_types:
                    fiscal_type.set(
                        'context', "{'type': '%s', 'fiscal_type': '%s'}" % (
                            context['type'],
                            context.get('fiscal_type', 'product')))

                fiscal_categories = eview.xpath(
                    "//field[@name='fiscal_category_id']")
                for fiscal_category_id in fiscal_categories:
                    fiscal_category_id.set(
                        'domain',
                        """[('fiscal_type', '=', '%s'), ('type', '=', '%s'),
                        ('state', '=', 'approved'),
                        ('journal_type', '=', '%s')]"""
                        % (context.get('fiscal_type', 'product'),
                            OPERATION_TYPE[context['type']],
                            JOURNAL_TYPE[context['type']]))
                    fiscal_category_id.set('required', '1')

                document_series = eview.xpath(
                    "//field[@name='document_serie_id']")
                for document_serie_id in document_series:
                    document_serie_id.set(
                        'domain', "[('fiscal_type', '=', '%s')]"
                        % (context.get('fiscal_type', 'product')))

            if context.get('fiscal_type', False):
                delivery_infos = eview.xpath("//group[@name='delivery_info']")
                for delivery_info in delivery_infos:
                    delivery_info.set('invisible', '1')

            result['arch'] = etree.tostring(eview)

        if view_type == 'tree':
            doc = etree.XML(result['arch'])
            nodes = doc.xpath("//field[@name='partner_id']")
            partner_string = _('Customer')
            if context.get('type', 'out_invoice') in ('in_invoice', 'in_refund'):
                partner_string = _('Supplier')
            for node in nodes:
                node.set('string', partner_string)
            result['arch'] = etree.tostring(doc)
        return result

    #TODO Imaginar em não apagar o internal number para nao ter a necessidade de voltar a numeracão
    @api.multi
    def action_cancel_draft(self):
        result = super(AccountInvoice, self).action_cancel_draft()
        self.write({
            'internal_number': False,
            'nfe_access_key': False,
            'nfe_status': False,
            'nfe_date': False,
            'nfe_export_date': False})
        return result

    def nfe_check(self, cr, uid, ids, context=None):
        result = txt.validate(cr, uid, ids, context)
        return result

    @api.multi
    def action_move_create(self):
        result = super(AccountInvoice, self).action_move_create()
        for invoice in self:
            date_time_now = fields.datetime.now()

            if not invoice.date_hour_invoice:
                invoice.write({'date_hour_invoice': date_time_now})

            if not invoice.date_in_out:
                invoice.write({'date_in_out': date_time_now})
        return result

    @api.multi
    def onchange_fiscal_document_id(self, fiscal_document_id,
                                    company_id, issuer, fiscal_type):
        result = {'value': {'document_serie_id': False}}
        company = self.env['res.company'].browse(company_id)

        if issuer == '0':
            series = [doc_serie for doc_serie in
                company.document_serie_product_ids if
                doc_serie.fiscal_document_id.id ==
                fiscal_document_id and doc_serie.active]

            #TODO Alerta se nao tiver serie
            if not series:
                action = self.env.ref('l10n_br_account.action_l10n_br_account_document_serie_form')
                msg = _(u'Você deve ser uma série de documento fiscal para este documento fiscal.')
                raise RedirectWarning(msg, action.id, _(u'Criar uma nova série'))
            result['value']['document_serie_id'] = series[0].id
        return result

    @api.multi
    def action_date_assign(self):
        for invoice in self:
            if invoice.date_hour_invoice:
                aux = datetime.datetime.strptime(invoice.date_hour_invoice, '%Y-%m-%d %H:%M:%S').date()
                invoice.date_invoice = str(aux)
            result = invoice.onchange_payment_term_date_invoice(
                invoice.payment_term.id, invoice.date_invoice)
            if result and result.get('value'):
                invoice.write(result['value'])
        return True


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_id', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'freight_value',
                 'insurance_value', 'freight_value', 'other_costs_value',
                 'invoice_id.currency_id')
    def _compute_price(self):
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = self.invoice_line_tax_id.compute_all(
            price, self.quantity, product=self.product_id.id,
            partner=self.invoice_id.partner_id,
            fiscal_position=self.fiscal_position,
            insurance_value=self.insurance_value,
            freight_value=self.freight_value,
            other_costs_value=self.other_costs_value)
        self.price_subtotal = 0.0
        self.price_total = 0.0
        self.price_gross = 0.0
        self.discount_value = 0.0
        if self.invoice_id:
            self.price_subtotal = self.invoice_id.currency_id.round(
                taxes['total'] - taxes['total_tax_discount'])
            self.price_total = self.invoice_id.currency_id.round(
                taxes['total'])
            self.price_gross = self.invoice_id.currency_id.round(
                self.price_unit * self.quantity)
            self.discount_value = self.invoice_id.currency_id.round(
                self.price_gross - taxes['total'])

    date_invoice = fields.Datetime(
        'Invoice Date', readonly=True, states={'draft':[('readonly',False)]},
        select=True, help="Keep empty to use the current date")
    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal')
    fiscal_position = fields.Many2one(
        'account.fiscal.position', u'Posição Fiscal',
        domain="[('fiscal_category_id','=',fiscal_category_id)]")
    cfop_id = fields.Many2one('l10n_br_account_product.cfop', 'CFOP')
    fiscal_classification_id = fields.Many2one(
        'account.product.fiscal.classification', 'Classificação Fiscal')
    fci = fields.Char('FCI do Produto', size=36)
    import_declaration_ids = fields.One2many(
        'l10n_br_account_product.import.declaration',
        'invoice_line_id', u'Declaração de Importação')
    product_type = fields.Selection(
        [('product', 'Produto'), ('service', u'Serviço')],
        'Tipo do Produto', required=True, default='product')
    discount_value = fields.Float(
        string='Vlr. desconto', store=True, compute='_compute_price',
        digits=dp.get_precision('Account'))
    price_total = fields.Float(
        string='Total', store=True, compute='_compute_price',
        digits=dp.get_precision('Account'))
    price_gross = fields.Float(
        string='Vlr. Bruto', store=True, compute='_compute_price',
        digits=dp.get_precision('Account'))
    price_subtotal = fields.Float(
        string='Subtotal', store=True, compute='_compute_price',
        digits=dp.get_precision('Account'))
    price_total = fields.Float(
        string='Total', store=True, compute='_compute_price',
        digits=dp.get_precision('Account'))
    total_taxes = fields.Float(
        string='Total de Tributos', requeried=True, default=0.00,
        digits=dp.get_precision('Account'))
    icms_manual = fields.Boolean('ICMS Manual?', default=False)
    icms_origin = fields.Selection(PRODUCT_ORIGIN, 'Origem', default='0')
    icms_base_type = fields.Selection(
        [('0', 'Margem Valor Agregado (%)'), ('1', 'Pauta (valor)'),
        ('2', 'Preço Tabelado Máximo (valor)'),
        ('3', 'Valor da Operação')],
        'Tipo Base ICMS', required=True, default='0')
    icms_base = fields.Float('Base ICMS', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_base_other = fields.Float(
        'Base ICMS Outras', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_value = fields.Float(
        'Valor ICMS', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_percent = fields.Float(
        'Perc ICMS', digits=dp.get_precision('Discount'), default=0.00)
    icms_percent_reduction = fields.Float(
        'Perc Redução de Base ICMS', digits=dp.get_precision('Discount'),
        default=0.00)
    icms_st_base_type = fields.Selection(
        [('0', 'Preço tabelado ou máximo  sugerido'),
         ('1', 'Lista Negativa (valor)'),
         ('2', 'Lista Positiva (valor)'), ('3', 'Lista Neutra (valor)'),
         ('4', 'Margem Valor Agregado (%)'), ('5', 'Pauta (valor)')],
        'Tipo Base ICMS ST', required=True, default='4')
    icms_st_value = fields.Float(
        'Valor ICMS ST', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_st_base = fields.Float(
        'Base ICMS ST', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_st_percent = fields.Float(
        'Percentual ICMS ST', digits=dp.get_precision('Discount'),
        default=0.00)
    icms_st_percent_reduction = fields.Float(
        'Perc Redução de Base ICMS ST',
        digits=dp.get_precision('Discount'), default=0.00)
    icms_st_mva = fields.Float(
        'MVA ICMS ST', digits=dp.get_precision('Discount'), default=0.00)
    icms_st_base_other = fields.Float(
        'Base ICMS ST Outras', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_cst_id = fields.Many2one(
        'account.tax.code', 'CST ICMS', domain=[('domain', '=', 'icms')])
    issqn_manual = fields.Boolean('ISSQN Manual?', default=False)
    issqn_type = fields.Selection(
        [('N', 'Normal'), ('R', 'Retida'),
         ('S', 'Substituta'), ('I', 'Isenta')], 'Tipo do ISSQN',
        required=True, default='N')
    service_type_id = fields.Many2one(
        'l10n_br_account.service.type', 'Tipo de Serviço')
    issqn_base = fields.Float(
        'Base ISSQN', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    issqn_percent = fields.Float(
        'Perc ISSQN', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    issqn_value = fields.Float(
        'Valor ISSQN', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ipi_manual = fields.Boolean('IPI Manual?', default=False)
    ipi_type = fields.Selection(
        [('percent', 'Percentual'), ('quantity', 'Em Valor')],
        'Tipo do IPI', required=True, default='percent')
    ipi_base = fields.Float(
        'Base IPI', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ipi_base_other = fields.Float(
        'Base IPI Outras', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ipi_value = fields.Float(
        'Valor IPI', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ipi_percent = fields.Float(
        'Perc IPI', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    ipi_cst_id = fields.Many2one(
        'account.tax.code', 'CST IPI', domain=[('domain', '=', 'ipi')])
    pis_manual = fields.Boolean('PIS Manual?', default=False)
    pis_type = fields.Selection(
        [('percent', 'Percentual'), ('quantity', 'Em Valor')],
        'Tipo do PIS', required=True, default='percent')
    pis_base = fields.Float('Base PIS', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    pis_base_other = fields.Float(
        'Base PIS Outras', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    pis_value = fields.Float(
        'Valor PIS', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    pis_percent = fields.Float(
        'Perc PIS', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    pis_cst_id = fields.Many2one(
        'account.tax.code', 'CST PIS', domain=[('domain', '=', 'pis')])
    pis_st_type = fields.Selection(
        [('percent', 'Percentual'), ('quantity', 'Em Valor')],
        'Tipo do PIS ST', required=True, default='percent')
    pis_st_base = fields.Float(
        'Base PIS ST', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    pis_st_percent = fields.Float(
        'Perc PIS ST', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    pis_st_value = fields.Float(
        'Valor PIS ST', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    cofins_manual = fields.Boolean('COFINS Manual?', default=False)
    cofins_type = fields.Selection(
        [('percent', 'Percentual'), ('quantity', 'Em Valor')],
        'Tipo do COFINS', required=True, default='percent')
    cofins_base = fields.Float('Base COFINS', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    cofins_base_other = fields.Float(
        'Base COFINS Outras', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    cofins_value = fields.Float(
        'Valor COFINS', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    cofins_percent = fields.Float(
        'Perc COFINS', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    cofins_cst_id = fields.Many2one(
        'account.tax.code', 'CST PIS', domain=[('domain', '=', 'cofins')])
    cofins_st_type = fields.Selection(
        [('percent', 'Percentual'), ('quantity', 'Em Valor')],
        'Tipo do COFINS ST', required=True, default='percent')
    cofins_st_base = fields.Float(
        'Base COFINS ST', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    cofins_st_percent = fields.Float(
        'Perc COFINS ST', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    cofins_st_value = fields.Float(
        'Valor COFINS ST', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ii_base = fields.Float(
        'Base II', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ii_value = fields.Float(
        'Valor II', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ii_iof = fields.Float(
        'Valor IOF', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ii_customhouse_charges = fields.Float(
        'Depesas Atuaneiras', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    insurance_value = fields.Float(
        'Valor do Seguro', digits=dp.get_precision('Account'), default=0.00)
    other_costs_value = fields.Float(
        'Outros Custos', digits=dp.get_precision('Account'), default=0.00)
    freight_value = fields.Float(
        'Frete', digits=dp.get_precision('Account'), default=0.00)

    def _amount_tax_icms(self, tax=None):
        result = {
            'icms_base_type': '0',
            'icms_base': tax.get('total_base', 0.0),
            'icms_base_other': tax.get('total_base_other', 0.0),
            'icms_value': tax.get('amount', 0.0),
            'icms_percent': tax.get('percent', 0.0) * 100,
            'icms_percent_reduction': tax.get('base_reduction') * 100,
        }
        return result

    def _amount_tax_icmsst(self, tax=None):
        result = {
            'icms_st_value': tax.get('amount', 0.0),
            'icms_st_base': tax.get('total_base', 0.0),
            'icms_st_percent': tax.get('icms_st_percent', 0.0) * 100,
            'icms_st_percent_reduction': tax.get('icms_st_percent_reduction', 0.0) * 100,
            'icms_st_mva': tax.get('amount_mva', 0.0) * 100,
            'icms_st_base_other': tax.get('icms_st_base_other', 0.0),
        }
        return result

    def _amount_tax_ipi(self, tax=None):
        result = {
            'ipi_type': tax.get('type'),
            'ipi_base': tax.get('total_base', 0.0),
            'ipi_value': tax.get('amount', 0.0),
            'ipi_percent': tax.get('percent', 0.0) * 100,
        }
        return result

    def _amount_tax_cofins(self, tax=None):
        result = {
            'cofins_base': tax.get('total_base', 0.0),
            'cofins_base_other': tax.get('total_base_other', 0.0),
            'cofins_value': tax.get('amount', 0.0),
            'cofins_percent': tax.get('percent', 0.0) * 100,
        }
        return result

    def _amount_tax_cofinsst(self, tax=None):
        result = {
            'cofins_st_type': 'percent',
            'cofins_st_base': 0.0,
            'cofins_st_percent': 0.0,
            'cofins_st_value': 0.0,
        }
        return result

    def _amount_tax_pis(self, tax=None):
        result = {
            'pis_base': tax.get('total_base', 0.0),
            'pis_base_other': tax.get('total_base_other', 0.0),
            'pis_value': tax.get('amount', 0.0),
            'pis_percent': tax.get('percent', 0.0) * 100,
        }
        return result

    def _amount_tax_pisst(self, tax=None):
        result = {
            'pis_st_type': 'percent',
            'pis_st_base': 0.0,
            'pis_st_percent': 0.0,
            'pis_st_value': 0.0,
        }
        return result

    def _amount_tax_ii(self, tax=None):
        result = {
            'ii_base': 0.0,
            'ii_value': 0.0,
        }
        return result

    def _amount_tax_issqn(self, tax=None):

        # TODO deixar dinamico a definição do tipo do ISSQN
        # assim como todos os impostos
        issqn_type = 'N'
        if not tax.get('amount'):
            issqn_type = 'I'

        result = {
            'issqn_type': issqn_type,
            'issqn_base': tax.get('total_base', 0.0),
            'issqn_percent': tax.get('percent', 0.0) * 100,
            'issqn_value': tax.get('amount', 0.0),
        }
        return result

    @api.multi
    def _get_tax_codes(self, product_id, fiscal_position, taxes):

        result = {}

        ctx = dict(self.env.context)
        ctx.update({'use_domain': ('use_invoice', '=', True)})

        if fiscal_position.fiscal_category_id.journal_type in ('sale', 'sale_refund'):
            ctx.update({'type_tax_use': 'sale'})
        else:
            ctx.update({'type_tax_use': 'purchase'})

        product = self.env['product.product'].browse(product_id)
        ctx.update({'fiscal_type': product.fiscal_type})
        result['cfop_id'] = fiscal_position.cfop_id.id

        tax_codes = fiscal_position.with_context(
            ctx).map_tax_code(product_id, taxes)

        result['icms_cst_id'] = tax_codes.get('icms')
        result['ipi_cst_id'] = tax_codes.get('ipi')
        result['pis_cst_id'] = tax_codes.get('pis')
        result['cofins_cst_id'] = tax_codes.get('cofins')
        return result

    #TODO
    @api.multi
    def _validate_taxes(self, values):
        """Verifica se o valor dos campos dos impostos estão sincronizados
        com os impostos do OpenERP"""
        context = self.env.context
        tax_obj = self.env['account.tax']

        if not values.get('product_id') or not values.get('quantity') \
        or not values.get('fiscal_position'):
            return {}

        result = {
            'product_type': 'product',
            'service_type_id': None,
            'fiscal_classification_id': None,
            'fci': None,
        }

        partner_id = None
        if values.get('partner_id'):
            partner_id = values.get('partner_id')
        else:
            if values.get('invoice_id'):
                invoice = self.env['account.invoice'].browse(
                    values.get('invoice_id'))

                partner_id = invoice.partner_id.id

        taxes = self.env['account.tax'].browse(
            values.get('invoice_line_tax_id', [[6, 0, []]])[0][2])
        fiscal_position = self.env['account.fiscal.position'].browse(
            values.get('fiscal_position'))

        price_unit = values.get('price_unit', 0.0)
        price = price_unit * (1 - values.get('discount', 0.0) / 100.0)

        taxes_calculed = taxes.compute_all(
            price, values.get('quantity', 0.0),
            values.get('product_id'), partner_id,
            fiscal_position=fiscal_position,
            insurance_value=values.get('insurance_value', 0.0),
            freight_value=values.get('freight_value', 0.0),
            other_costs_value=values.get('other_costs_value', 0.0))

        if values.get('product_id'):
            obj_product = self.pool.get('product.product').browse(
                self._cr, self._uid, values.get('product_id'), context=context)
            if obj_product.type == 'service':
                result['product_type'] = 'service'
                result['service_type_id'] = obj_product.service_type_id.id
            else:
                result['product_type'] = 'product'
            if obj_product.ncm_id:
                result['fiscal_classification_id'] = obj_product.ncm_id.id

            if obj_product.fci:
                result['fci'] = obj_product.fci

            result['icms_origin'] = obj_product.origin
            result['total_taxes'] = taxes_calculed['total_taxes']

        for tax in taxes_calculed['taxes']:
            try:
                amount_tax = getattr(
                    self, '_amount_tax_%s' % tax.get('domain', ''))
                result.update(amount_tax(tax))
            except AttributeError:
                # Caso não exista campos especificos dos impostos
                # no documento fiscal, os mesmos são calculados.
                continue

        result.update(self._get_tax_codes(
            values.get('product_id'), fiscal_position, taxes))
        return result

    @api.multi
    def _fiscal_position_map(self, result, **kwargs):
        ctx = dict(self.env.context)
        ctx.update({'use_domain': ('use_invoice', '=', True)})

        result_rule = self.env[
            'account.fiscal.position.rule'].with_context(
                ctx).apply_fiscal_mapping(result, **kwargs)
        return result_rule

    @api.multi
    def product_id_change(self, product, uom_id, qty=0, name='',
                        type='out_invoice', partner_id=False,
                        fposition_id=False, price_unit=False,
                        currency_id=False, company_id=None):

        result = super(AccountInvoiceLine, self).product_id_change(
            product, uom_id, qty, name, type, partner_id,
            fposition_id, price_unit, currency_id, company_id)
        return result

    @api.multi
    def onchange_fiscal_position(self, partner_id, company_id, product_id,
                                 fiscal_category_id, account_id, quantity,
                                 price_unit):
        result = {'value': {}}
        ctx = dict(self.env.context)

        kwargs = {
            'company_id': company_id,
            'partner_id': partner_id,
            'partner_invoice_id': partner_id,
            'fiscal_category_id': fiscal_category_id,
            'context': ctx
        }
        result.update(self._fiscal_position_map(result, **kwargs))
        fiscal_position = result['value'].get('fiscal_position')

        if product_id and fiscal_position:

            obj_product = self.env['product.product'].browse(product_id)
            obj_fposition = self.env['account.fiscal.position'].browse(
                fiscal_position)
            ctx['fiscal_type'] = obj_product.fiscal_type
            ctx['product_id'] = product_id
            if ctx.get('type') in ('out_invoice', 'out_refund'):
                ctx['type_tax_use'] = 'sale'
                taxes = obj_product.taxes_id + self.env['account.account'].browse(kwargs.get('account_id')).tax_ids
            else:
                ctx['type_tax_use'] = 'purchase'
                taxes = obj_product.supplier_taxes_id + self.env['account.account'].browse(kwargs.get('account_id')).tax_ids

            tax_ids = obj_fposition.with_context(ctx).map_tax(taxes)

            result['value']['invoice_line_tax_id'] = tax_ids
            values = {
                'partner_id': partner_id,
                'company_id': company_id,
                'product_id': product_id,
                'quantity': quantity,
                'price_unit': price_unit,
                'fiscal_position': result['value'].get('fiscal_position'),
                'invoice_line_tax_id': [
                    [6, 0, [x.id for x in result['value']['invoice_line_tax_id']]]],
            }
            result['value'].update(self._validate_taxes(values))

        return result

    @api.model
    def create(self, vals):
        vals.update(self._validate_taxes(vals))
        return super(AccountInvoiceLine, self).create(vals)

    #TODO comentado por causa deste bug https://github.com/odoo/odoo/issues/2197
    @api.multi
    def write(self, vals):
        vals.update(self._validate_taxes(vals))
        return super(AccountInvoiceLine, self).write(vals)


class AccountInvoiceTax(models.Model):
    _inherit = 'account.invoice.tax'

    @api.v8
    def compute(self, invoice):
        tax_grouped = {}
        currency = invoice.currency_id.with_context(date=invoice.date_invoice or fields.Date.context_today(invoice))
        company_currency = invoice.company_id.currency_id
        for line in invoice.invoice_line:
            taxes = line.invoice_line_tax_id.compute_all(
                (line.price_unit * (1 - (line.discount or 0.0) / 100.0)),
                line.quantity, line.product_id.id, invoice.partner_id,
                fiscal_position=line.fiscal_position,
                insurance_value=line.insurance_value,
                freight_value=line.freight_value,
                other_costs_value=line.other_costs_value)['taxes']
            for tax in taxes:
                val = {
                    'invoice_id': invoice.id,
                    'name': tax['name'],
                    'amount': tax['amount'],
                    'manual': False,
                    'sequence': tax['sequence'],
                    'base': currency.round(tax['price_unit'] * line['quantity']),
                }
                if invoice.type in ('out_invoice', 'in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = currency.compute(val['base'] * tax['base_sign'], company_currency, round=False)
                    val['tax_amount'] = currency.compute(val['amount'] * tax['tax_sign'], company_currency, round=False)
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_collected_id']
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = currency.compute(val['base'] * tax['ref_base_sign'], company_currency, round=False)
                    val['tax_amount'] = currency.compute(val['amount'] * tax['ref_tax_sign'], company_currency, round=False)
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_paid_id']

                key = (val['tax_code_id'], val['base_code_id'], val['account_id'], val['account_analytic_id'])
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']

        for t in tax_grouped.values():
            t['base'] = currency.round(t['base'])
            t['amount'] = currency.round(t['amount'])
            t['base_amount'] = currency.round(t['base_amount'])
            t['tax_amount'] = currency.round(t['tax_amount'])

        return tax_grouped
