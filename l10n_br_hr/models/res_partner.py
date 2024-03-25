# (c) 2019 KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_employee_dependent = fields.Boolean(string="Is an employee dependent")

    def create_depentent(self):
        for record in self.with_context(active_test=False):
            self.env["hr.employee.dependent"].create({"partner_id": record.id})
        return True

    @api.model
    def create(self, vals):
        if "depentent_employee_id" in self.env.context:
            employee_id = self.env["hr.employee"].browse(
                self.env.context.get("depentent_employee_id")
            )
            vals["parent_id"] = employee_id.address_home_id.id

        partner = super().create(vals)

        if "create_depentent" not in self._context and vals.get(
            "is_employee_dependent", False
        ):
            partner.with_context(create_depentent=True).create_depentent()
        return partner

    def write(self, vals):
        res = super().write(vals)
        if "is_employee_dependent" in vals and not self.is_employee_dependent:
            self.create_depentent()
        return res
