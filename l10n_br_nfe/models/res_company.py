# Copyright (C) 2013  Renato Lima - Akretion
# Copyright (C) 2019  Raphael Valyi - Akretion
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from erpbrasil.base import misc
from odoo import api, fields
from odoo.addons.spec_driven_model.models import spec_models

from ..constants.nfe import (NFE_ENVIRONMENT_DEFAULT, NFE_ENVIRONMENTS,
                             NFE_VERSION_DEFAULT, NFE_VERSIONS)

PROCESSADOR_ERPBRASIL_EDOC = 'erpbrasil_edoc'

PROCESSADOR = [(PROCESSADOR_ERPBRASIL_EDOC, 'erpbrasil.edoc')]


class ResCompany(spec_models.SpecModel):
    _inherit = ['res.company', 'nfe.40.emit']
    _name = "res.company"
    _nfe_search_keys = ['nfe40_CNPJ', 'nfe40_xNome', 'nfe40_xFant']

    nfe_version = fields.Selection(
        selection=NFE_VERSIONS, string="NFe Version", default=NFE_VERSION_DEFAULT
    )

    nfe_environment = fields.Selection(
        selection=NFE_ENVIRONMENTS,
        string="NFe Environment",
        default=NFE_ENVIRONMENT_DEFAULT,
    )

    nfe40_CNPJ = fields.Char(
        compute='_compute_nfe_data',
        inverse='_inverse_nfe40_CNPJ',
    )
    nfe40_IE = fields.Char(
        compute='_compute_nfe_data',
        inverse='_inverse_nfe40_IE',
    )

    nfe_default_serie_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.serie", string="NF-e Default Serie"
    )

    nfe40_CRT = fields.Selection(
        related='tax_framework'
    )

    # in fact enderEmit points to a TEnderEmi type which adds a few
    # constraints over the tendereco injected in res.partner
    # but as theses extra constraints are very few they are better checked here
    nfe40_enderEmit = fields.Many2one(
        "res.partner",
        related='partner_id',
        original_spec_model='nfe.40.tenderemi'
    )
    nfe40_nro = fields.Char(related='street_number')

    processador_edoc = fields.Selection(
        selection_add=PROCESSADOR
    )
    nfe40_xNome = fields.Char(related='partner_id.legal_name')
    nfe40_xFant = fields.Char(related='partner_id.name')
    nfe40_IM = fields.Char(related='partner_id.inscr_mun')

    nfe40_CEP = fields.Char(
        compute='_compute_nfe_data',
        nverse='_inverse_nfe40_zip'
        )

    @api.model
    def _prepare_import_dict(self, vals, defaults=False):
        vals = super(ResCompany, self)._prepare_import_dict(vals, defaults)
        if not vals.get('name'):
            vals['name'] = vals.get('nfe40_xFant') or vals.get('nfe40_xNome')
        return vals

    @api.multi
    def _compute_nfe_data(self):
        """Set schema data which are not just related fields"""
        for rec in self:
            if rec.cnpj_cpf:
                rec.nfe40_CNPJ = misc.punctuation_rm(rec.cnpj_cpf)

            if rec.zip:
                rec.nfe40_CEP = misc.punctuation_rm(rec.zip)

            if rec.inscr_est:
                rec.nfe40_IE = misc.punctuation_rm(rec.inscr_est)

    def _inverse_nfe40_CNPJ(self):
        for rec in self:
            if rec.nfe40_CNPJ:
                rec.is_company = True
                rec.cnpj_cpf = rec.nfe40_CNPJ

    def _inverse_nfe40_zip(self):
        for rec in self:
            if rec.nfe40_ZIP:
                rec.zip = rec.nfe40_ZIP

    def _inverse_nfe40_IE(self):
        for rec in self:
            if rec.nfe40_IE:
                rec.inscr_est = rec.nfe40_IE
