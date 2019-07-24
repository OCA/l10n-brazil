# -*- coding: utf-8 -*-
# (c) 2019 Kmee - Diego Paradeda <diego.paradeda@kmee.com.br>
# (c) 2019 Kmee - Hugo Borges <hugo.borges@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models

STATE_SELECTION = [
    ('draft', 'Inicial'),
    ('done', 'Final')
]


class HrEmployeeTimeSheetWizard(models.TransientModel):
    _name = 'hr.employee.timesheet.wizard'

    state = fields.Selection(
        string='Estado',
        selection=STATE_SELECTION,
        default='draft',
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.user.company_id.id,
    )

    contract_ids = fields.Many2many(
        string='Contratos',
        comodel_name='hr.contract',
    )

    @api.multi
    def action_process_hr_contracts(self):
        self.ensure_one()

        today = fields.Date.context_today(self)
        hr_contract_ids = self.env['hr.contract'].search(
            [
                ('employee_id.company_id', '=', self.company_id.id),
                ('compor_quadro_horario', '=', True),
                '|',
                ('date_end', '=', False),
                ('date_end', '>=', today),
            ])

        call_result = {
            'contract_ids': [
                (6, 0, hr_contract_ids.ids)] or None,
            'state': 'done'
        }
        self.write(call_result)

        return self.return_action_wizard()

    @api.multi
    def action_previous_hr_contracts(self):
        self.ensure_one()

        call_result = {
            'contract_ids': None,
            'state': 'draft'
        }
        self.write(call_result)

        return self.return_action_wizard()

    def return_action_wizard(self):
        view_rec = self.env['ir.model.data'].get_object_reference(
            'sped_esocial',
            'hr_employee_timesheet_wizard_form')
        view_id = view_rec and view_rec[1] or False

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [view_id],
            'res_model': 'hr.employee.timesheet.wizard',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': self.env.context,
        }

    @api.multi
    def action_print_hr_contracts_py3o(self):
        return self.env['report'].get_action(
            self,
            "sped_esocial.report_employees_timesheet"
        )
