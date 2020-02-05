# Copyright (C) 2013  Renato Lima - Akretion
# Copyright (C) 2019  Raphael Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

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

    nfe_default_serie_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.serie", string="NF-e Default Serie"
    )

    # in fact enderEmit points to a TEnderEmi type which adds a few
    # constraints over the tendereco injected in res.partner
    # but as theses extra constraints are very few they are better checked here
    nfe40_enderEmit = fields.Many2one(
        "res.partner",
        related='partner_id',
        original_spec_model='nfe.40.tenderemi'
    )

    processador_edoc = fields.Selection(
        selection_add=PROCESSADOR
    )

    # TODO CPF/CNPJ
    nfe40_xNome = fields.Char(related='partner_id.legal_name')
    nfe40_xFant = fields.Char(related='partner_id.name')
    # nfe_IE = fields.Char( TODO
    nfe40_IM = fields.Char(related='partner_id.inscr_mun')

    @api.model
    def _prepare_import_dict(self, vals, defaults={}):
        vals = super(ResCompany, self)._prepare_import_dict(vals)
        if not vals.get('name'):
            vals['name'] = vals.get('nfe40_xFant') or vals.get('nfe40_xNome')
        return vals
