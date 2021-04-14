# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

from ..constants.fiscal import (
    FISCAL_IN_OUT,
    FINAL_CUSTOMER,
    FINAL_CUSTOMER_YES,
    NFE_IND_PRES,
    NFE_IND_PRES_DEFAULT,
    FISCAL_COMMENT_DOCUMENT,
)


class FiscalDocumentMixin(models.AbstractModel):
    _name = 'l10n_br_fiscal.document.mixin'
    _inherit = 'l10n_br_fiscal.document.mixin.methods'
    _description = 'Document Fiscal Mixin'

    def _date_server_format(self):
        return fields.Datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def _default_operation(self):
        return False

    @api.model
    def _operation_domain(self):
        domain = [('state', '=', 'approved'),
                  '|', ('company_id', '=', self.env.user.company_id.id),
                  ('company_id', '=', False)]
        return domain

    fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        string='Operation',
        domain=lambda self: self._operation_domain(),
        default=_default_operation,
    )

    #
    # Company and Partner are defined here to avoid warnings on runbot
    #
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
    )

    fiscal_operation_type = fields.Selection(
        selection=FISCAL_IN_OUT,
        related='fiscal_operation_id.fiscal_operation_type',
        string='Fiscal Operation Type',
        readonly=True,
    )

    ind_pres = fields.Selection(
        selection=NFE_IND_PRES,
        string='Buyer Presence',
        default=NFE_IND_PRES_DEFAULT,
    )

    comment_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.comment',
        relation='l10n_br_fiscal_document_mixin_comment_rel',
        column1='document_mixin_id',
        column2='comment_id',
        string='Comments',
        domain=[('object', '=', FISCAL_COMMENT_DOCUMENT)],
    )

    fiscal_additional_data = fields.Text(
        string='Fiscal Additional Data',
    )

    customer_additional_data = fields.Text(
        string='Customer Additional Data',
    )

    ind_final = fields.Selection(
        selection=FINAL_CUSTOMER,
        string='Final Consumption Operation',
        default=FINAL_CUSTOMER_YES,
    )

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        default=lambda self: self.env.user.company_id.currency_id,
        store=True,
        readonly=True,
    )

    amount_price_gross = fields.Monetary(
        compute='_compute_amount',
        string='Amount Gross',
        store=True,
        readonly=True,
        help="Amount without discount.",
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

    amount_icmsst_base = fields.Monetary(
        string='ICMS ST Base',
        compute='_compute_amount',
    )

    amount_icmsst_value = fields.Monetary(
        string='ICMS ST Value',
        compute='_compute_amount',
    )

    amount_icmssn_value = fields.Monetary(
        string='ICMSSN Value',
        compute='_compute_amount',
    )

    amount_icmsfcp_base = fields.Monetary(
        string='ICMS FCP Base',
        compute='_compute_amount',
    )

    amount_icmsfcp_value = fields.Monetary(
        string='ICMS FCP Value',
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

    amount_estimate_tax = fields.Monetary(
        string='Amount Estimate Tax',
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

    amount_tax_withholding = fields.Monetary(
        string="Amount Tax Withholding",
        compute='_compute_amount')

    amount_financial = fields.Monetary(
        string='Amount Financial',
        compute='_compute_amount',
    )

    amount_discount_value = fields.Monetary(
        string='Amount Discount',
        compute='_compute_amount',
    )

    amount_insurance_value = fields.Monetary(
        string='Insurance Value',
        default=0.00,
        compute='_compute_amount',
    )

    amount_other_value = fields.Monetary(
        string='Other Costs',
        default=0.00,
        compute='_compute_amount',
    )

    amount_freight_value = fields.Monetary(
        string='Freight Value',
        default=0.00,
        compute='_compute_amount',
    )
