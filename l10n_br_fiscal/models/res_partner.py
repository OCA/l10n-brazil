# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2020 - TODAY Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

from ..constants.fiscal import (
    NFE_IND_IE_DEST,
    NFE_IND_IE_DEST_9,
    NFE_IND_IE_DEST_DEFAULT,
    TAX_FRAMEWORK,
    TAX_FRAMEWORK_NORMAL,
)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _default_fiscal_profile_id(self, is_company=False):
        """Define o valor padão para o campo tipo fiscal, por padrão pega
        o tipo fiscal para não contribuinte já que quando é criado um novo
        parceiro o valor do campo is_company é false"""
        return self.env["l10n_br_fiscal.partner.profile"].search(
            [('default', '=', True), ('is_company', '=', is_company)],
            limit=1)

    @api.multi
    def _compute_fiscal_document_count(self):
        for partner in self:
            partner.fiscal_documents_count = partner.fiscal_document_ids.search_count(
                [('partner_id', '=', partner.id)]
            )

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        default=TAX_FRAMEWORK_NORMAL,
        string='Tax Framework',
        track_visibility='onchange',
    )

    cnae_main_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cnae',
        domain=[('internal_type', '=', 'normal')],
        string='Main CNAE',
    )

    ind_ie_dest = fields.Selection(
        selection=NFE_IND_IE_DEST,
        string='Contribuinte do ICMS',
        required=True,
        default=NFE_IND_IE_DEST_DEFAULT,
        track_visibility='onchange',
    )

    fiscal_profile_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.partner.profile',
        string='Fiscal Partner Profile',
        inverse='_inverse_fiscal_profile',
        domain="[('is_company', '=', is_company)]",
        default=_default_fiscal_profile_id,
        track_visibility='onchange',
    )

    cnpj_cpf = fields.Char(
        track_visibility='onchange',
    )

    inscr_est = fields.Char(
        track_visibility='onchange',
    )

    inscr_mun = fields.Char(
        track_visibility='onchange',
    )

    is_company = fields.Boolean(
        track_visibility='onchange',
    )

    state_id = fields.Many2one(
        track_visibility='onchange',
    )

    city_id = fields.Many2one(
        track_visibility='onchange',
    )

    fiscal_documents_count = fields.Integer(
        compute='_compute_fiscal_document_count',
        string="Fiscal Document Count",
    )

    fiscal_document_ids = fields.One2many(
        'l10n_br_fiscal.document',
        'partner_id',
        string='Fiscal Documents',
        readonly=True,
        copy=False
    )

    def _inverse_fiscal_profile(self):
        for p in self:
            p._onchange_fiscal_profile_id()

    @api.onchange('is_company')
    def _onchange_is_company(self):
        for p in self:
            p.fiscal_profile_id = p._default_fiscal_profile_id(p.is_company)

    @api.onchange('fiscal_profile_id')
    def _onchange_fiscal_profile_id(self):
        for p in self:
            if p.fiscal_profile_id:
                p.tax_framework = p.fiscal_profile_id.tax_framework
                p.ind_ie_dest = p.fiscal_profile_id.ind_ie_dest

    @api.onchange('ind_ie_dest')
    def _onchange_ind_ie_dest(self):
        for p in self:
            if p.ind_ie_dest == NFE_IND_IE_DEST_9:
                p.inscr_est = False
                p.state_tax_number_ids = False

    @api.multi
    def action_view_document(self):
        action = self.env.ref('l10n_br_fiscal.document_out_action').read()[0]
        if len(self.fiscal_document_ids) > 1:
            action['domain'] = [
                ('id', 'in', self.fiscal_document_ids.ids),
            ]
        elif len(self.fiscal_document_ids) == 1:
            form_view = [
                (self.env.ref('l10n_br_fiscal.document_form').id, 'form'),
            ]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view
                                               in action['views'] if
                                               view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = self.fiscal_document_ids.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
