# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError
from odoo.tools import float_compare

from .product_template import PRODUCT_ORIGIN


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'freight_value',
                 'insurance_value', 'other_costs_value',
                 'invoice_id.currency_id', 'invoice_id.date_invoice')
    def _compute_price(self):
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = self.invoice_line_tax_ids.compute_all(
            price, self.invoice_id.currency_id, self.quantity,
            partner=self.invoice_id.partner_id,
            fiscal_position=self.fiscal_position_id,
            insurance_value=self.insurance_value,
            freight_value=self.freight_value,
            other_costs_value=self.other_costs_value)

        for tax in taxes['taxes']:
            try:
                amount_tax = getattr(
                    self, '_amount_tax_%s' % tax.get('domain', ''))
                amount_tax(tax)
            except AttributeError:
                # Caso não exista campos especificos dos impostos
                # no documento fiscal, os mesmos são calculados.
                continue

        self.price_tax_discount = 0.0
        self.price_subtotal = 0.0
        self.price_gross = 0.0
        self.discount_value = 0.0

        # sign = self.invoice_id.type in ['in_refund', 'out_refund']
        #        and -1 or 1
        sign = 1
        if self.invoice_id:
            self.price_tax_discount = self.invoice_id.currency_id.round(
                taxes['total_excluded'] - taxes['total_tax_discount'] * sign)
            self.price_subtotal = self.invoice_id.currency_id.round(
                taxes['base'] * sign)
            self.price_gross = self.invoice_id.currency_id.round(
                self.price_unit * self.quantity * sign)
            self.discount_value = self.invoice_id.currency_id.round(
                self.price_gross - taxes['total_excluded'] * sign)

    code = fields.Char(
        string=u'Código do Produto',
        size=60)

    date_invoice = fields.Datetime(
        string=u'Invoice Date',
        readonly=True,
        states={'draft': [('readonly', False)]},
        index=True,
        help="Keep empty to use the current date")

    fiscal_category_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string=u'Categoria Fiscal')

    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string=u'Posição Fiscal')

    cfop_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cfop',
        domain="[('internal_type', '=', 'normal')]",
        string=u'CFOP')

    fiscal_classification_id = fields.Many2one(
        comodel_name='account.product.fiscal.classification',
        string=u'Classificação Fiscal')

    cest_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cest',
        string=u'CEST')

    fci = fields.Char(
        string=u'FCI do Produto',
        size=36)

    import_declaration_ids = fields.One2many(
        comodel_name='l10n_br_account_product.import.declaration',
        inverse_name='invoice_line_id',
        string=u'Declaração de Importação')

    product_type = fields.Selection(
        selection=[('product', 'Produto'),
                   ('service', u'Serviço')],
        string=u'Tipo do Produto',
        required=True,
        default='product')

    discount_value = fields.Float(
        string=u'Vlr. desconto',
        store=True,
        compute='_compute_price',
        digits=dp.get_precision('Account'))

    price_gross = fields.Float(
        string=u'Vlr. Bruto',
        store=True,
        compute='_compute_price',
        digits=dp.get_precision('Account'))

    price_tax_discount = fields.Float(
        string=u'Vlr. s/ Impostos',
        store=True,
        compute='_compute_price',
        digits=dp.get_precision('Account'))

    total_taxes = fields.Float(
        string=u'Total de Tributos',
        requeried=True,
        default=0.00,
        digits=dp.get_precision('Account'))

    icms_manual = fields.Boolean(
        string=u'ICMS Manual?',
        default=False)

    icms_origin = fields.Selection(
        selection=PRODUCT_ORIGIN,
        string=u'Origem',
        default='0')

    icms_base_type = fields.Selection(
        selection=[('0', 'Margem Valor Agregado (%)'),
                   ('1', 'Pauta (valor)'),
                   ('2', u'Preço Tabelado Máximo (valor)'),
                   ('3', u'Valor da Operação')],
        string=u'Tipo Base ICMS',
        required=True,
        default='0')

    icms_base = fields.Float(
        string=u'Base ICMS',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    icms_base_other = fields.Float(
        string=u'Base ICMS Outras',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    icms_value = fields.Float(
        string=u'Valor ICMS',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    icms_percent = fields.Float(
        string=u'Perc ICMS',
        digits=dp.get_precision('Discount'),
        default=0.00)

    icms_percent_reduction = fields.Float(
        string=u'Perc Redução de Base ICMS',
        digits=dp.get_precision('Discount'),
        default=0.00)

    icms_st_base_type = fields.Selection(
        selection=[('0', u'Preço tabelado ou máximo  sugerido'),
                   ('1', 'Lista Negativa (valor)'),
                   ('2', 'Lista Positiva (valor)'),
                   ('3', 'Lista Neutra (valor)'),
                   ('4', 'Margem Valor Agregado (%)'),
                   ('5', 'Pauta (valor)')],
        string=u'Tipo Base ICMS ST',
        required=True,
        default='4')

    icms_st_value = fields.Float(
        string=u'Valor ICMS ST',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    icms_st_base = fields.Float(
        string=u'Base ICMS ST',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    icms_st_percent = fields.Float(
        string=u'Percentual ICMS ST',
        digits=dp.get_precision('Discount'),
        default=0.00)

    icms_st_percent_reduction = fields.Float(
        string=u'Perc Redução de Base ICMS ST',
        digits=dp.get_precision('Discount'),
        default=0.00)

    icms_st_mva = fields.Float(
        string=u'MVA Ajustado ICMS ST',
        digits=dp.get_precision('Discount'), default=0.00)

    icms_st_base_other = fields.Float(
        string=u'Base ICMS ST Outras',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    icms_cst_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cst',
        string=u'CST ICMS',
        domain=[('tax_group_id.domain', '=', 'icms')])

    icms_relief_id = fields.Many2one(
        comodel_name='l10n_br_account_product.icms_relief',
        string=u'Desoneração ICMS')

    issqn_manual = fields.Boolean(
        string=u'ISSQN Manual?',
        default=False)

    issqn_type = fields.Selection(
        selection=[('N', 'Normal'),
                   ('R', 'Retida'),
                   ('S', 'Substituta'),
                   ('I', 'Isenta')],
        string=u'Tipo do ISSQN',
        required=True,
        default='N')

    service_type_id = fields.Many2one(
        comodel_name='l10n_br_account.service.type',
        string=u'Tipo de Serviço')

    issqn_base = fields.Float(
        string=u'Base ISSQN',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    issqn_percent = fields.Float(
        string=u'Perc ISSQN',
        required=True,
        digits=dp.get_precision('Discount'),
        default=0.00)

    issqn_value = fields.Float(
        string=u'Valor ISSQN',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    ipi_manual = fields.Boolean(
        string=u'IPI Manual?',
        default=False)

    ipi_type = fields.Selection(
        selection=[('percent', 'Percentual'),
                   ('quantity', 'Em Valor')],
        string=u'Tipo do IPI',
        required=True,
        default='percent')

    ipi_base = fields.Float(
        string=u'Base IPI',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    ipi_base_other = fields.Float(
        string=u'Base IPI Outras',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    ipi_value = fields.Float(
        string=u'Valor IPI',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    ipi_percent = fields.Float(
        string=u'Perc IPI',
        required=True,
        digits=dp.get_precision('Discount'),
        default=0.00)

    ipi_cst_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cst',
        string=u'CST IPI',
        domain=[('tax_group_id.domain', '=', 'ipi')])

    ipi_guideline_id = fields.Many2one(
        comodel_name='l10n_br_account_product.ipi_guideline',
        string=u'Enquadramento Legal IPI')

    pis_manual = fields.Boolean(
        string=u'PIS Manual?',
        default=False)

    pis_type = fields.Selection(
        selection=[('percent', 'Percentual'),
                   ('quantity', 'Em Valor')],
        string=u'Tipo do PIS',
        required=True,
        default='percent')

    pis_base = fields.Float(
        string=u'Base PIS',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    pis_base_other = fields.Float(
        string=u'Base PIS Outras',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    pis_value = fields.Float(
        string=u'Valor PIS',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    pis_percent = fields.Float(
        string=u'Perc PIS',
        required=True,
        digits=dp.get_precision('Discount'),
        default=0.00)

    pis_cst_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cst',
        string=u'CST PIS',
        domain=[('tax_group_id.domain', '=', 'pis')])

    pis_st_type = fields.Selection(
        selection=[('percent', 'Percentual'),
                   ('quantity', 'Em Valor')],
        string=u'Tipo do PIS ST',
        required=True,
        default='percent')

    pis_st_base = fields.Float(
        string=u'Base PIS ST',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    pis_st_percent = fields.Float(
        string=u'Perc PIS ST',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    pis_st_value = fields.Float(
        string=u'Valor PIS ST',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    cofins_manual = fields.Boolean(
        string=u'COFINS Manual?',
        default=False)

    cofins_type = fields.Selection(
        selection=[('percent', 'Percentual'),
                   ('quantity', 'Em Valor')],
        string=u'Tipo do COFINS',
        required=True,
        default='percent')

    cofins_base = fields.Float(
        string=u'Base COFINS',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    cofins_base_other = fields.Float(
        string=u'Base COFINS Outras',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    cofins_value = fields.Float(
        string=u'Valor COFINS',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    cofins_percent = fields.Float(
        string=u'Perc COFINS',
        required=True,
        digits=dp.get_precision('Discount'),
        default=0.00)

    cofins_cst_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cst',
        string=u'CST PIS',
        domain=[('tax_group_id.domain', '=', 'cofins')])

    cofins_st_type = fields.Selection(
        selection=[('percent', 'Percentual'),
                   ('quantity', 'Em Valor')],
        string=u'Tipo do COFINS ST',
        required=True,
        default='percent')

    cofins_st_base = fields.Float(
        string=u'Base COFINS ST',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    cofins_st_percent = fields.Float(
        string=u'Perc COFINS ST',
        required=True,
        digits=dp.get_precision('Discount'),
        default=0.00)

    cofins_st_value = fields.Float(
        string=u'Valor COFINS ST',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    ii_base = fields.Float(
        string=u'Base II',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    ii_value = fields.Float(
        string=u'Valor II',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    ii_iof = fields.Float(
        string=u'Valor IOF',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    ii_customhouse_charges = fields.Float(
        string=u'Despesas Aduaneiras',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)

    insurance_value = fields.Float(
        string=u'Valor do Seguro',
        digits=dp.get_precision('Account'),
        default=0.00)

    other_costs_value = fields.Float(
        string=u'Outros Custos',
        digits=dp.get_precision('Account'),
        default=0.00)

    freight_value = fields.Float(
        string=u'Frete',
        digits=dp.get_precision('Account'),
        default=0.00)

    fiscal_comment = fields.Text(
        string=u'Observação Fiscal')

    icms_dest_base = fields.Float(
        string=u'Valor da BC do ICMS na UF de destino',
        digits=dp.get_precision('Account'),
        default=0.00)

    icms_fcp_percent = fields.Float(
        string=u'% Fundo de Combate à Pobreza (FCP)',
        digits=dp.get_precision('Account'),
        default=0.00)

    icms_origin_percent = fields.Float(
        string=u'Alíquota interna da UF de destino',
        digits=dp.get_precision('Account'),
        default=0.00)

    icms_dest_percent = fields.Float(
        string=u'Alíquota interestadual das UF envolvidas',
        digits=dp.get_precision('Account'),
        default=0.00)

    icms_part_percent = fields.Float(
        string=u'Percentual provisório de partilha do ICMS Interestadual',
        digits=dp.get_precision('Account'),
        default=0.00)

    icms_fcp_value = fields.Float(
        string=(u'Valor do ICMS relativo ao Fundo de Combate à Pobreza (FCP)'
                u' da UF de destino'),
        digits=dp.get_precision('Account'),
        default=0.00)

    icms_dest_value = fields.Float(
        string=u'Valor do ICMS Interestadual para a UF de destino',
        digits=dp.get_precision('Account'),
        default=0.00)

    icms_origin_value = fields.Float(
        string=u'Valor do ICMS Interno para a UF do remetente',
        digits=dp.get_precision('Account'),
        default=0.00)

    partner_order = fields.Char(
        string=u'Código do Pedido (xPed)',
        size=15)

    partner_order_line = fields.Char(
        string=u'Item do Pedido (nItemPed)',
        size=6)

    @api.onchange('partner_order_line')
    def _check_partner_order_line(self):
        if (self.partner_order_line and
                not self.partner_order_line.isdigit()):
            raise ValidationError(
                _(u"Customer Order Line must "
                  "be a number with up to six digits"))

    def _amount_tax_icms(self, tax=None):
        self.icms_base = tax.get('total_base', 0.0)
        self.icms_base_other = tax.get('total_base_other', 0.0)
        self.icms_value = tax.get('amount', 0.0)
        self.icms_percent = tax.get('percent', 0.0)
        self.icms_percent_reduction = tax.get('base_reduction')
        self.icms_base_type = tax.get('icms_base_type', '0')

    def _amount_tax_icmsinter(self, tax=None):
        self.icms_dest_base = tax.get('total_base', 0.0)
        self.icms_dest_percent = tax.get('percent', 0.0)
        self.icms_origin_percent = tax.get('icms_origin_percent', 0.0)
        self.icms_part_percent = tax.get('icms_part_percent', 0.0)
        self.icms_dest_value = tax.get('icms_dest_value', 0.0)
        self.icms_origin_value = tax.get('icms_origin_value', 0.0)

    def _amount_tax_icmsfcp(self, tax=None):
        self.icms_fcp_percent = tax.get('percent', 0.0)
        self.icms_fcp_value = tax.get('amount', 0.0)

    def _amount_tax_icmsst(self, tax=None):
        self.icms_st_value = tax.get('amount', 0.0)
        self.icms_st_base = tax.get('total_base', 0.0)
        self.icms_st_percent = tax.get('icms_st_percent', 0.0)
        self.icms_st_percent_reduction = tax.get(
            'icms_st_percent_reduction',
            0.0)
        self.icms_st_mva = tax.get('amount_mva', 0.0) * 100
        self.icms_st_base_other = tax.get('icms_st_base_other', 0.0)
        self.icms_st_base_type = tax.get('icms_st_base_type', '4')

    def _amount_tax_ipi(self, tax=None):
        self.ipi_type = tax.get('amount_type')
        self.ipi_base = tax.get('total_base', 0.0)
        self.ipi_value = tax.get('amount', 0.0)
        self.ipi_percent = tax.get('percent', 0.0)

    def _amount_tax_cofins(self, tax=None):
        self.cofins_base = tax.get('total_base', 0.0)
        self.cofins_base_other = tax.get('total_base_other', 0.0)
        self.cofins_value = tax.get('amount', 0.0)
        self.cofins_percent = tax.get('percent', 0.0)

    def _amount_tax_cofinsst(self, tax=None):
        self.cofins_st_type = 'percent'
        self.cofins_st_base = 0.0
        self.cofins_st_percent = 0.0
        self.cofins_st_value = 0.0

    def _amount_tax_pis(self, tax=None):
        self.pis_base = tax.get('total_base', 0.0)
        self.pis_base_other = tax.get('total_base_other', 0.0)
        self.pis_value = tax.get('amount', 0.0)
        self.pis_percent = tax.get('percent', 0.0)

    def _amount_tax_pisst(self, tax=None):
        self.pis_st_type = 'percent'
        self.pis_st_base = 0.0
        self.pis_st_percent = 0.0
        self.pis_st_value = 0.0

    def _amount_tax_ii(self, tax=None):
        self.ii_base = 0.0
        self.ii_value = 0.0

    def _amount_tax_issqn(self, tax=None):
        # TODO deixar dinamico a definição do tipo do ISSQN
        # assim como todos os impostos
        issqn_type = 'N'
        if not tax.get('amount'):
            issqn_type = 'I'

        self.issqn_type = issqn_type
        self.issqn_base = tax.get('total_base', 0.0)
        self.issqn_percent = tax.get('percent', 0.0)
        self.issqn_value = tax.get('amount', 0.0)

    def _set_taxes_codes(self):
        product = self.product_id
        self.product_type = product.fiscal_type
        self.code = product.default_code
        if self.product_type == 'product':
            self.fiscal_classification_id = product.fiscal_classification_id
            self.cest_id = product.cest_id
            self.fci = product.fci
            self.cest_id = product.cest_id.id
            self.icms_origin = product.origin
            self.cfop_id = self.fiscal_position_id.cfop_id.id

        if product.type == 'service':
            self.product_type = 'service'
            self.service_type_id = product.service_type_id.id

    def _set_taxes(self):
        """ Used in on_change to set taxes and price."""
        ctx = dict(self.env.context)
        if self.invoice_id.type in ('out_invoice', 'out_refund'):
            taxes = self.product_id.taxes_id or self.account_id.tax_ids
            ctx.update({'type_tax_use': 'sale'})
        else:
            taxes = (self.product_id.supplier_taxes_id or
                     self.account_id.tax_ids)
            ctx.update({'type_tax_use': 'purchase'})

        # Keep only taxes of the company
        company_id = self.company_id or self.env.user.company_id
        taxes = taxes.filtered(lambda r: r.company_id == company_id)

        map_tax = self.fiscal_position_id.with_context(ctx).map_tax_code(
            taxes, self.product_id, self.invoice_id.partner_id)

        fp_taxes = self.env['account.tax'].browse()
        tax_codes = {}
        for tax in map_tax:
            if map_tax[tax].get('tax'):
                fp_taxes |= map_tax[tax].get('tax')
                tax_codes.update({
                    map_tax[tax].get('tax').domain: map_tax[tax].get('cst')})

        self.invoice_line_tax_ids = fp_taxes

        fix_price = self.env['account.tax']._fix_tax_included_price
        if self.invoice_id.type in ('in_invoice', 'in_refund'):
            prec = self.env['decimal.precision'].precision_get('Product Price')
            if not self.price_unit or float_compare(
                    self.price_unit, self.product_id.standard_price,
                    precision_digits=prec) == 0:
                self.price_unit = fix_price(
                    self.product_id.standard_price, taxes, fp_taxes)
                self._set_currency()
        else:
            if not self.price_unit or self.price_unit == 0.0:
                self.price_unit = self.product_id.lst_price
            self.price_unit = fix_price(
                self.price_unit, taxes, fp_taxes)
            self._set_currency()

        self.icms_cst_id = tax_codes.get('icms')
        self.ipi_cst_id = tax_codes.get('ipi')
        self.pis_cst_id = tax_codes.get('pis')
        self.cofins_cst_id = tax_codes.get('cofins')
        self.icms_relief_id = tax_codes.get('icms_relief')
        self.ipi_guideline_id = tax_codes.get('ipi_guideline')

        self._compute_price()
        self._set_taxes_codes()

    @api.onchange('product_id',
                  'fiscal_category_id',
                  'fiscal_position_id',
                  'invoice_line_tax_ids',
                  'quantity',
                  'price_unit',
                  'discount',
                  'insurance_value',
                  'freight_value',
                  'other_costs_value')
    def _onchange_fiscal(self):
        partner = self.invoice_id.partner_id
        company = self.invoice_id.company_id
        fiscal_rule = self.env['account.fiscal.position.rule']

        if company and partner and self.fiscal_category_id:
            product_fc = fiscal_rule.product_fiscal_category_map(
                self.product_id, self.fiscal_category_id,
                partner.state_id.id)

            if product_fc:
                self.fiscal_category_id = product_fc

            kwargs = {
                'company_id': company,
                'partner_id': partner,
                'partner_invoice_id': partner,
                'product_id': self.product_id,
                'fiscal_category_id': self.fiscal_category_id,
            }

            context = dict(self.env.context)
            context.update(
                {'use_domain': ('use_invoice', '=', True)})

            fp = fiscal_rule.with_context(
                context).apply_fiscal_mapping(**kwargs)
            if fp:
                self.fiscal_position_id = fp.id
            self._set_taxes()

    @api.model
    def tax_exists(self, domain=None):
        result = False
        tax = self.env['account.tax'].search(domain, limit=1)
        if tax:
            result = tax
        return result

    # TODO if ICMS percent is not in account.tax,
    # create a new account.tax
    @api.onchange('icms_base_type',
                  'icms_base',
                  'icms_base_other',
                  'icms_value',
                  'icms_percent',
                  'icms_percent_reduction')
    def _onchange_tax_icms(self):
        pass

    # TODO if ICMS ST percent is not in account.tax,
    # create a new account.tax
    @api.onchange('icms_st_base_type',
                  'icms_st_base',
                  'icms_st_percent',
                  'icms_st_percent_reduction',
                  'icms_st_mva',
                  'icms_st_base_other')
    def _onchange_tax_icms_st(self):
        pass

    # TODO if IPI percent is not in account.tax,
    # create a new account.tax
    @api.onchange(
        'ipi_type',
        'ipi_base',
        'ipi_base_other',
        'ipi_value',
        'ipi_percent',
    )
    def _onchange_tax_ipi(self):
        pass

    # TODO if PIS percent is not in account.tax,
    # create a new account.tax
    @api.onchange('pis_type',
                  'pis_base',
                  'pis_base_other',
                  'pis_value',
                  'pis_percent',
                  'pis_st_type',
                  'pis_st_base',
                  'pis_st_percent',
                  'pis_st_value')
    def _onchange_tax_pis(self):
        pass

    # TODO if COFINS percent is not in account.tax,
    # create a new account.tax
    @api.onchange('cofins_type',
                  'cofins_base',
                  'cofins_base_other',
                  'cofins_percent',
                  'cofins_value',
                  'cofins_st_type',
                  'cofins_st_base',
                  'cofins_st_percent',
                  'cofins_st_value')
    def _onchange_tax_cofins(self):
        pass
