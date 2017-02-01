# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError

STATES = [('draft', 'Rascunho'),
          ('applied', 'Aplicada')]


class HrContractChangeReason(models.Model):

    _name = 'l10n_br_hr.contract.change_reason'
    _description = u"Motivo de alteração contratual"

    name = fields.Char(u"Motivo")


class HrContractChange(models.Model):

    _name = 'l10n_br_hr.contract.change'
    _description = u"Alteração contratual"
    _inherit = 'hr.contract'

    def _get_default_type(self):
        change_type = self._context.get('change_type', False)
        if change_type:
            return change_type
        else:
            raise UserError(u'Sem tipo de alteração definido!')

    @api.depends('contract_id', 'change_history_ids')
    def _get_change_history(self):
        change_type = self._context.get('change_type', False)
        full_history = self.search(
            [('contract_id', '=', self.contract_id.id),
             ('change_type', '=', change_type),
             ('state', '=', 'applied')])
        self.change_history_ids = full_history

    contract_id = fields.Many2one(
        'hr.contract',
        string="Contrato"
    )
    change_type = fields.Selection(
        selection=[
            ('remuneracao', u'Remuneração'),
            ('jornada', u'Jornada'),
            ('cargo-atividade', u'Cargo/Atividade'),
            ('filiacao-sindical', u'Filiação Sindical'),
            ('lotacao-local', u'Lotação/Local de trabalho'),
        ],
        string=u"Tipo de alteração contratual",
        default=_get_default_type
    )
    change_reason_id = fields.Many2one(
        comodel_name='l10n_br_hr.contract.change_reason',
        string=u"Motivo", required=True,
    )
    change_date = fields.Date(u'Data da alteração')
    change_history_ids = fields.Many2many(
        comodel_name='l10n_br_hr.contract.change',
        inverse_name='contract_id',
        string=u"Histórico",
        compute=_get_change_history,
    )
    name = fields.Char(string='Contract Reference', required=False)
    employee_id = fields.Many2one(string='Employee',
                                  comodel_name='hr.employee',
                                  required=False)
    type_id = fields.Many2one(string='Contract Type',
                              comodel_name='hr.contract.type',
                              required=False)
    state = fields.Selection(string=u'Alteração aplicada', selection=STATES,
                             default='draft')

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        contract = self.contract_id
        self.change_date = fields.datetime.now()
        self.notes = contract.notes
        if self.change_type == 'remuneracao':
            self.wage = contract.wage
            self.salary_unit = contract.salary_unit
            self.struct_id = contract.struct_id
        elif self.change_type == 'jornada':
            self.working_hours = contract.working_hours
            self.schedule_pay = contract.schedule_pay
            self.monthly_hours = contract.monthly_hours
            self.weekly_hours = contract.weekly_hours
        elif self.change_type == 'cargo-atividade':
            self.job_id = contract.job_id
            self.type_id = contract.type_id
            self.admission_type_id = contract.admission_type_id
            self.labor_bond_type_id = contract.labor_bond_type_id
            self.labor_regime_id = contract.labor_regime_id
        elif self.change_type == 'filiacao-sindical':
            self.union = contract.union
            self.union_cnpj = contract.union_cnpj
            self.union_entity_code = contract.union_entity_code
            self.discount_union_contribution = \
                contract.discount_union_contribution
            self.month_base_date = contract.month_base_date

    @api.multi
    def apply_contract_changes(self):
        for change in self:
            contract = change.contract_id
            if self.change_type == 'remuneracao':
                contract.wage = self.wage
                contract.salary_unit = self.salary_unit
                contract.struct_id = self.struct_id
            elif self.change_type == 'jornada':
                contract.working_hours = self.working_hours
                contract.schedule_pay = self.schedule_pay
                contract.monthly_hours = self.monthly_hours
                contract.weekly_hours = self.weekly_hours
            elif self.change_type == 'cargo-atividade':
                contract.job_id = self.job_id
                contract.type_id = self.type_id
                contract.admission_type_id = self.admission_type_id
                contract.labor_bond_type_id = self.labor_bond_type_id
                contract.labor_regime_id = self.labor_regime_id
            elif self.change_type == 'filiacao-sindical':
                contract.union = self.union
                contract.union_cnpj = self.union_cnpj
                contract.union_entity_code = self.union_entity_code
                contract.discount_union_contribution = \
                    self.discount_union_contribution
                contract.month_base_date = self.month_base_date
            self.state = 'applied'
