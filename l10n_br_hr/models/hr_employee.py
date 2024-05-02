# (c) 2014 Kmee - Rafael da Silva Lima <rafael.lima@kmee.com.br>
# (c) 2014 Kmee - Matheus Felix <matheus.felix@kmee.com.br>
# (c) 2016 KMEE Informática - Daniel Sadamo <daniel.sadamo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from erpbrasil.base.fiscal import cnpj_cpf, pis

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.l10n_br_base.tools import check_cnpj_cpf


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _default_country(self):
        return self.env["res.country"].search([("code", "=", "BR")])

    cnpj_cpf = fields.Char(string="CNPJ/CPF", groups="hr.group_hr_user")

    birth_city_id = fields.Many2one(comodel_name="res.city", groups="hr.group_hr_user")

    pis_pasep = fields.Char(string="PIS/PASEP", groups="hr.group_hr_user")

    pis_pasep_date = fields.Date(
        string="PIS/PASEP emission date", groups="hr.group_hr_user"
    )

    ctps = fields.Char(string="CTPS", help="CTPS number", groups="hr.group_hr_user")

    ctps_series = fields.Char(string="CTPS series", groups="hr.group_hr_user")

    ctps_date = fields.Date(string="CTPS emission date", groups="hr.group_hr_user")

    ctps_uf_id = fields.Many2one(
        string="CTPS district",
        comodel_name="res.country.state",
        groups="hr.group_hr_user",
    )

    creservist = fields.Char(
        string="Military service status certificate", groups="hr.group_hr_user"
    )

    cresv_categ = fields.Selection(
        string="Military service status category",
        selection=[
            ("1", "First Category"),
            ("2", "Second Category"),
            ("3", "Third Category"),
        ],
        default="3",
        groups="hr.group_hr_user",
    )

    rg = fields.Char(
        string="RG",
        store=True,
        related="address_home_id.inscr_est",
        help="National ID number",
        groups="hr.group_hr_user",
    )

    cpf = fields.Char(
        string="CPF",
        store=True,
        related="address_home_id.cnpj_cpf",
        readonly=False,
        groups="hr.group_hr_user",
    )

    organ_exp = fields.Char(string="Dispatcher organ", groups="hr.group_hr_user")

    rg_emission = fields.Date(string="Emission date", groups="hr.group_hr_user")

    voter_title = fields.Char(groups="hr.group_hr_user")

    voter_zone = fields.Char(groups="hr.group_hr_user")

    voter_section = fields.Char(groups="hr.group_hr_user")

    driver_license = fields.Char(
        string="Driver license number", groups="hr.group_hr_user"
    )

    driver_categ = fields.Char(
        string="Driver license category", groups="hr.group_hr_user"
    )

    father_name = fields.Char(groups="hr.group_hr_user")

    mother_name = fields.Char(groups="hr.group_hr_user")

    expiration_date = fields.Date(groups="hr.group_hr_user")

    ethnicity = fields.Many2one(comodel_name="hr.ethnicity", groups="hr.group_hr_user")

    blood_type = fields.Selection(
        selection=[
            ("a+", "A+"),
            ("a-", "A-"),
            ("b+", "B+"),
            ("b-", "B-"),
            ("o+", "O+"),
            ("o-", "O-"),
            ("ab+", "AB+"),
            ("ab-", "AB-"),
        ],
        groups="hr.group_hr_user",
    )

    deficiency_id = fields.Many2one(
        string="Deficiency",
        comodel_name="hr.deficiency",
        tracking=True,
        groups="hr.group_hr_user",
    )

    deficiency_description = fields.Char(groups="hr.group_hr_user")

    identity_type_id = fields.Many2one(
        string="ID type", comodel_name="hr.identity.type", groups="hr.group_hr_user"
    )

    identity_validity = fields.Date(
        string="ID expiration date", groups="hr.group_hr_user"
    )

    identity_uf_id = fields.Many2one(
        string="ID expedition district",
        comodel_name="res.country.state",
        groups="hr.group_hr_user",
    )

    identity_city_id = fields.Many2one(
        string="ID expedition city",
        comodel_name="res.city",
        domain="[('state_id','=',identity_uf_id)]",
        groups="hr.group_hr_user",
    )

    civil_certificate_type_id = fields.Many2one(
        string="Civil certificate type",
        comodel_name="hr.civil.certificate.type",
        groups="hr.group_hr_user",
    )

    alternate_phone = fields.Char(groups="hr.group_hr_user")

    emergency_phone = fields.Char(groups="hr.group_hr_user")

    talk_to = fields.Char(string="Emergency contact name", groups="hr.group_hr_user")

    alternate_email = fields.Char(groups="hr.group_hr_user")

    marital = fields.Selection(
        selection_add=[
            ("common_law_marriage", "Common law marriage"),
            ("separated", "Separated"),
        ],
        groups="hr.group_hr_user",
    )

    registration = fields.Char(string="Registration number", groups="hr.group_hr_user")

    country_id = fields.Many2one(comodel_name="res.country", default=_default_country)

    employee_relationship_type = fields.Selection(
        string="Tipo de Colaborador",
        selection=[
            # S2200
            ("funcionario", "Funcionário"),
            # S2300 Sem vinculo
            ("autonomo", "Autônomo"),
            ("terceirizado", "Terceirizado"),
            ("cedido", "Funcionário Cedido"),
        ],
        default="funcionario",
        required=True,
        groups="hr.group_hr_user",
    )

    @api.constrains("pis_pasep")
    def _validate_pis_pasep(self):
        for record in self:
            if record.pis_pasep and not pis.validar(record.pis_pasep):
                raise ValidationError(_("Invalid PIS/PASEP"))

    @api.constrains("cpf")
    def _check_cpf(self):
        for record in self:
            check_cnpj_cpf(record.env, record.cpf, record.country_id)

    @api.onchange("cpf")
    def onchange_cpf(self):
        cpf = cnpj_cpf.formata(str(self.cpf))
        if cpf:
            self.cpf = cpf
