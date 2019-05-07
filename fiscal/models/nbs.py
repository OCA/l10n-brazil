# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.addons.l10n_br_base.tools.misc import punctuation_rm
from odoo.osv import expression

from .ibpt.taxes import DeOlhoNoImposto, get_ibpt_service

_logger = logging.getLogger(__name__)


class Nbs(models.Model):
    _name = 'fiscal.nbs'
    _inherit = ['mail.thread']
    _description = 'NBS'
    _order = 'code'

    code = fields.Char(
        string='Code',
        size=12,
        required=True,
        index=True)

    code_unmasked = fields.Char(
         string='Unmasked Code',
         size=10,
         compute='_compute_code_unmasked',
         store=True,
         index=True)

    name = fields.Text(
        string='Name',
        required=True,
        index=True)

    tax_estimate_ids = fields.One2many(
        comodel_name='fiscal.tax.estimate',
        inverse_name='nbs_id',
        string=u'Estimae Taxes',
        readonly=True)

    product_tmpl_ids = fields.One2many(
        comodel_name='product.template',
        string='Products',
        compute='_compute_product_tmpl_info')

    product_tmpl_qty = fields.Integer(
        string='Products Quantity',
        compute='_compute_product_tmpl_info')

    _sql_constraints = [
        ('fiscal_ncm_code_extension_uniq', 'unique (code)',
         'NBS already exists with this code !')]

    @api.one
    def _compute_product_tmpl_info(self):
        product_tmpls = self.env['product.template'].search([
            ('nbs_id', '=', self.id), '|',
            ('active', '=', False), ('active', '=', True)])
        self.product_tmpl_ids = product_tmpls
        self.product_tmpl_qty = len(product_tmpls)

    @api.depends('code')
    def _compute_code_unmasked(self):
        for r in self:
            # TODO mask code and unmasck
            r.code_unmasked = punctuation_rm(r.code)

    @api.model
    def _name_search(self, name, args=None, operator='ilike',
                     limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', ('code', operator, name + '%'),
                      ('code_unmasked', operator, name),
                      ('name', operator, name)]

        recs = self._search(expression.AND([domain, args]), limit=limit,
                            access_rights_uid=name_get_uid)
        return self.browse(recs).name_get()

    @api.multi
    def name_get(self):
        def truncate_name(name):
            if len(name) > 60:
                name = '{0}...'.format(name[:60])
            return name

        return [(r.id,
                 "{0} - {1}".format(r.code, truncate_name(r.name)))
                for r in self]

    @api.multi
    def get_ibpt(self):
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

                self.env['fiscal.tax.estimate'].create(values)

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

        all_nbs = self.env['fiscal.nbs'].search([])

        not_estimated = all_nbs.filtered(
            lambda r: r.product_tmpl_qty > 0 and not r.tax_estimate_ids)

        query = (
            "WITH nbs_max_date AS ("
            "   SELECT "
            "       nbs_id, "
            "       max(create_date) "
            "   FROM  "
            "       fiscal_tax_estimate "
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

        nbs_past_estimated = self.env['fiscal.nbs'].browse(ids)

        for nbs in not_estimated + nbs_past_estimated:
            try:
                nbs.get_ibpt()
            except Exception:
                continue

        _logger.info('Scheduled NBS estimate taxes update complete.')
