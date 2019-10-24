# (c) 2014 Kmee - Rafael da Silva Lima <rafael.lima@kmee.com.br>
# (c) 2014 Kmee - Matheus Felix <matheus.felix@kmee.com.br>
# (c) 2016 KMEE Informática - Daniel Sadamo <daniel.sadamo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from erpbrasil.base.fiscal import cnpj_cpf, pis
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _default_country(self):
        return self.env["res.country"].search([("code", "=", "BR")])

    naturalidade = fields.Many2one(string="Naturalidade", comodel_name="res.city")

    pis_pasep = fields.Char(string="PIS/PASEP", size=15)

    ctps = fields.Char(string="CTPS", help="CTPS number")

    ctps_series = fields.Char(string="CTPS series")

    ctps_date = fields.Date(string="CTPS emission date")

    ctps_uf_id = fields.Many2one(
        string="CTPS district", comodel_name="res.country.state"
    )

    creservist = fields.Char(string="Military service status certificate")

    cresv_categ = fields.Selection(
        string="Military service status category",
        selection=[
            ("1", "First Category"),
            ("2", "Second Category"),
            ("3", "Third Category"),
        ],
        default="3",
    )

    educational_attainment = fields.Many2one(
        string="Educational attainment",
        comodel_name="hr.educational.attainment",
        track_visibility="onchange",
    )

    have_dependent = fields.Boolean(
        string="Has dependents", track_visibility="onchange"
    )

    dependent_ids = fields.One2many(
        comodel_name="hr.employee.dependent",
        inverse_name="employee_id",
        string="Dependents",
    )

    rg = fields.Char(
        string="RG",
        store=True,
        related="address_home_id.inscr_est",
        help="National ID number",
    )

    cpf = fields.Char(
        string="CPF", store=True, related="address_home_id.cnpj_cpf", readonly=False
    )

    organ_exp = fields.Char(string="Dispatcher organ")

    rg_emission = fields.Date(string="Emission date")

    voter_title = fields.Char(string="Voter title")

    voter_zone = fields.Char(string="Voter zone")

    voter_section = fields.Char(string="Voter section")

    driver_license = fields.Char(string="Driver license number")

    driver_categ = fields.Char(string="Driver license category")

    father_name = fields.Char(string="Father name")

    mother_name = fields.Char(string="Mother name")

    expiration_date = fields.Date(string="Expiration date")

    ethnicity = fields.Many2one(string="Ethnicity", comodel_name="hr.ethnicity")

    blood_type = fields.Selection(
        string="Blood type",
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
    )

    deficiency_id = fields.Many2one(
        string="Deficiency", comodel_name="hr.deficiency", track_visibility="onchange"
    )

    deficiency_description = fields.Char(string="Deficiency description")

    identity_type_id = fields.Many2one(
        string="ID type", comodel_name="hr.identity.type"
    )

    identity_validity = fields.Date(string="ID expiration date")

    identity_uf_id = fields.Many2one(
        string="ID expedition district", comodel_name="res.country.state"
    )

    identity_city_id = fields.Many2one(
        string="ID expedition city",
        comodel_name="res.city",
        domain="[('state_id','=',identity_uf_id)]",
    )

    civil_certificate_type_id = fields.Many2one(
        string="Civil certificate type", comodel_name="hr.civil.certificate.type"
    )

    alternate_phone = fields.Char(string="Alternate phone")

    emergency_phone = fields.Char(string="Emergency phone")

    talk_to = fields.Char(string="Emergency contact name")

    alternate_email = fields.Char(string="Alternate email")

    marital = fields.Selection(
        selection_add=[
            ("common_law_marriage", "Common law marriage"),
            ("separated", "Separated"),
        ]
    )

    registration = fields.Char(string="Registration number")

    country_id = fields.Many2one(comodel_name="res.country", default=_default_country)

    tipo = fields.Selection(
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
    )

    @api.constrains("dependent_ids")
    def _check_dependents(self):
        self._check_dob()
        self._check_dependent_type()

    def _check_dob(self):
        for dependent in self.dependent_ids:
            if dependent.dependent_dob > fields.Date.context_today(self):
                raise ValidationError(
                    _("Invalid birth date for dependent %s") % dependent.name
                )

    def _check_dependent_type(self):
        seen = set()
        restrictions = (
            self.env.ref("l10n_br_hr.l10n_br_dependent_1"),
            self.env.ref("l10n_br_hr.l10n_br_dependent_9_1"),
            self.env.ref("l10n_br_hr.l10n_br_dependent_9_2"),
        )
        for dependent in self.dependent_ids:
            dep_type = dependent.dependent_type_id
            if dep_type not in seen and dep_type in restrictions:
                seen.add(dep_type)
            elif dep_type in seen and dep_type in restrictions:
                raise ValidationError(
                    _(
                        "A dependent with the same level of relatedness"
                        " already exists for dependent %s"
                    )
                    % dependent.name
                )

    @api.constrains("pis_pasep")
    def _validate_pis_pasep(self):
        for record in self:
            if record.pis_pasep and not pis.validar(record.pis_pasep):
                raise ValidationError(_("Invalid PIS/PASEP"))

    @api.multi
    @api.constrains("cpf")
    def _check_cpf(self):
        for record in self:
            if record.cpf and not cnpj_cpf.validar(record.cpf):
                raise ValidationError(_("CPF Invalido!"))

    @api.onchange("cpf")
    def onchange_cpf(self):
        cpf = cnpj_cpf.formata(str(self.cpf))
        if cpf:
            self.cpf = cpf
