# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def get_credit_limit(self, partner):
        partner_id = self.browse(partner)
        return partner_id.credit_limit

    @api.model
    def get_states_ids(self, id_country):
        state_ids = self.env['res.country.state'].search([('country_id.id', '=', id_country)])
        dict = {}
        for id in state_ids._ids:
            dict[id] = self.env['res.country.state'].browse(id).name
        return dict

    @api.model
    def get_city_ids(self, id_state):
        state_ids = self.env['l10n_br_base.city'].search([('state_id.id', '=', id_state)])
        dict = {}
        for id in state_ids._ids:
            dict[id] = self.env['l10n_br_base.city'].browse(id).name
        return dict

    @api.multi
    def _mask_cnpj_cpf(self, cpfcnpj_type, cnpj_cpf):
        if cnpj_cpf:
            if cpfcnpj_type == 'cnpj' and len(cnpj_cpf) == 14:
                cnpj_cpf = "%s.%s.%s/%s-%s" % (
                    cnpj_cpf[0:2], cnpj_cpf[2:5], cnpj_cpf[5:8],
                    cnpj_cpf[8:12], cnpj_cpf[12:14]
                )
            elif cpfcnpj_type == 'cpf' and len(cnpj_cpf) == 11:
                cnpj_cpf = "%s.%s.%s-%s" % (
                    cnpj_cpf[0:3], cnpj_cpf[3:6], cnpj_cpf[6:9], cnpj_cpf[9:11]
                )
        return cnpj_cpf

    @api.model
    def create_from_ui(self, partner):
        from openerp.addons.l10n_br_base.tools import misc
        cnpj_cpf = misc.punctuation_rm(partner['cnpj_cpf'])
        cnpj_cpf_type = 'cpf' if len(cnpj_cpf) == 11 else 'cnpj'
        partner['cnpj_cpf'] = self._mask_cnpj_cpf(cnpj_cpf_type, cnpj_cpf)
        partner['whatsapp'] = 'sim' == partner['whatsapp']
        partner['opt_out']  = 'sim' == partner['opt_out']
        res = super(ResPartner, self).create_from_ui(partner)
        partner_id = self.browse(res)
        partner_id.legal_name = partner['name']
        if cnpj_cpf_type:
            fiscal_type = self.env.ref('l10n_br_account.partner_fiscal_type_4')
            partner_id.partner_fiscal_type_id = fiscal_type.id
        if self.env.user.company_id.parent_id:
            partner_id.company_id = self.env.user.company_id.parent_id.id
        return res
