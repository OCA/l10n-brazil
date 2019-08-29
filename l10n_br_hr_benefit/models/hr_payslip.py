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

    def get_contract_specific_rubrics(
            self, applied_specific_rule, rule_ids, DIAS_A_MAIOR):
        """

        :param rule_ids:
        :param DIAS_A_MAIOR:
        :return:
        """

        super(HrPayslip, self).get_contract_specific_rubrics(
                applied_specific_rule, rule_ids, DIAS_A_MAIOR
        )

        # Busca Benefícios ativos do contrato

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

        #
        # Salvo os benfícios vamos aplicar os benefícios na lista
        # applied_specific_rule
        #
        for benefit_line_id in self.benefit_line_ids:

            if benefit_line_id.income_rule_id:
                rule_ids.append(
                    (benefit_line_id.benefit_type_id.income_rule_id.id,
                     benefit_line_id.id)
                )
                specific = {
                    'type': 'benefit',
                    'rule_id': benefit_line_id,
                    # 'beneficiario_id': benefit_line_id.partner_id
                    'value': (
                        benefit_line_id.income_quantity *
                        benefit_line_id.income_percentual / 100 *
                        benefit_line_id.income_amount,

                        benefit_line_id.income_quantity,

                        benefit_line_id.income_percentual,
                        benefit_line_id.period_id.name or None,
                    )
                }
                applied_specific_rule[
                    benefit_line_id.benefit_type_id.income_rule_id.id
                ].append(specific)

            if benefit_line_id.deduction_rule_id:
                rule_ids.append(
                    (benefit_line_id.benefit_type_id.deduction_rule_id.id,
                     benefit_line_id.id)
                )
                specific = {
                    'type': 'benefit',
                    'rule_id': benefit_line_id,
                    # 'beneficiario_id': benefit_line_id.partner_id
                    'value': (
                        benefit_line_id.deduction_quantity *
                        benefit_line_id.deduction_percentual / 100 *
                        benefit_line_id.deduction_amount,

                        benefit_line_id.deduction_quantity,

                        benefit_line_id.deduction_percentual,
                        benefit_line_id.period_id.name or None,
                    )
                }
                applied_specific_rule[
                    benefit_line_id.benefit_type_id.deduction_rule_id.id
                ].append(specific)
