# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from openerp import api, fields, models, _
from openerp.exceptions import Warning


class HrPayslip(models.Model):

    _inherit = b'hr.payslip'

    def get_contract_specific_rubrics(self, contract_id, rule_ids):
        applied_specific_rule = super(
            HrPayslip, self).get_contract_specific_rubrics(
                contract_id, rule_ids
        )

        return applied_specific_rule

    @api.model
    def get_specific_rubric_value(
            self, rubrica_id, medias_obj=False,
            rubricas_especificas_calculadas=False, references=False):

        result = super(HrPayslip, self).get_specific_rubric_value(
            rubrica_id,
            medias_obj,
            rubricas_especificas_calculadas,
            references
        )

        return result
