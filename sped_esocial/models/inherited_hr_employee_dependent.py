# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import ValidationError


class HrEmployeeDependent(models.Model):
    _inherit = 'hr.employee.dependent'

    # Cria campos dep_sf e inc_trab (Dependentes) que não existe na l10n_br
    dep_sf = fields.Boolean(
        string='Salário Família?',
    )
    inc_trab = fields.Boolean(
        string='Incapacidade Física ou Mental?',
    )
    precisa_cpf = fields.Boolean(
        string='Precisa passar cpf?',
        compute='_precisa_preencher_cpf'
    )

    @api.multi
    @api.depends('dependent_dob', 'dependent_verification')
    def _precisa_preencher_cpf(self):
        for record in self:
            precisa_cpf = False
            if record.dependent_verification:
                data_atual = fields.Datetime.from_string(fields.Datetime.now())
                data_aniversario = fields.Datetime.from_string(
                    record.dependent_dob)
                if (data_atual - data_aniversario).days / 365 >= 8:
                    precisa_cpf = True
            record.precisa_cpf = precisa_cpf
