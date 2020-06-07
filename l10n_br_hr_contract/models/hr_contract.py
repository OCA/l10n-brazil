# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"
    _order = "employee_id"

    admission_type_id = fields.Many2one(
        string="Admission type",
        comodel_name="hr.contract.admission.type"
    )

    labor_bond_type_id = fields.Many2one(
        string="Labor bond type", comodel_name="hr.contract.labor.bond.type"
    )

    labor_regime_id = fields.Many2one(
        string="Labor regime",
        comodel_name="hr.contract.labor.regime",
        help="e-Social: S2200/S2300 - tpRegTrab",
    )

    welfare_policy = fields.Selection(
        string="Welfare policy",
        selection=[
            ("rgps", u"Regime Geral da Previdência Social"),
            ("rpps", u"Regime Próprio da Previdência Social"),
            ("rpse", "Regime de Previdência Social no Exterior"),
        ],
        help="e-Social: S2200/S2300 - tpRegPrev",
    )

    salary_unit = fields.Many2one(
        string="Salary Unity", comodel_name="hr.contract.salary.unit"
    )

    weekly_hours = fields.Float(string="Weekly hours")

    monthly_hours = fields.Float(string="Monthly hours")

    partner_union = fields.Many2one(
        string="Sindicato",
        comodel_name="res.partner",
        domain=[("union_entity_code", "!=", False)],
        help="Sindicato é um partner que tem código de sindicato "
             "(union_entity_code) definido.",
    )

    union_name = fields.Char(
        string="Union", related="partner_union.name", readonly=True
    )

    union_cnpj = fields.Char(
        string="Union CNPJ",
        related="partner_union.cnpj_cpf",
        readonly=True
    )

    union_entity_code = fields.Char(
        string="Union entity code",
        related="partner_union.union_entity_code",
        readonly=True,
    )

    discount_union_contribution = fields.Boolean(
        string="Discount union contribution in admission"
    )

    resignation_date = fields.Date(string="Resignation date")

    resignation_cause_id = fields.Many2one(
        comodel_name="hr.contract.resignation.cause",
        string="Resignation cause"
    )

    notice_of_termination_id = fields.Many2one(
        string="Notice of termination type",
        comodel_name="hr.contract.notice.termination",
    )

    notice_of_termination_date = fields.Date(
        string="Notice of termination date",
    )

    by_death = fields.Char(
        string="By death",
        help="Death certificate/Process/Beneficiary"
    )

    resignation_code = fields.Char(
        related="resignation_cause_id.code",
        invisible=True,
    )

    @api.onchange("job_id")
    def set_job_in_employee(self):
        """
        Definir o campo função no funcionário.
        Caso o funcionário venha a ter um segundo contrato, popular o campo
        no employee. Caso tenha uma alteração contratual, popular o campo
        """
        for record in self:
            if record.employee_id:
                if not record.job_id == record.employee_id.job_id:
                    record.employee_id.with_context(
                        alteracaocontratual=True).write(
                        {"job_id": record.job_id.id}
                    )

    @api.model
    def create(self, vals):
        res = super(HrContract, self).create(vals)
        if vals.get("department_id") and vals.get("employee_id"):
            employee = self.env["hr.employee"].browse(vals.get("employee_id"))
            employee.department_id = vals.get("department_id")
        return res
