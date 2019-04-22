# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.addons.l10n_br_hr_payroll.models.hr_payslip import (
    MES_DO_ANO,
)
from openerp.exceptions import ValidationError


class WizardL10n_br_hr_payrollAnalytic_report(models.TransientModel):

    _name = 'wizard.l10n_br_hr_payroll.analytic_report'

    tipo_de_folha = fields.Selection(
        selection=(("('normal', 'rescisao', 'rescisao_complementar')", "Folha Normal"),
                   ("('ferias')", "Férias"),
                   ("('decimo_terceiro')", "Décimo Terceiro (13º)"),
                   ("('provisao_decimo_terceiro')", "Provisão 13º Salário"),
                   ("('provisao_ferias')", "Provisão de Férias"),
        ),
        string=u'Tipo de folha',
        default="('normal', 'rescisao', 'rescisao_complementar')",
    )

    mes_do_ano = fields.Selection(
        selection=MES_DO_ANO,
        string=u'Mês',
        default=fields.Date.from_string(fields.Date.today()).month
    )

    ano = fields.Integer(
        string=u'Ano',
        default=fields.Date.from_string(fields.Date.today()).year
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string=u'Empresa',
        default=lambda self: self.env.user.company_id.id or '',
    )

    @api.multi
    def doit(self):
        busca = [
            ('company_id', '=', self.company_id.id),
            ('mes_do_ano', '=', self.mes_do_ano),
            ('ano', '=', self.ano),
            ('state', 'in', ['done', 'verify']),
        ]
        if self.tipo_de_folha == "('normal', 'rescisao', 'rescisao_complementar')":
            busca.append(('tipo_de_folha', 'in', eval(self.tipo_de_folha)))
        else:
            busca.append(('tipo_de_folha', '=', eval(self.tipo_de_folha)))
        payslip_ids = self.env['hr.payslip'].search(busca)

        if not payslip_ids:
            raise ValidationError(
                _('Não foi encontrado lote de holerite '
                  'dentro do período selecionado.'))

        else:
            return self.env['report'].get_action(
                self, "l10n_br_hr_payroll_report.report_analyticreport")
