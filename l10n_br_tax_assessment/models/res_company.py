# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    tax_assessment_start = fields.Date(
        string="Início da apuração pelo sistema",
        help="Primeiro dia do primeiro mês em que o sistema apura os impostos desta "
        "empresa (ICMS, IPI, PIS e COFINS). A partir dele a apuração leva o saldo "
        "credor de um mês para o seguinte e exige a apuração lançada dos meses "
        "com movimento; os meses anteriores não são exigidos. O saldo credor que "
        "vem de antes dessa data é informado como saldo inicial (menu de "
        "apuração). Em base existente, defina-o antes de apurar; em empresa sem "
        "movimento anterior, é o mês da primeira apuração.",
    )

    @api.constrains("tax_assessment_start")
    def _check_tax_assessment_start(self):
        for company in self:
            if company.tax_assessment_start and company.tax_assessment_start.day != 1:
                raise ValidationError(
                    _("O início da apuração pelo sistema é o primeiro dia de um mês.")
                )
