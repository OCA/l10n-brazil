# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.addons.l10n_br_base.tools.misc import punctuation_rm

from .ibpt.taxes import DeOlhoNoImposto, get_ibpt_service


class Nbs(models.Model):
    _name = 'fiscal.nbs'
    _description = 'NBS'

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

    _sql_constraints = [
        ('fiscal_ncm_code_extension_uniq', 'unique (code)',
         'NBS already exists with this code !')]

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
        return [(r.id, "{0} - {1}".format(r.code, r.name))
                for r in self]

    @api.multi
    def get_ibpt(self):

        for nbs in self:

            company = self.env.user.company_id

            config = DeOlhoNoImposto(
                company.ipbt_token,
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
