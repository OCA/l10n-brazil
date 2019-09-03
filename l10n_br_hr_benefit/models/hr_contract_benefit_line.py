# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from openerp import api, fields, models, _
from openerp.exceptions import Warning, ValidationError

from datetime import date
from pybrasil.data import dias_uteis
from pybrasil.data import ultimo_dia_mes
from datetime import datetime, tzinfo, timedelta

BENEFIT_TYPE = {
    'va_vr': ['va', 'vr'],
    'saude': ['Auxílio Saúde'],
    'cesta': ['Cesta Alimentação'],
    'creche': ['Creche / Babá', 'creche', 'babá'],
    'seguro_vida': ['Seguro de Vida', 'Seguro Vida'],
}


class HrContractBenefitLine(models.Model):
    _name = b'hr.contract.benefit.line'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Prestação de contas'

    def _get_contract_id_default(self):
        if self.env.user.has_group('base.group_hr_user'):
            return False
        return self.env.user.employee_ids[0].contract_id

    @api.depends('benefit_type_id', 'amount_base')
    def _compute_benefit(self):
        for record in self:
            amount_benefit = 0
            benefit_type_id = record.benefit_type_id
            if benefit_type_id:
                if benefit_type_id.type_calc == 'fixed':
                    amount_benefit = benefit_type_id.amount

                elif benefit_type_id.type_calc == 'max':
                    if benefit_type_id.amount_max > record.amount_base:
                        amount_benefit = record.amount_base
                    else:
                        amount_benefit = \
                            benefit_type_id.amount_max

                elif benefit_type_id.type_calc == 'daily':
                    worked_days = 22

                    partner_date_start = record.contract_id.date_start
                    date_today = fields.Date.today()

                    if partner_date_start[:7] == date_today[:7]:
                        daily_admission_type = benefit_type_id.\
                            daily_admission_type
                        company_id = record.beneficiary_ids[:1].\
                            partner_id.company_id
                        if daily_admission_type == 'partial':
                            worked_days = len(dias_uteis(
                                data_inicial=partner_date_start,
                                data_final=ultimo_dia_mes(partner_date_start),
                                estado=company_id.state_id,
                                municipio=company_id.l10n_br_city_id)
                            )
                        else:
                            available_days = \
                                (ultimo_dia_mes(partner_date_start) -
                                 fields.Date.from_string(partner_date_start)).days
                            if daily_admission_type == 'rule15days' and \
                                    available_days < 15:
                                worked_days = 0
                            elif daily_admission_type == 'rulexdays' and \
                                    available_days < record.\
                                    benefit_type_id.min_worked_days:
                                worked_days = 0

                    amount_benefit = \
                        benefit_type_id.amount * worked_days

                elif benefit_type_id.type_calc == 'percent':
                    amount_benefit = \
                        record.amount_base * \
                        benefit_type_id.percent / 100

                elif benefit_type_id.type_calc == 'percent_max':

                    # FIND DEPENDENT
                    dependent_id = self.env['hr.employee.dependent']\
                        .search([('partner_id', '=', record.beneficiary_ids[:1]
                                  .partner_id.id)])

                    # CHECK IF BENEFICIARY HAS BIRTHDATE SET
                    if not dependent_id.dependent_dob:
                        record.amount_benefit = 0
                        amount_benefit = 0
                    else:

                        dob = datetime.strptime(
                            dependent_id.dependent_dob, '%Y-%m-%d')
                        now = datetime.now()
                        years = now.year - dob.year
                        months = now.month - dob.month
                        if now.day < dob.day:
                            months -= 1
                        while months < 0:
                            months += 12
                            years -= 1
                        age = '{}y{}mo'.format(years, months)

                        dependent_age_in_months = months + 12 * years

                        # CHECK IF BENEFICIARY IS YOUNGER THAN 6 MONTHS
                        if dependent_age_in_months < 6:
                          record.amount_benefit = record.amount_base
                          amount_benefit = record.amount_base

                        # CHECK IF BENEFICIARY IS OLDER THAN 71 MONTHS AND NOT INC_TRAB
                        elif dependent_age_in_months > 71 and \
                                not dependent_id.inc_trab:
                            record.amount_benefit = 0
                            amount_benefit = 0
                        elif benefit_type_id.amount_max > (
                                record.amount_base *
                                benefit_type_id.percent / 100):
                            amount_benefit = (record.amount_base *
                                benefit_type_id.percent / 100)
                        else:
                            amount_benefit = \
                                benefit_type_id.amount_max

            record.amount_benefit = amount_benefit

    state = fields.Selection(
        selection=[
            ('todo', 'Aguardando Comprovante'),
            ('waiting', 'Enviado para apuração'),
            ('validated', 'Apurado'),
            ('exception', 'Negado'),
            ('cancel', 'Cancelado'),
            ('payslip_deleted', 'Holerite Cancelado'),
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
        ondelete='restrict',
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
        stored=True,
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
        ondelete='set null',
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

        self._generate_calculated_values()

    def _check_benefit_type(self, benefit_key):
        return BENEFIT_TYPE.get(benefit_key) and \
               any([benef.lower() in self.name.lower() for benef in
                    BENEFIT_TYPE.get(benefit_key)])

    @api.multi
    def _generate_calculated_values(self):
        self.ensure_one()

        if self._check_benefit_type('va_vr'):
            self._generate_calculated_values_va_vr()

        elif self._check_benefit_type('saude'):
            self._generate_calculated_values_saude()

        elif self._check_benefit_type('cesta'):
            self._generate_calculated_values_cesta()

        elif self._check_benefit_type('creche'):
            self._generate_calculated_values_creche()

        elif self._check_benefit_type('seguro_vida'):
            self._generate_calculated_values_seguro_vida()

    def _generate_calculated_values_va_vr(self):
        self.deduction_amount = 0.01 * self.amount_benefit
        self.deduction_percentual = 100
        self.deduction_quantity = 1

        self.income_amount = self.amount_benefit
        self.income_percentual = 100
        self.income_quantity = 1

    def _generate_calculated_values_saude(self):
        self.income_amount = self.amount_benefit
        self.income_percentual = 100
        self.income_quantity = 1

    def _generate_calculated_values_cesta(self):
        self.income_amount = self.amount_benefit
        self.income_percentual = 100
        self.income_quantity = 1

        # 13ª Cesta
        if self.benefit_type_id.extra_income and \
                date.today().month == \
                int(self.benefit_type_id.extra_income_month):
            self.income_quantity += 1

    def _generate_calculated_values_creche(self):
        dependent_id = self.env['hr.employee.dependent'] \
            .search([('partner_id', '=', self.beneficiary_ids[0]
                      .partner_id.id)])

        if not dependent_id:
            self.exception_message = 'Reijeitado pois o beneficiário não' \
                                     ' está mais na idade aceita para ' \
                                     'este benefício. O benefício foi ' \
                                     'cancelado.'
            self.state = 'exception'
            self.beneficiary_ids[:1].button_cancel()
        # CHECK IF BENEFICIARY HAS BIRTHDATE SET
        elif dependent_id.dependent_dob:
            dob = datetime.strptime(
                dependent_id.dependent_dob, '%Y-%m-%d')
            now = datetime.now()
            years = now.year - dob.year
            months = now.month - dob.month
            if now.day < dob.day:
                months -= 1
            while months < 0:
                months += 12
                years -= 1
            age = '{}y{}mo'.format(years, months)

            dependent_age_in_months = months + 12 * years

            if dependent_age_in_months > 71 and \
                 not dependent_id.inc_trab:
                self.exception_message = 'Reijeitado pois o beneficiário não' \
                                         ' está mais na idade aceita para ' \
                                         'este benefício. O benefício foi ' \
                                         'cancelado.'
                self.state = 'exception'
                self.beneficiary_ids[:1].button_cancel()
            else:
                self.income_amount = self.amount_benefit
                self.income_percentual = 100
                self.income_quantity = 1
        else:
            self.exception_message = 'Reijeitado pois o beneficiário não' \
                                     ' possui uma data de nascimento ' \
                                     'cadastrada. O benefício foi ' \
                                     'cancelado.'
            self.state = 'exception'
            self.beneficiary_ids[:1].button_cancel()

    def _generate_calculated_values_seguro_vida(self):
        self.income_amount = self.amount_benefit
        self.income_percentual = 100
        self.income_quantity = 1

    def check_approve_limit(self):
        today = datetime.today()
        create_date = fields.Datetime.from_string(
            self.create_date)
        days_since_created = (today - create_date).days

        if self.benefit_type_id.line_days_approval_limit and \
                days_since_created > \
                self.benefit_type_id.line_days_approval_limit:
            # CHECK PERMISSION
            if not self.env.user.has_group('base.group_hr_manager'):
                return False
        return True

    @api.multi
    def button_send_receipt(self):
        for record in self:
            if not record.check_approve_limit():
                raise Warning(_("""\nSomente membros do RH podem aprovar 
                benefícios após a data limite de confirmação"""))
            if (record.benefit_type_id.line_need_approval_file and
                    not record.attachment_ids):
                raise Warning(_("""\nPara enviar para aprovação é necessário
                 anexar o comprovante"""))

            if record.benefit_type_id.line_need_clearance and \
                    not record.amount_base:
                raise Warning(
                    _('Para enviar para aprovação é '
                      'necessário anexar ao menos um '
                      'comprovante e preencher o '
                      'valor comprovado'))

            record._get_rules()
            if record.state not in ['exception']:
                if not record.benefit_type_id.line_need_approval:
                    record.state = 'validated'
                else:
                    record.state = 'waiting'

    @api.multi
    def button_approve_receipt(self):
        for record in self:
            if not record.check_approve_limit():
                raise Warning(_("""\nSomente membros do RH podem aprovar 
                benefícios após a data limite de confirmação"""))
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
