# -*- coding: utf-8 -*-
# Copyright 2018 ABGF - Hendrix Costa <hendrix.costa@abgf.gov..br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class HrPayslipAutonomo(models.Model):
    _inherit = 'hr.payslip.autonomo'

    sefip_id = fields.Many2one(
        comodel_name='l10n_br.hr.sefip',
        string='Sefip',
    )
