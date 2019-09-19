# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from datetime import timedelta
from lxml import etree

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.osv import orm
from erpbrasil.base.misc import punctuation_rm

from .ibpt.taxes import DeOlhoNoImposto, get_ibpt_service

_logger = logging.getLogger(__name__)


class Nbs(models.Model):
    _name = 'l10n_br_fiscal.nbs'
    _inherit = ['l10n_br_fiscal.data.abstract',
                'mail.thread',
                'mail.activity.mixin']
    _description = 'NBS'

    @api.one
    @api.depends('tax_estimate_ids')
    def _compute_amount(self):
        last_estimated = self.env['l10n_br_fiscal.tax.estimate'].search(
            [('nbs_id', '=', self.id),
             ('company_id', '=', self.env.user.company_id.id)],
            order='create_date DESC',
            limit=1)

        self.estimate_tax_imported = (
            last_estimated.federal_taxes_import +
            last_estimated.state_taxes + last_estimated.municipal_taxes)
        self.estimate_tax_national = (
            last_estimated.federal_taxes_national +
            last_estimated.state_taxes + last_estimated.municipal_taxes)

    code = fields.Char(
        size=12)

    code_unmasked = fields.Char(
        size=10)

    tax_estimate_ids = fields.One2many(
        comodel_name='l10n_br_fiscal.tax.estimate',
        inverse_name='nbs_id',
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
        ('fiscal_nbs_code_uniq', 'unique (code)',
         'NBS already exists with this code !')]

    @api.one
    def _compute_product_tmpl_info(self):
        product_tmpls = self.env['product.template'].search([
            ('nbs_id', '=', self.id), '|',
            ('active', '=', False), ('active', '=', True)])
        self.product_tmpl_ids = product_tmpls
        self.product_tmpl_qty = len(product_tmpls)

    @api.multi
    def get_ibpt(self):
        if not self.env.user.company_id.ibpt_api:
            return False

        for nbs in self:
            try:
                company = self.env.user.company_id

                config = DeOlhoNoImposto(
                    company.ibpt_token,
                    punctuation_rm(company.cnpj_cpf),
                    company.state_id.code)

                result = get_ibpt_service(
                    config,
                    nbs.code_unmasked,
                )

                values = {
                    'nbs_id': nbs.id,
                    'origin': 'IBPT-WS',
                    'state_id': company.state_id.id,
                    'state_taxes': result.estadual,
                    'federal_taxes_national': result.nacional,
                    'federal_taxes_import': result.importado}

                self.env['l10n_br_fiscal.tax.estimate'].create(values)

                nbs.message_post(
                    body=_('NBS Tax Estimate Updated'),
                    subject=_('NBS Tax Estimate Updated'))

            except Exception as e:
                _logger.warning('NBS Tax Estimate Failure: %s' % e)
                nbs.message_post(
                    body=str(e),
                    subject=_('NBS Tax Estimate Failure'))
                continue

    @api.model
    def _scheduled_update(self):
        _logger.info('Scheduled NBS estimate taxes update...')

        config_date = self.env.user.company_id.ibpt_update_days
        today = fields.date.today()
        data_max = today - timedelta(days=config_date)

        all_nbs = self.env['l10n_br_fiscal.nbs'].search([])

        not_estimated = all_nbs.filtered(
            lambda r: r.product_tmpl_qty > 0 and not r.tax_estimate_ids)

        query = (
            "WITH nbs_max_date AS ("
            "   SELECT "
            "       nbs_id, "
            "       max(create_date) "
            "   FROM  "
            "       l10n_br_fiscal_tax_estimate "
            "   GROUP BY "
            "       nbs_id"
            ") SELECT nbs_id "
            "FROM "
            "   nbs_max_date "
            "WHERE "
            "   max < %(create_date)s  ")

        query_params = {'create_date': data_max.strftime('%Y-%m-%d')}

        self.env.cr.execute(self.env.cr.mogrify(query, query_params))
        past_estimated = self.env.cr.fetchall()

        ids = [estimate[0] for estimate in past_estimated]

        nbs_past_estimated = self.env['l10n_br_fiscal.nbs'].browse(ids)

        for nbs in not_estimated + nbs_past_estimated:
            try:
                nbs.get_ibpt()
            except Exception:
                continue

        _logger.info('Scheduled NBS estimate taxes update complete.')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(Nbs, self).fields_view_get(
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
