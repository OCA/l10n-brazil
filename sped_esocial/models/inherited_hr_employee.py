# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Cria campos pais_nac_id e pais_nascto_id para substituir o place_of_birth (que é texto)
    pais_nascto_id = fields.Many2one(
        string='País de Nascimento',
        comodel_name='sped.pais',
    )
    pais_nac_id = fields.Many2one(
        string='Nacionalidade',
        comodel_name='sped.pais',
    )

    # Dados que faltam em l10n_br_hr
    cnh_dt_exped = fields.Date(
        string='Data de Emissão',
    )
    cnh_uf = fields.Many2one(
        string='UF',
        comodel_name='res.country.state',
    )
    cnh_dt_pri_hab = fields.Date(
        string='Data da 1ª Hab.',
    )
    )
