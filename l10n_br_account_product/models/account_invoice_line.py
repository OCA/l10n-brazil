# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _, tools
from odoo.addons import decimal_precision as dp

from .l10n_br_account_product import (PRODUCT_FISCAL_TYPE,
                                      PRODUCT_FISCAL_TYPE_DEFAULT)

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
        self.price_tax_discount = 0.0
        self.price_subtotal = 0.0
        self.price_gross = 0.0
        self.discount_value = 0.0
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        if self.invoice_id:
            self.price_tax_discount = self.invoice_id.currency_id.round(
                taxes['total_excluded'] - taxes['total_tax_discount'] * sign)
            self.price_subtotal = self.invoice_id.currency_id.round(
                taxes['total_excluded'] * sign)
            self.price_gross = self.invoice_id.currency_id.round(
                self.price_unit * self.quantity * sign)
            self.discount_value = self.invoice_id.currency_id.round(
                self.price_gross - taxes['total_excluded'] * sign)

    code = fields.Char(
        string=u'Código do Produto',
        size=60
    )
    date_invoice = fields.Datetime(
        string=u'Invoice Date',
        readonly=True,
        states={'draft': [('readonly', False)]},
        index=True,
        help="Keep empty to use the current date"
    )
    fiscal_category_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string=u'Categoria Fiscal'
    )
    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string=u'Posição Fiscal',
    )
    cfop_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cfop',
        domain="[('internal_type', '=', 'normal')]",
        string=u'CFOP'
    )
    fiscal_classification_id = fields.Many2one(
        comodel_name='account.product.fiscal.classification',
        string=u'Classificação Fiscal'
    )
    cest_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cest',
        string=u'CEST'
    )
    fci = fields.Char(
        string=u'FCI do Produto',
        size=36
    )
    import_declaration_ids = fields.One2many(
        comodel_name='l10n_br_account_product.import.declaration',
        inverse_name='invoice_line_id',
        string=u'Declaração de Importação'
    )
    product_type = fields.Selection(
        selection=[('product', 'Produto'),
                   ('service', u'Serviço')],
        string=u'Tipo do Produto',
        required=True,
        default='product'
    )
    discount_value = fields.Float(
        string=u'Vlr. desconto',
        store=True,
        compute='_compute_price',
        digits=dp.get_precision('Account')
    )
    price_gross = fields.Float(
        string=u'Vlr. Bruto',
        store=True,
        compute='_compute_price',
        digits=dp.get_precision('Account')
    )
    price_tax_discount = fields.Float(
        string=u'Vlr. s/ Impostos',
        store=True,
        compute='_compute_price',
        digits=dp.get_precision('Account')
    )
    total_taxes = fields.Float(
        string=u'Total de Tributos',
        requeried=True,
        default=0.00,
        digits=dp.get_precision('Account')
    )
    icms_manual = fields.Boolean(
        string=u'ICMS Manual?',
        default=False
    )
    icms_origin = fields.Selection(
        selection=PRODUCT_ORIGIN,
        string=u'Origem',
        default='0'
    )
    icms_base_type = fields.Selection(
        selection=[('0', 'Margem Valor Agregado (%)'),
                   ('1', 'Pauta (valor)'),
                   ('2', u'Preço Tabelado Máximo (valor)'),
                   ('3', u'Valor da Operação')],
        string=u'Tipo Base ICMS',
        required=True,
        default='0'
    )
    icms_base = fields.Float(
        string=u'Base ICMS',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    icms_base_other = fields.Float(
        string=u'Base ICMS Outras',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    icms_value = fields.Float(
        string=u'Valor ICMS',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    icms_percent = fields.Float(
        string=u'Perc ICMS',
        digits=dp.get_precision('Discount'),
        default=0.00
    )
    icms_percent_reduction = fields.Float(
        string=u'Perc Redução de Base ICMS',
        digits=dp.get_precision('Discount'),
        default=0.00
    )
    icms_st_base_type = fields.Selection(
        selection=[('0', u'Preço tabelado ou máximo  sugerido'),
                   ('1', 'Lista Negativa (valor)'),
                   ('2', 'Lista Positiva (valor)'),
                   ('3', 'Lista Neutra (valor)'),
                   ('4', 'Margem Valor Agregado (%)'),
                   ('5', 'Pauta (valor)')],
        string=u'Tipo Base ICMS ST',
        required=True,
        default='4'
    )
    icms_st_value = fields.Float(
        string=u'Valor ICMS ST',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    icms_st_base = fields.Float(
        string=u'Base ICMS ST',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    icms_st_percent = fields.Float(
        string=u'Percentual ICMS ST',
        digits=dp.get_precision('Discount'),
        default=0.00
    )
    icms_st_percent_reduction = fields.Float(
        string=u'Perc Redução de Base ICMS ST',
        digits=dp.get_precision('Discount'),
        default=0.00
    )
    icms_st_mva = fields.Float(
        string=u'MVA Ajustado ICMS ST',
        digits=dp.get_precision('Discount'), default=0.00)
    icms_st_base_other = fields.Float(
        string=u'Base ICMS ST Outras',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    icms_cst_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cst',
        string=u'CST ICMS',
        domain=[('domain', '=', 'icms')])
    icms_relief_id = fields.Many2one(
        comodel_name='l10n_br_account_product.icms_relief',
        string=u'Desoneração ICMS'
    )
    issqn_manual = fields.Boolean(
        string=u'ISSQN Manual?',
        default=False
    )
    issqn_type = fields.Selection(
        selection=[('N', 'Normal'),
                   ('R', 'Retida'),
                   ('S', 'Substituta'),
                   ('I', 'Isenta')],
        string=u'Tipo do ISSQN',
        required=True,
        default='N'
    )
    service_type_id = fields.Many2one(
        comodel_name='l10n_br_account.service.type',
        string=u'Tipo de Serviço'
    )
    issqn_base = fields.Float(
        string=u'Base ISSQN',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    issqn_percent = fields.Float(
        string=u'Perc ISSQN',
        required=True,
        digits=dp.get_precision('Discount'),
        default=0.00
    )
    issqn_value = fields.Float(
        string=u'Valor ISSQN',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    ipi_manual = fields.Boolean(
        string=u'IPI Manual?',
        default=False
    )
    ipi_type = fields.Selection(
        selection=[('percent', 'Percentual'),
                   ('quantity', 'Em Valor')],
        string=u'Tipo do IPI',
        required=True,
        default='percent'
    )
    ipi_base = fields.Float(
        string=u'Base IPI',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    ipi_base_other = fields.Float(
        string=u'Base IPI Outras',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    ipi_value = fields.Float(
        string=u'Valor IPI',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    ipi_percent = fields.Float(
        string=u'Perc IPI',
        required=True,
        digits=dp.get_precision('Discount'),
        default=0.00
    )
    ipi_cst_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cst',
        string=u'CST IPI',
        domain=[('domain', '=', 'ipi')]
    )
    ipi_guideline_id = fields.Many2one(
        comodel_name='l10n_br_account_product.ipi_guideline',
        string=u'Enquadramento Legal IPI'
    )
    pis_manual = fields.Boolean(
        string=u'PIS Manual?',
        default=False
    )
    pis_type = fields.Selection(
        selection=[('percent', 'Percentual'),
                   ('quantity', 'Em Valor')],
        string=u'Tipo do PIS',
        required=True,
        default='percent'
    )
    pis_base = fields.Float(
        string=u'Base PIS',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    pis_base_other = fields.Float(
        string=u'Base PIS Outras',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    pis_value = fields.Float(
        string=u'Valor PIS',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    pis_percent = fields.Float(
        string=u'Perc PIS',
        required=True,
        digits=dp.get_precision('Discount'),
        default=0.00
    )
    pis_cst_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cst',
        string=u'CST PIS',
        domain=[('domain', '=', 'pis')]
    )
    pis_st_type = fields.Selection(
        selection=[('percent', 'Percentual'),
                   ('quantity', 'Em Valor')],
        string=u'Tipo do PIS ST',
        required=True,
        default='percent'
    )
    pis_st_base = fields.Float(
        string=u'Base PIS ST',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    pis_st_percent = fields.Float(
        string=u'Perc PIS ST',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    pis_st_value = fields.Float(
        string=u'Valor PIS ST',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    cofins_manual = fields.Boolean(
        string=u'COFINS Manual?',
        default=False)
    cofins_type = fields.Selection(
        selection=[('percent', 'Percentual'),
                   ('quantity', 'Em Valor')],
        string=u'Tipo do COFINS',
        required=True,
        default='percent'
    )
    cofins_base = fields.Float(
        string=u'Base COFINS',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    cofins_base_other = fields.Float(
        string=u'Base COFINS Outras',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    cofins_value = fields.Float(
        string=u'Valor COFINS',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    cofins_percent = fields.Float(
        string=u'Perc COFINS',
        required=True,
        digits=dp.get_precision('Discount'),
        default=0.00
    )
    cofins_cst_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cst',
        string=u'CST PIS',
        domain=[('domain', '=', 'cofins')]
    )
    cofins_st_type = fields.Selection(
        selection=[('percent', 'Percentual'),
                   ('quantity', 'Em Valor')],
        string=u'Tipo do COFINS ST',
        required=True,
        default='percent'
    )
    cofins_st_base = fields.Float(
        string=u'Base COFINS ST',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    cofins_st_percent = fields.Float(
        string=u'Perc COFINS ST',
        required=True,
        digits=dp.get_precision('Discount'),
        default=0.00
    )
    cofins_st_value = fields.Float(
        string=u'Valor COFINS ST',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    ii_base = fields.Float(
        string=u'Base II',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    ii_value = fields.Float(
        string=u'Valor II',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    ii_iof = fields.Float(
        string=u'Valor IOF',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    ii_customhouse_charges = fields.Float(
        string=u'Despesas Aduaneiras',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00
    )
    insurance_value = fields.Float(
        string=u'Valor do Seguro',
        digits=dp.get_precision('Account'),
        default=0.00
    )
    other_costs_value = fields.Float(
        string=u'Outros Custos',
        digits=dp.get_precision('Account'),
        default=0.00
    )
    freight_value = fields.Float(
        string=u'Frete',
        digits=dp.get_precision('Account'),
        default=0.00
    )
    fiscal_comment = fields.Text(
        string=u'Observação Fiscal'
    )
    icms_dest_base = fields.Float(
        string=u'Valor da BC do ICMS na UF de destino',
        digits=dp.get_precision('Account'),
        default=0.00
    )
    icms_fcp_percent = fields.Float(
        string=u'% Fundo de Combate à Pobreza (FCP)',
        digits=dp.get_precision('Account'),
        default=0.00
    )
    icms_origin_percent = fields.Float(
        string=u'Alíquota interna da UF de destino',
        digits=dp.get_precision('Account'),
        default=0.00
    )
    icms_dest_percent = fields.Float(
        string=u'Alíquota interestadual das UF envolvidas',
        digits=dp.get_precision('Account'),
        default=0.00
    )
    icms_part_percent = fields.Float(
        string=u'Percentual provisório de partilha do ICMS Interestadual',
        digits=dp.get_precision('Account'),
        default=0.00
    )
    icms_fcp_value = fields.Float(
        string=(u'Valor do ICMS relativo ao Fundo de Combate à Pobreza (FCP)'
                u' da UF de destino'),
        digits=dp.get_precision('Account'),
        default=0.00
    )
    icms_dest_value = fields.Float(
        string=u'Valor do ICMS Interestadual para a UF de destino',
        digits=dp.get_precision('Account'),
        default=0.00
    )
    icms_origin_value = fields.Float(
        string=u'Valor do ICMS Interno para a UF do remetente',
        digits=dp.get_precision('Account'),
        default=0.00
    )
    partner_order = fields.Char(
        string=u'Código do Pedido (xPed)',
        size=15,
    )
    partner_order_line = fields.Char(
        string=u'Item do Pedido (nItemPed)',
        size=6,
    )

    @api.onchange("partner_order_line")
    def _check_partner_order_line(self):
        if (self.partner_order_line and
                not self.partner_order_line.isdigit()):
            raise ValidationError(
                _(u"Customer Order Line must "
                  "be a number with up to six digits")
            )

    def _amount_tax_icms(self, tax=None):
        result = {
            'icms_base': tax.get('total_base', 0.0),
            'icms_base_other': tax.get('total_base_other', 0.0),
            'icms_value': tax.get('amount', 0.0),
            'icms_percent': tax.get('percent', 0.0) * 100,
            'icms_percent_reduction': tax.get('base_reduction') * 100,
            'icms_base_type': tax.get('icms_base_type', '0'),
        }
        return result

    def _amount_tax_icmsinter(self, tax=None):
        result = {
            'icms_dest_base': tax.get('total_base', 0.0),
            'icms_dest_percent': tax.get('percent', 0.0) * 100,
            'icms_origin_percent': tax.get('icms_origin_percent', 0.0) * 100,
            'icms_part_percent': tax.get('icms_part_percent', 0.0) * 100,
            'icms_dest_value': tax.get('icms_dest_value', 0.0),
            'icms_origin_value': tax.get('icms_origin_value', 0.0),
        }
        return result

    def _amount_tax_icmsfcp(self, tax=None):
        result = {
            'icms_fcp_percent': tax.get('percent', 0.0) * 100,
            'icms_fcp_value': tax.get('amount', 0.0),
        }
        return result

    def _amount_tax_icmsst(self, tax=None):
        result = {
            'icms_st_value': tax.get('amount', 0.0),
            'icms_st_base': tax.get('total_base', 0.0),
            'icms_st_percent': tax.get('icms_st_percent', 0.0) * 100,
            'icms_st_percent_reduction': tax.get(
                'icms_st_percent_reduction',
                0.0) * 100,
            'icms_st_mva': tax.get('amount_mva', 0.0) * 100,
            'icms_st_base_other': tax.get('icms_st_base_other', 0.0),
            'icms_st_base_type': tax.get('icms_st_base_type', '4')
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
        ctx.update({'product_id': product_id})

        if fiscal_position.fiscal_category_id.journal_type in (
                'sale', 'sale_refund'):
            ctx.update({'type_tax_use': 'sale'})
        else:
            ctx.update({'type_tax_use': 'purchase'})

        ctx.update({'fiscal_type': product_id.fiscal_type})
        result['cfop_id'] = fiscal_position.cfop_id.id

        tax_codes = fiscal_position.with_context(
            ctx).map_tax_code(product_id, taxes)

        result['icms_cst_id'] = tax_codes.get('icms')
        result['ipi_cst_id'] = tax_codes.get('ipi')
        result['pis_cst_id'] = tax_codes.get('pis')
        result['cofins_cst_id'] = tax_codes.get('cofins')
        result['icms_relief_id'] = tax_codes.get('icms_relief')
        result['ipi_guideline_id'] = tax_codes.get('ipi_guideline')
        return result

    # TODO
    @api.multi
    def _validate_taxes(self, values):
        """Verifica se o valor dos campos dos impostos estão sincronizados
        com os impostos do Odoo"""
        context = self.env.context

        price_unit = values.get('price_unit', 0.0) or self.price_unit
        discount = values.get('discount', 0.0) or self.discount
        insurance_value = values.get(
            'insurance_value', 0.0) or self.insurance_value
        freight_value = values.get(
            'freight_value', 0.0) or self.freight_value
        other_costs_value = values.get(
            'other_costs_value', 0.0) or self.other_costs_value
        tax_ids = []
        if values.get('invoice_line_tax_ids'):
            tax_ids = values.get('invoice_line_tax_ids', [[6, 0, []]])[
                0][2] or self.invoice_line_tax_ids.ids
        partner_id = values.get('partner_id') or self.partner_id
        currency_id = values.get('currency_id') or self.currency_id
        product_id = values.get('product_id') or self.product_id
        quantity = values.get('quantity') or self.quantity
        fiscal_position = values.get(
            'fiscal_position') or self.fiscal_position_id

        if not product_id or not quantity or not fiscal_position:
            return {}

        result = {
            'code': None,
            'product_type': 'product',
            'service_type_id': None,
            'fiscal_classification_id': None,
            'fci': None,
        }

        if self:
            partner = self.invoice_id.partner_id
            currency = self.invoice_id.currency_id
        else:
            partner = partner_id
            currency = currency_id

        taxes = self.env['account.tax'].browse(tax_ids)

        price = price_unit * (1 - discount / 100.0)

        if product_id:
            product = product_id
            if product.type == 'service':
                result['product_type'] = 'service'
                result['service_type_id'] = product.service_type_id.id
            else:
                result['product_type'] = 'product'
            if product.fiscal_classification_id:
                result['fiscal_classification_id'] = \
                    product.fiscal_classification_id.id

            if product.cest_id:
                result['cest_id'] = product.cest_id.id

            if product.fci:
                result['fci'] = product.fci

            result['code'] = product.default_code
            result['icms_origin'] = product.origin

        taxes_calculed = taxes.compute_all(
            price, quantity=quantity, currency=currency, partner=partner,
            fiscal_position=fiscal_position,
            insurance_value=insurance_value,
            freight_value=freight_value,
            other_costs_value=other_costs_value)

        # result['total_taxes'] = taxes_calculed['total_taxes']

        for tax in taxes_calculed['taxes']:
            try:
                amount_tax = getattr(
                    self, '_amount_tax_%s' % tax.get('domain', ''))
                result.update(amount_tax(tax))
            except AttributeError:
                # Caso não exista campos especificos dos impostos
                # no documento fiscal, os mesmos são calculados.
                continue

        taxes_dict = self._get_tax_codes(product_id, fiscal_position, taxes)

        for key in taxes_dict:
            result[key] = values.get(key) or taxes_dict[key]

        return result

    # TODO não foi migrado por causa do bug github.com/odoo/odoo/issues/1711
    # def fields_view_get(self, cr, uid, view_id=None, view_type=False,
    #                    context=None, toolbar=False, submenu=False):
    #    result = super(AccountInvoiceLine, self).fields_view_get(
    #        cr, uid, view_id=view_id, view_type=view_type, context=context,
    #        toolbar=toolbar, submenu=submenu)
    #    return result

    @api.model
    def _fiscal_position_map(self, **kwargs):
        ctx = dict(self.env.context)
        ctx.update({'use_domain': ('use_invoice', '=', True)})
        ctx.update({'partner_id': kwargs.get('partner_id')})
        ctx.update({'product_id': kwargs.get('product_id')})
        account_obj = self.env['account.account']
        obj_fp_rule = self.env['account.fiscal.position.rule']
        partner = kwargs.get('partner_id')

        product_fiscal_category_id = obj_fp_rule.with_context(
            ctx).product_fiscal_category_map(
            kwargs.get('product_id'), kwargs.get('fiscal_category_id'),
            partner.state_id.id)

        if product_fiscal_category_id:
            kwargs['fiscal_category_id'] = product_fiscal_category_id

        fp = obj_fp_rule.with_context(ctx).apply_fiscal_mapping(**kwargs)
        self.fiscal_category_id = kwargs.get('fiscal_category_id')
        if fp:
            self.fiscal_position_id = fp
            if kwargs.get('product_id'):
                product = kwargs['product_id']
                taxes = self.env['account.tax']
                ctx['fiscal_type'] = product.fiscal_type
                if ctx.get('type') in ('out_invoice', 'out_refund'):
                    ctx['type_tax_use'] = 'sale'
                    if product.taxes_id:
                        taxes |= product.taxes_id
                    elif kwargs.get('account_id'):
                        account_id = kwargs['account_id']
                        taxes |= account_obj.browse(account_id).tax_ids
                else:
                    ctx['type_tax_use'] = 'purchase'
                    if product.supplier_taxes_id:
                        taxes |= product.supplier_taxes_id
                    elif kwargs.get('account_id'):
                        account_id = kwargs['account_id']
                        taxes |= account_obj.browse(account_id).tax_ids
                tax_ids = fp.with_context(ctx).map_tax(
                    taxes, kwargs.get('product_id'))
                self.invoice_line_tax_ids = tax_ids
                self.update(self._get_tax_codes(
                    kwargs['product_id'], fp, tax_ids))

        return fp

    @api.multi
    def product_id_change(self, product, uom_id, qty=0, name='',
                          type='out_invoice', partner_id=False,
                          fposition_id=False, price_unit=False,
                          currency_id=False, company_id=None):
        ctx = dict(self.env.context)
        if type in ('out_invoice', 'out_refund'):
            ctx.update({'type_tax_use': 'sale'})
        else:
            ctx.update({'type_tax_use': 'purchase'})

        result = super(AccountInvoiceLine, self).product_id_change(
            product, uom_id, qty, name, type, partner_id,
            fposition_id, price_unit, currency_id, company_id)

        fiscal_category_id = ctx.get('parent_fiscal_category_id')

        if not fiscal_category_id or not product:
            return result
        product_obj = self.env['product.product'].browse(product)
        result['value']['name'] = product_obj.display_name

        result = self.with_context(ctx)._fiscal_position_map(
            result, partner_id=partner_id, partner_invoice_id=partner_id,
            company_id=company_id, product_id=product,
            fiscal_category_id=fiscal_category_id,
            account_id=result['value']['account_id'])
        return result

    @api.onchange('fiscal_category_id',
                  'fiscal_position_id',
                  'invoice_line_tax_ids',
                  'quantity',
                  'price_unit',
                  'discount',
                  'insurance_value',
                  'freight_value',
                  'other_costs_value')
    def onchange_fiscal(self):
        ctx = dict(self.env.context)
        if self.invoice_id.type in ('out_invoice', 'out_refund'):
            ctx.update({'type_tax_use': 'sale'})
        else:
            ctx.update({'type_tax_use': 'purchase'})

        partner_id = self.invoice_id.partner_id or \
            self.env['res.partner'].browse(ctx.get('partner_id'))
        company_id = self.invoice_id.company_id or \
            self.env['res.company'].browse(ctx.get('company_id'))
        if company_id and partner_id and self.fiscal_category_id:
            kwargs = {
                'company_id': company_id,
                'partner_id': partner_id,
                'partner_invoice_id': self.invoice_id.partner_id,
                'product_id': self.product_id,
                'fiscal_category_id': self.fiscal_category_id,
                'context': ctx
            }
            self.with_context(ctx)._fiscal_position_map(**kwargs)

            kwargs.update({
                'invoice_line_tax_id': [
                    (6, 0, self.invoice_line_tax_ids.ids)],
                'quantity': self.quantity,
                'price_unit': self.price_unit,
                'discount': self.discount,
                'fiscal_position_id': self.fiscal_position_id,
                'insurance_value': self.insurance_value,
                'freight_value': self.freight_value,
                'other_costs_value': self.other_costs_value,
            })

            self.update(self._validate_taxes(kwargs))

    @api.model
    def tax_exists(self, domain=None):
        result = False
        tax = self.env['account.tax'].search(domain, limit=1)
        if tax:
            result = tax
        return result

    @api.multi
    def update_invoice_line_tax_ids(self, tax_id, taxes, domain):
        new_taxes = [(6, 0, [tax_id])]
        for tax in self.env['account.tax'].browse(taxes[0][2]):
            if not tax.domain == domain:
                new_taxes[0][2].append(tax.id)
        return new_taxes

    @api.multi
    def onchange_tax_icms(self, icms_base_type, icms_base, icms_base_other,
                          icms_value, icms_percent, icms_percent_reduction,
                          icms_cst_id, price_unit, discount, quantity,
                          partner_id, product_id, fiscal_position_id,
                          insurance_value, freight_value, other_costs_value,
                          invoice_line_tax_ids):

        result = {'value': {}}
        # ctx = dict(self.env.context)

        # Search if exists the tax
        # domain = [('domain', '=', 'icms')]
        #
        # domain.append(('icms_base_type', '=', icms_base_type))
        #
        # percent_decimal = icms_percent / 100
        # domain.append(('amount', '=', percent_decimal))
        #
        # reduction_percent = icms_percent_reduction / 100
        # domain.append(('base_reduction', '=', reduction_percent))
        #
        # tax = self.tax_exists(domain)
        #
        # # If not exists create a new tax
        # if not tax:
        #     tax_template = self.env['account.tax'].search([
        #         ('type_tax_use', '=', DEFAULT_TAX_TYPE[ctx.get(
        #             'type_tax_use', 'out_invoice')]),
        #         ('domain', '=', 'icms'),
        #         ('amount', '=', '0.0'),
        #         ('company_id', '=', self.env.user.company_id.id),
        #     ])
        #
        #     if not tax_template:
        #         raise except_orm(_('Alerta', u'Não existe imposto\
        #                            do domínio ICMS com aliquita 0%!'))
        #
        #     tax_name = 'ICMS Interno Saída {:.2f}%'.format(icms_percent)
        #
        #     if icms_percent_reduction:
        #         tax_name = 'ICMS Interno Saída {:.2f}% Red \
        #                     {:.2f}%'.format(icms_percent,
        #                                     icms_percent_reduction)
        #
        #     tax_values = {
        #         'name': tax_name,
        #         'description': tax_name,
        #         'type_tax_use': tax_template[0].type_tax_use,
        #         'company_id': tax_template[0].company_id.id,
        #         'active': True,
        #         'type': 'percent',
        #         'amount': icms_percent / 100,
        #         'tax_discount': True,
        #         'base_reduction': icms_percent_reduction / 100,
        #         'applicable_type': 'true',
        #         'icms_base_type': icms_base_type,
        #         'domain': 'icms',
        #         'account_collected_id': (tax_template[0]
        #                                  .account_collected_id.id),
        #         'account_paid_id': tax_template[0].account_paid_id.id,
        #         'base_code_id': tax_template[0].base_code_id.id,
        #         'base_sign': 1.0,
        #         'ref_base_code_id': tax_template[0].ref_base_code_id.id,
        #         'ref_base_sign': 1.0,
        #         'tax_code_id': tax_template[0].tax_code_id.id,
        #         'tax_sign': 1.0,
        #         'ref_tax_code_id': tax_template[0].ref_tax_code_id.id,
        #         'ref_tax_sign': 1.0,
        #     }
        #     tax = self.env['account.tax'].create(tax_values)
        #
        # # Compute the tax
        # partner = self.env['res.partner'].browse(partner_id)
        # product = self.env['product.product'].browse(partner_id)
        # fiscal_position = self.env['account.fiscal.position'].browse(
        #     fiscal_position_id)
        # price = price_unit * (1 - discount / 100.0)
        # tax_compute = tax.compute_all(
        #     price, quantity, product, partner,
        #     fiscal_position=fiscal_position,
        #     insurance_value=insurance_value,
        #     freight_value=freight_value,
        #     other_costs_value=other_costs_value,
        #     base_tax=icms_base)
        #
        # # Update tax values to new values
        # result['value'].update(self._amount_tax_icms(
        # tax_compute['taxes'][0]))
        #
        # # Update invoice_line_tax_id
        # # Remove all taxes with domain ICMS
        # result['value']['invoice_line_tax_id'] = (self
        #      .update_invoice_line_tax_id(tax.id, invoice_line_tax_id,
        #                                  tax.domain))
        return result

    @api.multi
    def onchange_tax_icms_st(
            self,
            icms_st_base_type,
            icms_st_base,
            icms_st_percent,
            icms_st_percent_reduction,
            icms_st_mva,
            icms_st_base_other,
            price_unit,
            discount,
            insurance_value,
            freight_value,
            other_costs_value):
        return {'value': {}}

    @api.multi
    def onchange_tax_ipi(self, ipi_type, ipi_base, ipi_base_other,
                         ipi_value, ipi_percent, ipi_cst_id,
                         price_unit, discount, insurance_value,
                         freight_value, other_costs_value):
        return {'value': {}}

    @api.multi
    def onchange_tax_pis(self, pis_type, pis_base, pis_base_other,
                         pis_value, pis_percent, pis_cst_id,
                         price_unit, discount, insurance_value,
                         freight_value, other_costs_value):
        return {'value': {}}

    @api.multi
    def onchange_tax_pis_st(
            self,
            pis_st_type,
            pis_st_base,
            pis_st_percent,
            pis_st_value,
            price_unit,
            discount,
            insurance_value,
            freight_value,
            other_costs_value):
        return {'value': {}}

    @api.multi
    def onchange_tax_cofins(
            self,
            cofins_st_type,
            cofins_st_base,
            cofins_st_percent,
            cofins_st_value,
            price_unit,
            discount,
            insurance_value,
            freight_value,
            other_costs_value):
        return {'value': {}}

    @api.multi
    def onchange_tax_cofins_st(
            self,
            cofins_st_type,
            cofins_st_base,
            cofins_st_percent,
            cofins_st_value,
            price_unit,
            discount,
            insurance_value,
            freight_value,
            other_costs_value):
        return {'value': {}}

    @api.model
    def create(self, vals):
        vals.update(self._validate_taxes(vals))
        return super(AccountInvoiceLine, self).create(vals)

    # TODO comentado por causa deste bug
    # https://github.com/odoo/odoo/issues/2197
    # @api.multi
    # def write(self, vals):
    #    vals.update(self._validate_taxes(vals))
    #    return super(AccountInvoiceLine, self).write(vals)
