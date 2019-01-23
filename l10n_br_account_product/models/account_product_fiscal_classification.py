# -*- coding: utf-8 -*-
# Copyright (C) 2012  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import timedelta, date

from odoo import models, fields, api

from odoo.addons.l10n_br_account.models.l10n_br_account_tax_definition import (
    L10nBrTaxDefinition
)

from odoo.addons.l10n_br_account.sped.ibpt.deolhonoimposto import (
    DeOlhoNoImposto,
    get_ibpt_product
)
from odoo.addons.l10n_br_base.tools.misc import punctuation_rm


class AccountProductFiscalClassification(models.Model):
    _inherit = 'account.product.fiscal.classification'
    _rec_name = 'code'

    @api.multi
    @api.depends('purchase_tax_definition_line',
                 'sale_tax_definition_line')
    def _compute_taxes(self):
        for fc in self:
            fc.sale_tax_ids = [line.tax_id.id for line in
                               fc.sale_tax_definition_line]
            fc.purchase_tax_ids = [line.tax_id.id for line in
                                   fc.purchase_tax_definition_line]

    @api.multi
    @api.depends('tax_estimate_ids')
    def _compute_product_estimated_taxes_percent(self):
        for record in self:
            t_ids = record.tax_estimate_ids.ids
            last_estimated = self.env['l10n_br_tax.estimate'].search(
                [('id', 'in', t_ids)], order='create_date DESC', limit=1)

            record.estd_import_taxes_perct = (
                last_estimated.federal_taxes_import +
                last_estimated.state_taxes + last_estimated.municipal_taxes)
            record.estd_national_taxes_perct = (
                last_estimated.federal_taxes_national +
                last_estimated.state_taxes + last_estimated.municipal_taxes)

    type = fields.Selection(
        selection=[('view', u'Visão'),
                   ('normal', 'Normal'),
                   ('extension', u'Extensão')],
        string=u'Tipo',
        default='normal')

    note = fields.Text(
        string=u'Observações')

    inv_copy_note = fields.Boolean(
        string=u'Copiar Observação',
        help=u"Copia a observação no documento fiscal")

    parent_id = fields.Many2one(
        comodel_name='account.product.fiscal.classification',
        string=u'Parent Fiscal Classification',
        domain="[('type', 'in', ('view', 'normal'))]",
        index=True)

    child_ids = fields.One2many(
        comodel_name='account.product.fiscal.classification',
        inverse_name='parent_id',
        string=u'Child Fiscal Classifications')

    sale_tax_definition_line = fields.One2many(
        comodel_name='l10n_br_tax.definition.sale',
        inverse_name='fiscal_classification_id',
        string=u'Taxes Definitions')

    sale_tax_ids = fields.Many2many(
        comodel_name='account.tax',
        string=u'Sale Taxes',
        compute='_compute_taxes',
        store=True)

    purchase_tax_definition_line = fields.One2many(
        comodel_name='l10n_br_tax.definition.purchase',
        inverse_name='fiscal_classification_id',
        string=u'Taxes Definitions')

    purchase_tax_ids = fields.Many2many(
        comodel_name='account.tax',
        string='Purchase Taxes',
        compute='_compute_taxes',
        store=True)

    tax_estimate_ids = fields.One2many(
        comodel_name='l10n_br_tax.estimate',
        inverse_name='fiscal_classification_id',
        string=u'Impostos Estimados',
        readonly=True)

    estd_import_taxes_perct = fields.Float(
        string=u'Impostos de Importação Estimados(%)',
        compute='_compute_product_estimated_taxes_percent',
        store=True)

    estd_national_taxes_perct = fields.Float(
        string=u'Impostos Nacionais Estimados(%)',
        compute='_compute_product_estimated_taxes_percent',
        store=True)

    _sql_constraints = [
        ('account_fiscal_classfication_code_uniq', 'unique (code)',
         u'Já existe um classificação fiscal com esse código!')]

    @api.multi
    def get_ibpt(self):
        for fiscal_classification in self:

            company = (
                fiscal_classification.env.user.company_id or
                fiscal_classification.company_id)

            config = DeOlhoNoImposto(
                company.ipbt_token, punctuation_rm(company.cnpj_cpf),
                company.state_id.code)

            result = get_ibpt_product(
                config,
                punctuation_rm(fiscal_classification.code or ''),
            )

            vals = {
                'fiscal_classification_id': fiscal_classification.id,
                'origin': 'IBPT-WS',
                'state_id': company.state_id.id,
                'state_taxes': result.estadual,
                'federal_taxes_national': result.nacional,
                'federal_taxes_import': result.importado,
                'company_id': company.id,
                }

            tax_estimate = fiscal_classification.env[
                'l10n_br_tax.estimate']

            tax_estimate.create(vals)

        return True

    @api.model
    def update_due_ncm(self):

        config_date = self.env['account.config.settings'].browse(
            [1]).ibpt_update_days
        today = date.today()
        data_max = today - timedelta(days=config_date)

        all_ncm = self.env[
            'account.product.fiscal.classification'].search([])

        not_estimated = all_ncm.filtered(
            lambda r: r.product_tmpl_qty > 0 and not r.tax_estimate_ids
        )

        query = (
            "WITH ncm_max_date AS ("
            "   SELECT "
            "       fiscal_classification_id, "
            "       max(create_date) "
            "   FROM  "
            "       l10n_br_tax_estimate "
            "   GROUP BY "
            "       fiscal_classification_id"
            ") SELECT fiscal_classification_id "
            "FROM "
            "   ncm_max_date "
            "WHERE "
            "   max < %(create_date)s  "
        )
        query_params = {'create_date': data_max.strftime('%Y-%m-%d')}

        self._cr.execute(self._cr.mogrify(query, query_params))
        past_estimated = self._cr.fetchall()

        ids = [estimate[0] for estimate in past_estimated]

        ncm_past_estimated = self.env[
            'account.product.fiscal.classification'].browse(ids)

        for ncm in not_estimated + ncm_past_estimated:
            try:
                ncm.get_ibpt()
            except Exception:
                pass


class L10nBrTaxEstimate(models.Model):
    _name = 'l10n_br_tax.estimate'
    _inherit = 'l10n_br_tax.estimate.model'

    fiscal_classification_id = fields.Many2one(
        comodel_name='account.product.fiscal.classification',
        string=u'Fiscal Classification',
        index=True)


class L10nBrTaxDefinitionModel(L10nBrTaxDefinition):
    _name = 'l10n_br_tax.definition.model'

    fiscal_classification_id = fields.Many2one(
        comodel_name='account.product.fiscal.classification',
        string=u'Parent Fiscal Classification',
        index=True)

    cst_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cst',
        domain="[('tax_group_id', '=', tax_group_id)]",
        string='CST')

    tax_ipi_guideline_id = fields.Many2one(
        comodel_name='l10n_br_account_product.ipi_guideline',
        string=u'Enquadramento IPI')

    tax_icms_relief_id = fields.Many2one(
        comodel_name='l10n_br_account_product.icms_relief',
        string=u'Desoneração ICMS')

    _sql_constraints = [
        ('l10n_br_tax_definition_tax_id_uniq', 'unique (tax_id,\
        fiscal_classification_id)',
         u'Imposto já existente nesta classificação fiscal!')]

    @api.onchange('tax_id')
    def _onchange_tax_template_id(self):
        if self.tax_id.tax_group_id != self.cst_id.tax_group_id:
            self.cst_id = None


class L10nBrTaxDefinitionSale(L10nBrTaxDefinitionModel, models.Model):
    _name = 'l10n_br_tax.definition.sale'


class L10nBrTaxDefinitionPurchase(L10nBrTaxDefinitionModel, models.Model):
    _name = 'l10n_br_tax.definition.purchase'
