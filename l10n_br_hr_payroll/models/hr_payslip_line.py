# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models


class HrPayslipeLine(models.Model):
    _inherit = "hr.payslip.line"

    @api.model
    def _valor_provento(self):
        for record in self:
            if record.salary_rule_id.category_id.code == "PROVENTO":
                record.valor_provento = record.total
            else:
                record.valor_provento = 0.00

    @api.model
    def _valor_deducao(self):
        for record in self:
            if record.salary_rule_id.category_id.code in ["DEDUCAO"] \
                    or record.salary_rule_id.code == "INSS" \
                    or record.salary_rule_id.code == "IRPF":
                record.valor_deducao = record.total
            else:
                record.valor_deducao = 0.00

    valor_provento = fields.Float(
        string="Provento",
        compute=_valor_provento,
        default=0.00,
    )
    valor_deducao = fields.Float(
        string="Dedução",
        compute=_valor_deducao,
        default=0.00,
    )
