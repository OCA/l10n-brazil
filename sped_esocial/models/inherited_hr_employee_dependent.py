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
