# (c) 2014 Kmee - Rafael da Silva Lima <rafael.lima@kmee.com.br>
# (c) 2014 Kmee - Matheus Felix <matheus.felix@kmee.com.br>
# (c) 2016 KMEE Informática - Daniel Sadamo <daniel.sadamo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from erpbrasil.base import misc
from erpbrasil.base.fiscal import cnpj_cpf, pis

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.l10n_br_base.tools import check_cnpj_cpf


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _default_country(self):
        return self.env["res.country"].search([("code", "=", "BR")])

    birth_city_id = fields.Many2one(comodel_name="res.city", groups="hr.group_hr_user")

    pis_pasep = fields.Char(string="PIS/PASEP", groups="hr.group_hr_user")

    pis_pasep_formatted = fields.Char(
        string="PIS/PASEP Formatted",
        compute="_compute_pis_pasep_formatted",
        inverse="_inverse_pis_pasep_formatted",
        help="PIS/PASEP displayed with punctuation (XXX.XXXXX.XX-X);"
        " it is stored unformatted in the pis_pasep field.",
        groups="hr.group_hr_user",
    )

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

    l10n_br_rg_code = fields.Char(
        related="work_contact_id.l10n_br_rg_code",
        help="National ID number",
        groups="hr.group_hr_user",
    )

    vat = fields.Char(
        string="CPF",
        related="work_contact_id.vat",
        readonly=False,
        groups="hr.group_hr_user",
    )

    vat_formatted_cnpj = fields.Char(
        string="CPF Formatted",
        compute="_compute_vat_formatted_cnpj",
        inverse="_inverse_vat_formatted_cnpj",
        help="CPF displayed with punctuation (XXX.XXX.XXX-XX); it is stored"
        " unformatted in the vat field.",
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

    alternate_email = fields.Char(groups="hr.group_hr_user")

    marital = fields.Selection(
        selection="_get_marital_status_selection",
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._sanitize_document_fields(vals)
        employees = super().create(vals_list)
        # The hr module auto-creates the work contact only after the
        # related field inverse has run, so a vat (CPF) given at creation
        # time would be lost: apply it again on the created work contact.
        for employee, vals in zip(employees, vals_list, strict=False):
            if vals.get("vat") and employee.work_contact_id:
                employee.vat = vals["vat"]
        return employees

    def write(self, vals):
        self._sanitize_document_fields(vals)
        return super().write(vals)

    @api.model
    def _sanitize_document_fields(self, vals):
        """Store identification documents as plain digits, as required by
        the eSocial layouts; formatted values are exposed by the
        pis_pasep_formatted and vat_formatted_cnpj fields. The employee
        vat (CPF) is sanitized here and not only on the work contact,
        because the res.partner vat normalization of l10n_br_base is
        skipped for non-Brazilian contacts."""
        for fname in ("vat", "pis_pasep", "ctps"):
            if vals.get(fname):
                vals[fname] = misc.punctuation_rm(str(vals[fname]))

    @api.depends("pis_pasep")
    def _compute_pis_pasep_formatted(self):
        for record in self:
            pis_pasep = record.pis_pasep
            if pis_pasep and len(pis_pasep) == 11 and pis_pasep.isdigit():
                record.pis_pasep_formatted = (
                    f"{pis_pasep[:3]}.{pis_pasep[3:8]}.{pis_pasep[8:10]}"
                    f"-{pis_pasep[10]}"
                )
            else:
                # legacy records may still hold a punctuated value
                record.pis_pasep_formatted = pis_pasep

    def _inverse_pis_pasep_formatted(self):
        for record in self:
            if record.pis_pasep_formatted:
                record.pis_pasep = misc.punctuation_rm(record.pis_pasep_formatted)
            else:
                record.pis_pasep = False

    @api.constrains("pis_pasep")
    def _validate_pis_pasep(self):
        for record in self:
            if record.pis_pasep and not pis.validar(record.pis_pasep):
                raise ValidationError(_("Invalid PIS/PASEP"))

    @api.constrains("ctps")
    def _validate_ctps(self):
        for record in self:
            ctps = record.ctps
            if ctps and (not ctps.isdigit() or len(ctps) > 11):
                raise ValidationError(
                    _(
                        "The CTPS number must hold up to 11 digits, without"
                        " punctuation."
                    )
                )

    @api.constrains("vat")
    def _check_cpf(self):
        for record in self:
            check_cnpj_cpf(record.env, record.vat, record.country_id)

    @api.depends("vat", "country_id")
    def _compute_vat_formatted_cnpj(self):
        for record in self:
            vat = record.vat
            if vat and record.country_id.code == "BR" and len(vat) in (11, 14):
                record.vat_formatted_cnpj = cnpj_cpf.formata(vat)
            else:
                # foreign document or legacy punctuated value: show it as stored
                record.vat_formatted_cnpj = vat

    def _inverse_vat_formatted_cnpj(self):
        for record in self:
            if record.vat_formatted_cnpj:
                record.vat = misc.punctuation_rm(record.vat_formatted_cnpj)
            else:
                record.vat = False

    @api.model
    def _get_marital_status_selection(self):
        return super()._get_marital_status_selection() + [
            ("common_law_marriage", _("Common law marriage")),
            ("separated", _("Separated")),
        ]
