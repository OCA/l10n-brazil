# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from openerp import api, fields, models, _
from openerp.exceptions import Warning


class HrContractBenefitLine(models.Model):
    _name = b'hr.contract.benefit.line'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Prestação de contas'

    def _get_contract_id_default(self):
        if self.env.user.has_group('base.group_hr_user'):
            return False
        return self.env.user.employee_ids[0].contract_id

    @api.depends('benefit_type_id','amount_base')
    def _compute_benefit(self):
        for record in self:
            amount_benefit = 0
            if record.benefit_type_id:
                if record.benefit_type_id.type_calc == 'fixed':
                    amount_benefit = record.benefit_type_id.amount

                elif record.benefit_type_id.type_calc == 'max':
                    if record.benefit_type_id.amount_max > record.amount_base:
                        amount_benefit = record.amount_base
                    else:
                        amount_benefit = \
                            record.benefit_type_id.amount_max

                elif record.benefit_type_id.type_calc == 'daily':
                    # TODO: Buscar os dias trabalhados
                    worked_days = 22

                    if worked_days > record.benefit_type_id.min_worked_days:
                        # Verificar se é o mês que foi admitido
                        # Se for admitido e os dias trabalhados forem
                        # menor que a referencia. Não pagar:
                        amount_benefit = \
                            record.benefit_type_id.amount * worked_days

                elif record.benefit_type_id.type_calc == 'percent':
                    amount_benefit = \
                        record.amount_base * \
                        record.benefit_type_id.percent / 100

                elif record.benefit_type_id.type_calc == 'percent_max':
                    # TODO: Verificar se o filho é menor que 6 meses
                    #  Benefício mensal de reembolso de 50% do valor gasto,
                    #  limitado ao teto, salvo exceções (idade até 6 meses).

                    if record.benefit_type_id.amount_max > (
                            record.amount_base *
                            record.benefit_type_id.percent / 100):
                        amount_benefit = (record.amount_base *
                            record.benefit_type_id.percent / 100)
                    else:
                        amount_benefit = \
                            record.benefit_type_id.amount_max

            record.amount_benefit = amount_benefit

    state = fields.Selection(
        selection=[
            ('todo', 'Aguardando Comprovante'),
            ('waiting', 'Enviado para apuração'),
            ('validated', 'Apurado'),
            ('exception', 'Negado'),
            ('cancel', 'Cancelado'),
        ],
        string='Situação',
        index=True,
        default='todo',
        track_visibility='onchange'
    )
    name = fields.Char(
        compute='_compute_benefit_line_name'
    )
    benefit_type_id = fields.Many2one(
        comodel_name='hr.benefit.type',
        required=True,
        readonly=True,
        string='Tipo Benefício',
        track_visibility='onchange'
    )
    contract_id = fields.Many2one(
        comodel_name='hr.contract',
        required=True,
        readonly=True,
        index=True,
        string='Contrato',
        track_visibility='onchange',
        default=_get_contract_id_default
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        related='contract_id.employee_id',
        readonly=True,
        index=True,
        store=True,
        string='Colaborador',
    )
    period_id = fields.Many2one(
        comodel_name='account.period',
        string='Competência',
        readonly=True,
        index=True,
        track_visibility='onchange'
    )
    date_start = fields.Date(
        string='Início de Vigência',
        index=True,
        readonly=True,
        track_visibility='onchange'
    )
    date_stop = fields.Date(
        string='Fim de Vigência',
        index=True,
        readonly=True,
        track_visibility='onchange'
    )
    beneficiary_ids = fields.Many2many(
        comodel_name='hr.contract.benefit',
        string='Beneficiários',
        column1='hr_contract_benefit_line_id',
        column2='hr_contract_benefit_id',
        relation='contract_benefitiary_rel',
        track_visibility='onchange',
        readonly=True,
    )
    amount_base = fields.Float(
        string='Valor Comprovado',
        index=True,
        track_visibility='onchange',
        states={'todo': [('readonly', False)]},
        readonly=True,
    )
    amount_benefit = fields.Float(
        string='Valor Apurado',
        index=True,
        track_visibility='onchange',
        # states={'todo': [('readonly', False)]},
        readonly=True,
        compute='_compute_benefit',
    )
    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='hr_contract_benefit_line_att_rel',
        column1='benefit_line_id',
        column2='attachment_id',
        string='Anexos',
        track_visibility='onchange',
        states={'todo': [('readonly', False)]},
        readonly=True,
    )
    is_payroll_processed = fields.Boolean(
        string='Processado',
        readonly=True,
        track_visibility='onchange'
    )
    exception_message = fields.Text(
        string='Motivo da exceção na apuração',
        readonly=True,
        track_visibility='onchange'
    )
    income_rule_id = fields.Many2one(
        comodel_name="hr.salary.rule",
        string=u"Provento (+)",
    )
    deduction_rule_id = fields.Many2one(
        comodel_name="hr.salary.rule",
        string=u"Dedução (-)",
    )
    hr_payslip_id = fields.Many2one(
        comodel_name="hr.payslip",
        string="Folha de pagamento",
        readonly=True,
    )
    income_amount = fields.Float(
        string='Valor apurado',
    )
    income_percentual = fields.Float(
        string='Percentual apurado',
    )
    income_quantity = fields.Float(
        string='Quantidade apurada',
    )
    deduction_amount = fields.Float(
        string='Valor apurado',
    )
    deduction_percentual = fields.Float(
        string='Percentual apurado',
    )
    deduction_quantity = fields.Float(
        string='Quantidade apurada',
    )

    @api.model
    def map_valid_benefit_line_to_payslip(self, hr_payslip_id):
        """ Dado um conjunto de Benefícios apurados, mapeia quais deles podem
         compor uma folha de pagamento.

        OBS: Não deve ser feita nenhuma validação neste método, apenas na
        aprovação do registro e se ele não compoe nenhuma outra folha.

        :param hr_payslip_id:
        :return:
        """
        valid = self.env['hr.contract.benefit.line']
        for record in self:
            if record.state == 'validated':
                if not record.hr_payslip_id or (
                        record.hr_payslip_id.id == hr_payslip_id and not
                        record.is_payroll_processed
                ):
                    valid |= record

        return valid

    @api.onchange('hr_payslip_id')
    def onchange_payroll_processed(self):
        for record in self:
            if record.hr_payslip_id:
                record.is_payroll_processed = True
            else:
                record.is_payroll_processed = False

    @api.multi
    @api.depends('benefit_type_id', 'date_start', 'date_stop')
    def _compute_benefit_line_name(self):
        for record in self:
            if (not record.employee_id or
                    not record.benefit_type_id or
                    not record.period_id):
                record.name = 'Novo'
                continue

            record.name = ("%s - %s de %s" %
                           (record.employee_id.name,
                            record.benefit_type_id.name,
                            record.period_id.name))

    @api.multi
    def _get_rules(self):
        self.ensure_one()
        self.income_rule_id = self.benefit_type_id.income_rule_id
        self.deduction_rule_id = self.benefit_type_id.deduction_rule_id

    @api.multi
    def button_send_receipt(self):
        for record in self:
            if (record.benefit_type_id.line_need_approval_file and
                    not record.attachment_ids):
                raise Warning(_("""\nPara enviar para aprovação é necessário
                 anexar o comprovante"""))

            if not record.amount_base:
                raise Warning(
                    _('Para enviar para aprovação é '
                      'necessário anexar ao menos um '
                      'comprovante e preencher o '
                      'valor comprovado'))

            if not record.benefit_type_id.line_need_approval:
                record.state = 'validated'
            else:
                record.state = 'waiting'
                record._get_rules()

    @api.multi
    def button_approve_receipt(self):
        for record in self:
            if record.benefit_type_id.line_need_approval and not \
                    self.env.user.has_group('base.group_hr_user'):
                raise Warning(
                    _("\nFavor solicitar a aprovação de um gerente")
                )

            record.state = 'validated'
            record._get_rules()

    @api.multi
    def button_exception_receipt(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.benefit.exception.cause',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': False,
            'target': 'new',
        }

    @api.multi
    def button_back_todo(self):
        for record in self:
            if record.state in 'exception':
                record.state = 'todo'
