# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from ..constants.nfse import (NFSE_ENVIRONMENT_DEFAULT, NFSE_ENVIRONMENTS)

PROCESSADOR = 'erpbrasil_edoc'


class ResCompany(models.Model):

    _inherit = 'res.company'
    processador_edoc = fields.Selection(
        selection_add=[(PROCESSADOR, 'erpbrasil.edoc')]
    )
    provedor_nfse = fields.Selection(
        selection=[
            ('ginfes', 'Ginfes'),
            ('dsf', 'DSF / Iss Digital'),
        ],
        default='ginfes',
    )
    cultural_encourager = fields.Boolean(
        string='Cultural Encourager',
        default=False,
    )
    nfse_environment = fields.Selection(
        selection=NFSE_ENVIRONMENTS,
        string="NFSe Environment",
        default=NFSE_ENVIRONMENT_DEFAULT,
    )

    nfse_city_logo = fields.Binary(
        string='NFSe City Logo',
    )

    def prepare_company_servico(self):
        return {
            'codigo_municipio': int('%s%s' % (
                self.partner_id.state_id.ibge_code,
                self.partner_id.city_id.ibge_code
            )) or None,
        }
