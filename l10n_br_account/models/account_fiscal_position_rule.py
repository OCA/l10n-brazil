# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import time

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from .res_company import COMPANY_FISCAL_TYPE, COMPANY_FISCAL_TYPE_DEFAULT


class AccountFiscalPositionRuleAbstract(object):

    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria')
    fiscal_type = fields.Selection(
        COMPANY_FISCAL_TYPE, u'Regime Tributário', required=True,
        default=COMPANY_FISCAL_TYPE_DEFAULT)
    revenue_start = fields.Float(
        'Faturamento Inicial', digits=dp.get_precision('Account'),
        default=0.00, help="Faixa inicial de faturamento bruto")
    revenue_end = fields.Float(
        'Faturamento Final', digits=dp.get_precision('Account'),
        default=0.00, help="Faixa inicial de faturamento bruto")


class AccountFiscalPositionRuleTemplate(AccountFiscalPositionRuleAbstract,
                                        models.Model):
    _inherit = 'account.fiscal.position.rule.template'

    partner_fiscal_type_id = fields.Many2many(
        comodel_name='l10n_br_account.partner.fiscal.type',
        relation='afp_rule_template_l10n_br_account_partner_fiscal_type',
        column1='afp_template',
        column2='partner_fiscal_type',
        string='Tipo Fiscal do Parceiro',
    )
    partner_special_fiscal_type_id = fields.Many2many(
        comodel_name='l10n_br_account.partner.special.fiscal.type',
        relation=(
            'afp_rule_template_l10n_br_account_partner_special_fiscal_type'
        ),
        column1='afp_id',
        column2='partner_special_fiscal_type_id',
        string='Regime especial'
    )


class AccountFiscalPositionRule(AccountFiscalPositionRuleAbstract,
                                models.Model):

    _inherit = 'account.fiscal.position.rule'

    partner_fiscal_type_id = fields.Many2many(
        comodel_name='l10n_br_account.partner.fiscal.type',
        relation='afp_rule_l10n_br_account_partner_fiscal_type',
        column1='afp_id',
        column2='partner_fiscal_type_id',
        string='Tipo Fiscal do Parceiro'
    )
    partner_special_fiscal_type_id = fields.Many2many(
        comodel_name='l10n_br_account.partner.special.fiscal.type',
        relation='afp_rule_l10n_br_account_partner_special_fiscal_type',
        column1='afp_id',
        column2='partner_special_fiscal_type_id',
        string='Regime especial'
    )

    def _map_domain(self, partner, addrs, company, **kwargs):
        from_country = company.partner_id.country_id.id
        from_state = company.partner_id.state_id.id
        partner_fiscal_type_id = partner.partner_fiscal_type_id.id

        document_date = self.env.context.get('date', time.strftime('%Y-%m-%d'))
        use_domain = self.env.context.get(
            'use_domain', ('use_sale', '=', True))
        special_domain = []
        domain = ['&']
        for special in self.env[
            'l10n_br_account.partner.special.fiscal.type'
        ].search([]).ids:
            if special in partner.partner_special_fiscal_type_id.ids:
                special_domain.append(
                    ('partner_special_fiscal_type_id', 'in', special))
            else:
                special_domain.append(
                    ('partner_special_fiscal_type_id', 'not in', special))
        if special_domain:
            domain += special_domain
        else:
            domain += [('partner_special_fiscal_type_id', '=', False)]

        if kwargs.get('fiscal_category_id'):
            fiscal_category_id = kwargs.get('fiscal_category_id').id
        else:
            fiscal_category_id = False

        domain += [
            ('company_id', '=', company.id), use_domain,
            ('fiscal_type', '=', company.fiscal_type),
            ('fiscal_category_id', '=', fiscal_category_id),
            '|', ('partner_fiscal_type_id', '=', partner_fiscal_type_id),
            ('partner_fiscal_type_id', '=', False),
            '|', ('from_country', '=', from_country),
            ('from_country', '=', False),
            '|', ('from_state', '=', from_state),
            ('from_state', '=', False),
            '|', ('date_start', '=', False),
            ('date_start', '<=', document_date),
            '|', ('date_end', '=', False),
            ('date_end', '>=', document_date),
            '|', ('revenue_start', '=', False),
            ('revenue_start', '<=', company.annual_revenue),
            '|', ('revenue_end', '=', False),
            ('revenue_end', '>=', company.annual_revenue)]

        if kwargs.get('fiscal_category_id'):
            fc = kwargs.get('fiscal_category_id')
            domain += [('fiscal_category_id', '=', fc.id)]

        for address_type, address in addrs.items():
            key_country = 'to_%s_country' % address_type
            key_state = 'to_%s_state' % address_type
            to_country = address.country_id.id or False
            domain += [
                '|', (key_country, '=', to_country),
                (key_country, '=', False)]
            to_state = address.state_id.id or False
            domain += [
                '|', (key_state, '=', to_state), (key_state, '=', False)]

        return domain

    def product_fiscal_category_map(self, product_id, fiscal_category_id,
                                    to_state_id=None):
        result = None

        if not product_id or not fiscal_category_id:
            return result
        product_tmpl_id = product_id.product_tmpl_id
        fiscal_category = self.env[
            'l10n_br_account.product.category'].search(
            [('product_tmpl_id', '=', product_tmpl_id.id),
             ('fiscal_category_source_id', '=', fiscal_category_id.id),
             '|', ('to_state_id', '=', False),
             ('to_state_id', '=', to_state_id)], limit=1)
        if fiscal_category:
            result = fiscal_category.fiscal_category_destination_id
        return result


class WizardAccountFiscalPositionRule(models.TransientModel):
    _inherit = 'wizard.account.fiscal.position.rule'

    @api.multi
    def action_create(self):
        super(WizardAccountFiscalPositionRule, self).action_create()

        obj_wizard = self

        obj_fpr = self.env['account.fiscal.position.rule']
        obj_fpr_templ = self.env['account.fiscal.position.rule.template']

        company_id = obj_wizard.company_id.id
        pfr_ids = obj_fpr_templ.search([])

        for fpr_template in pfr_ids:

            from_country = fpr_template.from_country.id or False
            from_state = fpr_template.from_state.id or False
            to_invoice_country = fpr_template.to_invoice_country.id or False
            to_invoice_state = fpr_template.to_invoice_state.id or False
            partner_ft_id = fpr_template.partner_fiscal_type_id.id or False
            fiscal_category_id = fpr_template.fiscal_category_id.id or False

            fiscal_position_id = self.env['account.fiscal.position'].search([
                ('name', '=', fpr_template.fiscal_position_id.name),
                ('company_id', '=', company_id)], limit=1)

            fprt_id = obj_fpr.search([
                ('name', '=', fpr_template.name),
                ('company_id', '=', company_id),
                ('description', '=', fpr_template.description),
                ('from_country', '=', from_country),
                ('from_state', '=', from_state),
                ('to_invoice_country', '=', to_invoice_country),
                ('to_invoice_state', '=', to_invoice_state),
                ('use_sale', '=', fpr_template.use_sale),
                ('use_invoice', '=', fpr_template.use_invoice),
                ('use_purchase', '=', fpr_template.use_purchase),
                ('use_picking', '=', fpr_template.use_picking),
                ('fiscal_position_id', '=', fiscal_position_id.id)])

            if fprt_id:
                obj_fpr.write({
                    'partner_fiscal_type_id': partner_ft_id,
                    'fiscal_category_id': fiscal_category_id,
                    'fiscal_type': fpr_template.fiscal_type,
                    'revenue_start': fpr_template.revenue_start,
                    'revenue_end': fpr_template.revenue_end})
        return {}
