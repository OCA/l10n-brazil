# Copyright (C) 2012  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from datetime import timedelta
from lxml import etree

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.osv import orm
from odoo.addons.l10n_br_base.tools.misc import punctuation_rm

from .ibpt.taxes import DeOlhoNoImposto, get_ibpt_product

_logger = logging.getLogger(__name__)


class Ncm(models.Model):
    _name = 'fiscal.ncm'
    _inherit = ['fiscal.data.abstract', 'mail.thread', 'mail.activity.mixin']
    _description = 'NCM'

    @api.one
    @api.depends('tax_estimate_ids')
    def _compute_amount(self):
        last_estimated = self.env['fiscal.tax.estimate'].search(
            [('ncm_id', '=', self.id),
             ('company_id', '=', self.env.user.company_id.id)],
            order='create_date DESC',
            limit=1)

        if last_estimated:
            self.estimate_tax_imported = (
                last_estimated.federal_taxes_import +
                last_estimated.state_taxes + last_estimated.municipal_taxes)
            self.estimate_tax_national = (
                last_estimated.federal_taxes_national +
                last_estimated.state_taxes + last_estimated.municipal_taxes)

    code = fields.Char(
        size=10)

    code_unmasked = fields.Char(
         size=8)

    exception = fields.Char(
        string='Exception',
        size=2)

    tax_ipi_id = fields.Many2one(
        comodel_name='fiscal.tax',
        string='Tax IPI',
        domain="[('tax_domain', '=', 'ipi')]")

    tax_ii_id = fields.Many2one(
        comodel_name='fiscal.tax',
        string='Tax II',
        domain="[('tax_domain', '=', 'ii')]")

    tax_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Tax Unit')

    tax_estimate_ids = fields.One2many(
        comodel_name='fiscal.tax.estimate',
        inverse_name='ncm_id',
        string=u'Estimate Taxes',
        readonly=True)

    product_tmpl_ids = fields.One2many(
        comodel_name='product.template',
        string='Products',
        compute='_compute_product_tmpl_info')

    product_tmpl_qty = fields.Integer(
        string='Products Quantity',
        compute='_compute_product_tmpl_info')

    estimate_tax_national = fields.Float(
        string='Estimate Tax Nacional Percent',
        store=True,
        readonly=True,
        digits=dp.get_precision('Fiscal Tax Percent'),
        compute='_compute_amount')

    estimate_tax_imported = fields.Float(
        string='Estimate Tax Imported Percent',
        store=True,
        readonly=True,
        digits=dp.get_precision('Fiscal Tax Percent'),
        compute='_compute_amount')

    _sql_constraints = [
        ('fiscal_ncm_code_exception_uniq', 'unique (code, exception)',
         'NCM already exists with this code !')]

    @api.one
    def _compute_product_tmpl_info(self):
        product_tmpls = self.env['product.template'].search([
            ('ncm_id', '=', self.id), '|',
            ('active', '=', False), ('active', '=', True)])
        self.product_tmpl_ids = product_tmpls
        self.product_tmpl_qty = len(product_tmpls)

    @api.multi
    def get_ibpt(self):
        if not self.env.user.company_id.ibpt_api:
            return False

        for ncm in self:
            try:
                company = self.env.user.company_id

                config = DeOlhoNoImposto(
                    company.ibpt_token,
                    punctuation_rm(company.cnpj_cpf),
                    company.state_id.code)

                result = get_ibpt_product(
                    config,
                    ncm.code_unmasked,
                )

                values = {
                    'ncm_id': ncm.id,
                    'origin': 'IBPT-WS',
                    'state_id': company.state_id.id,
                    'state_taxes': result.estadual,
                    'federal_taxes_national': result.nacional,
                    'federal_taxes_import': result.importado}

                self.env['fiscal.tax.estimate'].create(values)

                ncm.message_post(
                    body=_('NCM Tax Estimate Updated'),
                    subject=_('NCM Tax Estimate Updated'))

            except Exception as e:
                _logger.warning('NCM Tax Estimate Failure: %s' % e)
                ncm.message_post(
                    body=str(e),
                    subject=_('NCM Tax Estimate Failure'))
                continue

    @api.model
    def _scheduled_update(self):
        _logger.info('Scheduled NCM estimate taxes update...')

        config_date = self.env.user.company_id.ibpt_update_days
        today = fields.date.today()
        data_max = today - timedelta(days=config_date)

        all_ncm = self.env['fiscal.ncm'].search([])

        not_estimated = all_ncm.filtered(
            lambda r: r.product_tmpl_qty > 0 and not r.tax_estimate_ids)

        query = (
            "WITH ncm_max_date AS ("
            "   SELECT "
            "       ncm_id, "
            "       max(create_date) "
            "   FROM  "
            "       fiscal_tax_estimate "
            "   GROUP BY "
            "       ncm_id"
            ") SELECT ncm_id "
            "FROM "
            "   ncm_max_date "
            "WHERE "
            "   max < %(create_date)s  ")

        query_params = {'create_date': data_max.strftime('%Y-%m-%d')}

        self.env.cr.execute(self.env.cr.mogrify(query, query_params))
        past_estimated = self.env.cr.fetchall()

        ids = [estimate[0] for estimate in past_estimated]

        ncm_past_estimated = self.env['fiscal.ncm'].browse(ids)

        for ncm in not_estimated + ncm_past_estimated:
            try:
                ncm.get_ibpt()
            except Exception:
                continue

        _logger.info('Scheduled NCM estimate taxes update complete.')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(Ncm, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if view_type == 'form':
            xml = etree.XML(res['arch'])
            xml_button = xml.xpath("//button[@name='get_ibpt']")
            if xml_button and not self.env.user.company_id.ibpt_api:
                xml_button[0].attrib['invisible'] = '1'
                orm.setup_modifiers(xml_button[0])
                res['arch'] = etree.tostring(xml, pretty_print=True)
        if res.get('toolbar') and not self.env.user.company_id.ibpt_api:
            res['toolbar']['action'] = []
        return res
