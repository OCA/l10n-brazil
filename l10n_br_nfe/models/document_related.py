# Copyright 2020 Akretion (Renato Lima <renato.lima@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class DocumentRelated(spec_models.SpecModel):
    _name = 'l10n_br_fiscal.document.related'
    _inherit = ['l10n_br_fiscal.document.related', 'nfe.40.nfref']
    # _nfe_search_keys = ['nfe40_CNPJ', 'nfe40_CPF', 'nfe40_xNome']

    # @api.model
    # def _prepare_import_dict(self, values, defaults={}):
    #     vals = super()._prepare_import_dict(values)
    #     if not values.get('name') and values.get('legal_name'):
    #         values['name'] = values['legal_name']
    #     return values

    nfe40_choice4 = fields.Selection(
        compute='_compute_nfe_data',
        inverse='_inverse_nfe40_choice4',
        store=True,
    )

    nfe40_refNFe = fields.Char(
        compute='_compute_nfe_data',
        inverse='_inverse_nfe40_refNFe',
        store=True,
    )

    # TODO
    # nfe40_refNF = fields.Many2one(
    #     compute='_compute_nfe_data',
    #     inverse='_inverse_nfe40_refNF',
    #     store=True,
    # )
    #
    # nfe40_refNFP = fields.Many2one(
    #     compute='_compute_nfe_data',
    #     inverse='_inverse_nfe40_refNFP',
    #     store=True,
    # )
    #
    # nfe40_refECF = fields.Many2one(
    #     compute='_compute_nfe_data',
    #     inverse='_inverse_nfe40_refECF',
    #     store=True,
    # )

    @api.multi
    def _compute_nfe_data(self):
        """Set schema data which are not just related fields"""
        for rec in self:
            if rec.document_type_id:
                if rec.document_type_id.code == '55': # TODO Enumerate
                    rec.nfe40_choice4 = 'nfe40_refNFe'
                    rec.nfe40_refNFe = rec.document_key

    def _inverse_nfe40_choice4(self):

        for rec in self:
            if rec.nfe40_choice4 == 'nfe40_refNFe':
                rec.document_type_id = self.env.ref(
                    'l10n_br_fiscal.document_55')

    def _inverse_nfe40_refNFe(self):
        for rec in self:
            if rec.nfe40_refNFe:
                rec.document_key = rec.nfe40_refNFe
