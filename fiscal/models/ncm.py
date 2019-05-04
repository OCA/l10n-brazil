# Copyright (C) 2012  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.addons.l10n_br_base.tools.misc import punctuation_rm

from .ibpt.taxes import DeOlhoNoImposto, get_ibpt_product


class Ncm(models.Model):
    _name = 'fiscal.ncm'
    _description = 'NCM'

    code = fields.Char(
        string='Code',
        size=10,
        required=True,
        index=True)

    code_unmasked = fields.Char(
         string='Unmasked Code',
         size=8,
         compute='_compute_code_unmasked',
         store=True,
         index=True)

    name = fields.Text(
        string='Name',
        required=True,
        index=True)

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
        string=u'Estimae Taxes',
        readonly=True)

    _sql_constraints = [
        ('fiscal_ncm_code_exception_uniq', 'unique (code, exception)',
         'NCM already exists with this code !')]

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
            domain = ['|', ('code', operator, name + '%')
                      ('code_unmasked', operator, name),
                      ('name', operator, name)]

        recs = self._search(expression.AND([domain, args]), limit=limit,
                            access_rights_uid=name_get_uid)
        return self.browse(recs).name_get()

    @api.multi
    def name_get(self):
        return [(r.id,
                 "{0} - {1}".format(r.code, r.name))
                for r in self]

    @api.multi
    def get_ibpt(self):

        for ncm in self:

            company = self.env.user.company_id

            config = DeOlhoNoImposto(
                company.ipbt_token,
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
