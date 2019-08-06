# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from openerp import api, fields, models


class HrPayslip(models.Model):

    _inherit = b'hr.payslip'

    benefit_line_ids = fields.One2many(
        comodel_name='hr.contract.benefit.line',
        inverse_name='hr_payslip_id',
    )

    def get_contract_specific_rubrics(self, rule_ids, DIAS_A_MAIOR):
        """

        :param rule_ids:
        :param DIAS_A_MAIOR:
        :return:
        """

        applied_specific_rule = super(
            HrPayslip, self).get_contract_specific_rubrics(
                rule_ids, DIAS_A_MAIOR
        )

        # Busca beneficios ativos do contrato

        valid_benefit_ids = \
            self.contract_id.benefit_ids.filtered(
                lambda r: r.state == 'validated'
            )

        if valid_benefit_ids:
            #
            # Verificar a existência de benefícios apurados
            #
            valid_benefit_line_ids = \
                valid_benefit_ids.mapped(
                    'line_ids'
                ).map_valid_benefit_line_to_payslip(self.id)

            if valid_benefit_line_ids:
                valid_benefit_line_ids.write({'hr_payslip_id': self.id})
                # TODO: Remover caso a folha seja cancelada ou
                #  outro estágio pertinente.

        return applied_specific_rule

    @api.model
    def get_specific_rubric_value(
            self, rubrica_id, references=False):

        result = super(HrPayslip, self).get_specific_rubric_value(
            rubrica_id,
            references
        )

        return result
