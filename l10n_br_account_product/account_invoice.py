# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

import time

from openerp import models, fields, api, _
from openerp.addons import decimal_precision as dp
from openerp.exceptions import except_orm, Warning, RedirectWarning

from .l10n_br_account_product import (
    PRODUCT_FISCAL_TYPE,
    PRODUCT_FISCAL_TYPE_DEFAULT)
from .product import PRODUCT_ORIGIN
from .sped.nfe.validator import txt


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    @api.depends('invoice_line.price_subtotal', 'tax_line.amount')
    def _compute_amount(self):
        self.amount_untaxed = 0.0
        self.amount_tax = 0.0
        self.amount_tax_discount = 0.0
        self.amount_total = 0.0
        self.icms_base = 0.0
        self.icms_base_other = 0.0
        self.icms_value = 0.0
        self.icms_st_base = 0.0
        self.icms_st_value = 0.0
        self.ipi_base = 0.0
        self.ipi_base_other = 0.0
        self.ipi_value = 0.0
        self.pis_base = 0.0
        self.pis_value = 0.0
        self.cofins_base = 0.0
        self.cofins_value = 0.0
        self.ii_value = 0.0
        self.amount_discount = 0.0
        self.amount_insurance = 0.0
        self.amount_costs = 0.0
        self.amount_gross = 0.0
        self.amount_discount = 0.0
        self.amount_freight = 0.0

        for line in self.invoice_line:
            self.amount_untaxed += line.price_total
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
            self.ipi_base += line.ipi_base
            self.ipi_base_other += line.ipi_base_other
            self.ipi_value += line.ipi_value
            self.pis_base += line.pis_base
            self.pis_value += line.pis_value
            self.cofins_base += line.cofins_base
            self.cofins_value += line.cofins_value
            self.ii_value += line.ii_value
            self.amount_insurance += line.insurance_value
            self.amount_freight += line.freight_value
            self.amount_costs += line.other_costs_value
            self.amount_gross += line.price_gross
            self.amount_discount += line.discount_value

            for invoice_tax in self.tax_line:
                if not invoice_tax.tax_code_id.tax_discount:
                    self.amount_tax += invoice_tax.amount

            self.amount_total = self.amount_tax + self.amount_untaxed

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
    date_in_out = fields.Date(u'Data de Entrada/Saida', readonly=True,
        states={'draft': [('readonly', False)]}, select=True,
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
        states={'draft': [('readonly', False)]})
    nfe_status = fields.Char('Status na Sefaz', size=44, readonly=True,
        copy=False)
    nfe_date = fields.Datetime('Data do Status NFE', readonly=True,
        copy=False)
    nfe_export_date = fields.Datetime('Exportação NFE', readonly=True)
    cfop_ids = fields.Many2many('l10n_br_account_product.cfop', string='CFOP',
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
    icms_value = fields.Float(string='Valor ICMS',
        digits=dp.get_precision('Account'), compute='_compute_amount')
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
    amount_insurance = fields.Float(
        string='Valor do Seguro', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    amount_freight = fields.Float(
        string='Valor do Seguro', store=True,
        digits=dp.get_precision('Account'), cfiscal_ompute='_compute_amount2')
    amount_costs = fields.Float(
        string='Outros Custos', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')

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
            if not invoice.date_in_out:
                date_in_out = invoice.date_invoice or time.strftime('%Y-%m-%d')
                self.write({'date_in_out': date_in_out})
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


class AccountInvoiceLine(orm.Model):
    _inherit = 'account.invoice.line'

    def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            res[line.id] = {
                'price_subtotal': 0.0,
                'price_total': 0.0,
                'discount_value': 0.0,
                'price_gross': 0.0,
            }

            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(
                cr, uid, line.invoice_line_tax_id, price, line.quantity,
                line.product_id, line.invoice_id.partner_id,
                fiscal_position=line.fiscal_position,
                insurance_value=line.insurance_value,
                freight_value=line.freight_value,
                other_costs_value=line.other_costs_value)

            if line.invoice_id:
                currency = line.invoice_id.currency_id
                price_gross = cur_obj.round(cr, uid, currency,
                    line.price_unit * line.quantity)
                res[line.id].update({
                    'price_subtotal': cur_obj.round(
                        cr, uid, currency,
                        taxes['total'] - taxes['total_tax_discount']),
                    'price_total': cur_obj.round(
                        cr, uid, currency, taxes['total']),
                    'price_gross': price_gross,
                    'discount_value': (price_gross - taxes['total']),
                })

        return res

    _columns = {
        'fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria'),
        'fiscal_position': fields.many2one(
            'account.fiscal.position', u'Posição Fiscal',
            domain="[('fiscal_category_id','=',fiscal_category_id)]"),
        'import_declaration_ids': fields.one2many(
            'l10n_br_account_product.import.declaration',
            'invoice_line_id', u'Declaração de Importação'),
        'cfop_id': fields.many2one('l10n_br_account_product.cfop', 'CFOP'),
        'fiscal_classification_id': fields.many2one(
            'account.product.fiscal.classification', u'Classficação Fiscal'),
        'product_type': fields.selection(
            [('product', 'Produto'), ('service', u'Serviço')],
            'Tipo do Produto', required=True),
        'discount_value': fields.function(
            _amount_line, method=True, string='Vlr. desconto', type="float",
            digits_compute=dp.get_precision('Account'),
            store=True, multi='all'),
        'price_total': fields.function(
            _amount_line, method=True, string='Total', type="float",
            digits_compute=dp.get_precision('Account'),
            store=True, multi='all'),
        'price_gross': fields.function(
            _amount_line, method=True, string='Vlr. Bruto', type="float",
            digits_compute=dp.get_precision('Account'),
            store=True, multi='all'),
        'price_subtotal': fields.function(
            _amount_line, method=True, string='Subtotal', type="float",
            digits_compute=dp.get_precision('Account'),
            store=True, multi='all'),
        'price_total': fields.function(
            _amount_line, method=True, string='Total', type="float",
            digits_compute=dp.get_precision('Account'),
            store=True, multi='all'),
        'icms_manual': fields.boolean('ICMS Manual?'),
        'icms_origin': fields.selection(PRODUCT_ORIGIN, 'Origem'),
        'icms_base_type': fields.selection(
            [('0', 'Margem Valor Agregado (%)'), ('1', 'Pauta (valor)'),
            ('2', u'Preço Tabelado Máximo (valor)'),
            ('3', u'Valor da Operação')],
            'Tipo Base ICMS', required=True),
        'icms_base': fields.float('Base ICMS', required=True,
            digits_compute=dp.get_precision('Account')),
        'icms_base_other': fields.float('Base ICMS Outras', required=True,
            digits_compute=dp.get_precision('Account')),
        'icms_value': fields.float('Valor ICMS', required=True,
            digits_compute=dp.get_precision('Account')),
        'icms_percent': fields.float('Perc ICMS',
            digits_compute=dp.get_precision('Discount')),
        'icms_percent_reduction': fields.float(u'Perc Redução de Base ICMS',
            digits_compute=dp.get_precision('Discount')),
        'icms_st_base_type': fields.selection(
            [('0', u'Preço tabelado ou máximo  sugerido'),
            ('1', 'Lista Negativa (valor)'),
            ('2', 'Lista Positiva (valor)'), ('3', 'Lista Neutra (valor)'),
            ('4', 'Margem Valor Agregado (%)'), ('5', 'Pauta (valor)')],
            'Tipo Base ICMS ST', required=True),
        'icms_st_value': fields.float('Valor ICMS ST', required=True,
            digits_compute=dp.get_precision('Account')),
        'icms_st_base': fields.float('Base ICMS ST', required=True,
            digits_compute=dp.get_precision('Account')),
        'icms_st_percent': fields.float('Percentual ICMS ST',
            digits_compute=dp.get_precision('Discount')),
        'icms_st_percent_reduction': fields.float(
            u'Perc Redução de Base ICMS ST',
            digits_compute=dp.get_precision('Discount')),
        'icms_st_mva': fields.float('MVA ICMS ST',
            digits_compute=dp.get_precision('Discount')),
        'icms_st_base_other': fields.float('Base ICMS ST Outras',
            required=True, digits_compute=dp.get_precision('Account')),
        'icms_cst_id': fields.many2one('account.tax.code', 'CST ICMS',
            domain=[('domain', '=', 'icms')]),
        'issqn_manual': fields.boolean('ISSQN Manual?'),
        'issqn_type': fields.selection(
            [('N', 'Normal'), ('R', 'Retida'),
            ('S', 'Substituta'), ('I', 'Isenta')], 'Tipo do ISSQN',
            required=True),
        'service_type_id': fields.many2one(
            'l10n_br_account.service.type', u'Tipo de Serviço'),
        'issqn_base': fields.float('Base ISSQN', required=True,
            digits_compute=dp.get_precision('Account')),
        'issqn_percent': fields.float('Perc ISSQN', required=True,
            digits_compute=dp.get_precision('Discount')),
        'issqn_value': fields.float('Valor ISSQN', required=True,
            digits_compute=dp.get_precision('Account')),
        'ipi_manual': fields.boolean('IPI Manual?'),
        'ipi_type': fields.selection(
            [('percent', 'Percentual'), ('quantity', 'Em Valor')],
            'Tipo do IPI', required=True),
        'ipi_base': fields.float('Base IPI', required=True,
            digits_compute=dp.get_precision('Account')),
        'ipi_base_other': fields.float('Base IPI Outras', required=True,
            digits_compute=dp.get_precision('Account')),
        'ipi_value': fields.float('Valor IPI', required=True,
            digits_compute=dp.get_precision('Account')),
        'ipi_percent': fields.float('Perc IPI', required=True,
            digits_compute=dp.get_precision('Discount')),
        'ipi_cst_id': fields.many2one('account.tax.code', 'CST IPI',
            domain=[('domain', '=', 'ipi')]),
        'pis_manual': fields.boolean('PIS Manual?'),
        'pis_type': fields.selection(
            [('percent', 'Percentual'), ('quantity', 'Em Valor')],
            'Tipo do PIS', required=True),
        'pis_base': fields.float('Base PIS', required=True,
            digits_compute=dp.get_precision('Account')),
        'pis_base_other': fields.float('Base PIS Outras', required=True,
            digits_compute=dp.get_precision('Account')),
        'pis_value': fields.float('Valor PIS', required=True,
            digits_compute=dp.get_precision('Account')),
        'pis_percent': fields.float('Perc PIS', required=True,
            digits_compute=dp.get_precision('Discount')),
        'pis_cst_id': fields.many2one('account.tax.code', 'CST PIS',
            domain=[('domain', '=', 'pis')]),
        'pis_st_type': fields.selection(
            [('percent', 'Percentual'), ('quantity', 'Em Valor')],
            'Tipo do PIS ST', required=True),
        'pis_st_base': fields.float('Base PIS ST', required=True,
            digits_compute=dp.get_precision('Account')),
        'pis_st_percent': fields.float('Perc PIS ST', required=True,
            digits_compute=dp.get_precision('Account')),
        'pis_st_value': fields.float('Valor PIS ST', required=True,
            digits_compute=dp.get_precision('Account')),
        'cofins_manual': fields.boolean('COFINS Manual?'),
        'cofins_type': fields.selection(
            [('percent', 'Percentual'), ('quantity', 'Em Valor')],
            'Tipo do COFINS', required=True),
        'cofins_base': fields.float('Base COFINS', required=True,
            digits_compute=dp.get_precision('Account')),
        'cofins_base_other': fields.float('Base COFINS Outras', required=True,
            digits_compute=dp.get_precision('Account')),
        'cofins_value': fields.float('Valor COFINS', required=True,
            digits_compute=dp.get_precision('Account')),
        'cofins_percent': fields.float('Perc COFINS', required=True,
            digits_compute=dp.get_precision('Discount')),
        'cofins_cst_id': fields.many2one('account.tax.code', 'CST PIS',
            domain=[('domain', '=', 'cofins')]),
        'cofins_st_type': fields.selection(
            [('percent', 'Percentual'), ('quantity', 'Em Valor')],
            'Tipo do COFINS ST', required=True),
        'cofins_st_base': fields.float('Base COFINS ST', required=True,
            digits_compute=dp.get_precision('Account')),
        'cofins_st_percent': fields.float('Perc COFINS ST', required=True,
            digits_compute=dp.get_precision('Discount')),
        'cofins_st_value': fields.float('Valor COFINS ST', required=True,
            digits_compute=dp.get_precision('Account')),
        'ii_base': fields.float('Base II', required=True,
            digits_compute=dp.get_precision('Account')),
        'ii_value': fields.float('Valor II', required=True,
            digits_compute=dp.get_precision('Account')),
        'ii_iof': fields.float('Valor IOF', required=True,
            digits_compute=dp.get_precision('Account')),
        'ii_customhouse_charges': fields.float('Depesas Atuaneiras',
            required=True, digits_compute=dp.get_precision('Account')),
        'insurance_value': fields.float('Valor do Seguro',
            digits_compute=dp.get_precision('Account')),
        'other_costs_value': fields.float('Outros Custos',
            digits_compute=dp.get_precision('Account')),
        'freight_value': fields.float('Frete',
            digits_compute=dp.get_precision('Account'))
    }
    _defaults = {
        'product_type': 'product',
        'icms_manual': False,
        'icms_origin': '0',
        'icms_base_type': '0',
        'icms_base': 0.0,
        'icms_base_other': 0.0,
        'icms_value': 0.0,
        'icms_percent': 0.0,
        'icms_percent_reduction': 0.0,
        'icms_st_base_type': 'percent',
        'icms_st_value': 0.0,
        'icms_st_base': 0.0,
        'icms_st_percent': 0.0,
        'icms_st_percent_reduction': 0.0,
        'icms_st_mva': 0.0,
        'icms_st_base_other': 0.0,
        'icms_st_base_type': '4',
        'issqn_manual': False,
        'issqn_type': 'N',
        'issqn_base': 0.0,
        'issqn_percent': 0.0,
        'issqn_value': 0.0,
        'ipi_manual': False,
        'ipi_type': 'percent',
        'ipi_base': 0.0,
        'ipi_base_other': 0.0,
        'ipi_value': 0.0,
        'ipi_percent': 0.0,
        'pis_manual': False,
        'pis_type': 'percent',
        'pis_base': 0.0,
        'pis_base_other': 0.0,
        'pis_value': 0.0,
        'pis_percent': 0.0,
        'pis_st_type': 'percent',
        'pis_st_base': 0.0,
        'pis_st_percent': 0.0,
        'pis_st_value': 0.0,
        'cofins_manual': False,
        'cofins_type': 'percent',
        'cofins_base': 0.0,
        'cofins_base_other': 0.0,
        'cofins_value': 0.0,
        'cofins_percent': 0.0,
        'cofins_st_type': 'percent',
        'cofins_st_base': 0.0,
        'cofins_st_percent': 0.0,
        'cofins_st_value': 0.0,
        'ii_base': 0.0,
        'ii_value': 0.0,
        'ii_iof': 0.0,
        'ii_customhouse_charges': 0.0,
        'insurance_value': 0.0,
        'other_costs_value': 0.0,
        'freight_value': 0.0,
    }

    def _amount_tax_icms(self, cr, uid, tax=None):
        result = {
            'icms_base_type': '0',
            'icms_base': tax.get('total_base', 0.0),
            'icms_base_other': tax.get('total_base_other', 0.0),
            'icms_value': tax.get('amount', 0.0),
            'icms_percent': tax.get('percent', 0.0) * 100,
            'icms_percent_reduction': tax.get('base_reduction') * 100,
        }
        return result

    def _amount_tax_icmsst(self, cr, uid, tax=None):
        result = {
            'icms_st_value': tax.get('amount', 0.0),
            'icms_st_base': tax.get('total_base', 0.0),
            'icms_st_percent': tax.get('icms_st_percent', 0.0) * 100,
            'icms_st_percent_reduction': tax.get('icms_st_percent_reduction', 0.0) * 100,
            'icms_st_mva': tax.get('amount_mva', 0.0) * 100,
            'icms_st_base_other': tax.get('icms_st_base_other', 0.0),
        }
        return result

    def _amount_tax_ipi(self, cr, uid, tax=None):
        result = {
            'ipi_type': tax.get('type'),
            'ipi_base': tax.get('total_base', 0.0),
            'ipi_value': tax.get('amount', 0.0),
            'ipi_percent': tax.get('percent', 0.0) * 100,
        }
        return result

    def _amount_tax_cofins(self, cr, uid, tax=None):
        result = {
            'cofins_base': tax.get('total_base', 0.0),
            'cofins_base_other': tax.get('total_base_other', 0.0),
            'cofins_value': tax.get('amount', 0.0),
            'cofins_percent': tax.get('percent', 0.0) * 100,
        }
        return result

    def _amount_tax_cofinsst(self, cr, uid, tax=None):
        result = {
            'cofins_st_type': 'percent',
            'cofins_st_base': 0.0,
            'cofins_st_percent': 0.0,
            'cofins_st_value': 0.0,
        }
        return result

    def _amount_tax_pis(self, cr, uid, tax=False):
        result = {
            'pis_base': tax.get('total_base', 0.0),
            'pis_base_other': tax.get('total_base_other', 0.0),
            'pis_value': tax.get('amount', 0.0),
            'pis_percent': tax.get('percent', 0.0) * 100,
        }
        return result

    def _amount_tax_pisst(self, cr, uid, tax=False):
        result = {
            'pis_st_type': 'percent',
            'pis_st_base': 0.0,
            'pis_st_percent': 0.0,
            'pis_st_value': 0.0,
        }
        return result

    def _amount_tax_ii(self, cr, uid, tax=False):
        result = {
            'ii_base': 0.0,
            'ii_value': 0.0,
        }
        return result

    def _amount_tax_issqn(self, cr, uid, tax=False):

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

    def _get_tax_codes(self, cr, uid, product_id, fiscal_position,
                        taxes, company_id, context=None):

        if not context:
            context = {}

        result = {}

        if fiscal_position.fiscal_category_id.journal_type in ('sale', 'sale_refund'):
            context['type_tax_use'] = 'sale'
        else:
            context['type_tax_use'] = 'purchase'

        context['fiscal_type'] = fiscal_position.fiscal_category_fiscal_type

        tax_codes = self.pool.get('account.fiscal.position').map_tax_code(
            cr, uid, product_id, fiscal_position, company_id,
            taxes, context=context)

        result['icms_cst_id'] = tax_codes.get('icms', False)
        result['ipi_cst_id'] = tax_codes.get('ipi', False)
        result['pis_cst_id'] = tax_codes.get('pis', False)
        result['cofins_cst_id'] = tax_codes.get('cofins', False)
        return result

    def _validate_taxes(self, cr, uid, values, context=None):
        """Verifica se o valor dos campos dos impostos estão sincronizados
        com os impostos do OpenERP"""
        if not context:
            context = {}

        tax_obj = self.pool.get('account.tax')

        if not values.get('product_id') or not values.get('quantity') \
        or not values.get('fiscal_position'):
            return {}

        result = {
            'product_type': 'product',
            'service_type_id': False,
            'fiscal_classification_id': False
        }

        if values.get('partner_id') and values.get('company_id'):
            partner_id = values.get('partner_id')
            company_id = values.get('company_id')
        else:
            if values.get('invoice_id'):
                inv = self.pool.get('account.invoice').read(
                    cr, uid, values.get('invoice_id'),
                    ['partner_id', 'company_id'])

                partner_id = inv.get('partner_id', [False])[0]
                company_id = inv.get('company_id', [False])[0]

        taxes = tax_obj.browse(
            cr, uid, values.get('invoice_line_tax_id')[0][2])
        fiscal_position = self.pool.get('account.fiscal.position').browse(
            cr, uid, values.get('fiscal_position'))

        price_unit = values.get('price_unit', 0.0)
        price = price_unit * (1 - values.get('discount', 0.0) / 100.0)

        taxes_calculed = tax_obj.compute_all(
            cr, uid, taxes, price, values.get('quantity', 0.0),
            values.get('product_id'), partner_id,
            fiscal_position=fiscal_position,
            insurance_value=values.get('insurance_value', 0.0),
            freight_value=values.get('freight_value', 0.0),
            other_costs_value=values.get('other_costs_value', 0.0))

        if values.get('product_id'):
            obj_product = self.pool.get('product.product').browse(
                cr, uid, values.get('product_id'), context=context)
            if obj_product.type == 'service':
                result['product_type'] = 'service'
                result['service_type_id'] = obj_product.service_type_id.id
            else:
                result['product_type'] = 'product'
            if obj_product.ncm_id:
                result['fiscal_classification_id'] = obj_product.ncm_id.id

            result['icms_origin'] = obj_product.origin

        for tax in taxes_calculed['taxes']:
            try:
                amount_tax = getattr(
                    self, '_amount_tax_%s' % tax.get('domain', ''))
                result.update(amount_tax(cr, uid, tax))
            except AttributeError:
                # Caso não exista campos especificos dos impostos
                # no documento fiscal, os mesmos são calculados.
                continue

        result.update(self._get_tax_codes(
            cr, uid, values.get('product_id'), fiscal_position,
            values.get('invoice_line_tax_id')[0][2],
            company_id, context=context))
        return result

    def create(self, cr, uid, vals, context=None):
        if not context:
            context = {}
        vals.update(self._validate_taxes(cr, uid, vals, context))
        return super(AccountInvoiceLine, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if not context:
            context = {}
        vals.update(self._validate_taxes(cr, uid, vals, context))
        return super(AccountInvoiceLine, self).write(
            cr, uid, ids, vals, context=context)


class AccountInvoiceTax(orm.Model):
    _inherit = "account.invoice.tax"

    def compute(self, cr, uid, invoice_id, context=None):
        tax_grouped = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('account.invoice').browse(
            cr, uid, invoice_id, context=context)
        cur = inv.currency_id
        currenty_date = time.strftime('%Y-%m-%d')
        company_currency = inv.company_id.currency_id.id

        for line in inv.invoice_line:
            for tax in tax_obj.compute_all(
                cr, uid, line.invoice_line_tax_id,
                (line.price_unit * (1 - (line.discount or 0.0) / 100.0)),
                line.quantity, line.product_id, inv.partner_id,
                fiscal_position=line.fiscal_position,
               insurance_value=line.insurance_value,
                freight_value=line.freight_value,
                other_costs_value=line.other_costs_value)['taxes']:
                val = {}
                val['invoice_id'] = inv.id
                val['name'] = tax['name']
                val['amount'] = tax['amount']
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = tax.get('total_base', 0.0)

                if inv.type in ('out_invoice', 'in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid,
                        inv.currency_id.id, company_currency,
                        val['base'] * tax['base_sign'],
                        context={'date': inv.date_invoice or currenty_date},
                        round=False)
                    val['tax_amount'] = cur_obj.compute(
                        cr, uid, inv.currency_id.id, company_currency,
                        val['amount'] * tax['tax_sign'],
                        context={'date': inv.date_invoice or currenty_date},
                        round=False)
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_collected_id']
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = cur_obj.compute(
                        cr, uid, inv.currency_id.id, company_currency,
                        val['base'] * tax['ref_base_sign'],
                        context={'date': inv.date_invoice or currenty_date},
                        round=False)
                    val['tax_amount'] = cur_obj.compute(
                        cr, uid, inv.currency_id.id,
                        company_currency, val['amount'] * tax['ref_tax_sign'],
                        context={'date': inv.date_invoice or currenty_date},
                        round=False)
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_paid_id']

                key = (val['tax_code_id'], val['base_code_id'], val['account_id'], val['account_analytic_id'])
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']

        for t in tax_grouped.values():
            t['base'] = cur_obj.round(cr, uid, cur, t['base'])
            t['amount'] = cur_obj.round(cr, uid, cur, t['amount'])
            t['base_amount'] = cur_obj.round(cr, uid, cur, t['base_amount'])
            t['tax_amount'] = cur_obj.round(cr, uid, cur, t['tax_amount'])
        return tax_grouped
