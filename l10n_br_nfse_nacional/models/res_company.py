from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class ResCompany(spec_models.SpecModel):
    _name = "res.company"
    _inherit = [
        "res.company",
        "nfse.10.tcinfoprestador",
        "nfse.10.tcregtrib",
    ]

    _nfse10_binding_type = "TcinfoPrestador"

    nfse10_CNPJ = fields.Char(related="partner_id.nfse10_CNPJ")
    nfse10_CPF = fields.Char(related="partner_id.nfse10_CPF")
    nfse10_IM = fields.Char(related="l10n_br_im_code")
    nfse10_xNome = fields.Char(related="partner_id.nfse10_xNome")
    nfse10_email = fields.Char(related="partner_id.nfse10_email")
    nfse10_fone = fields.Char(related="partner_id.nfse10_fone")

    nfse10_end = fields.Many2one("res.partner", related="partner_id")

    # Overriding the inherited fields to make them computed
    nfse10_opSimpNac = fields.Selection(compute="_compute_nfse10_reg_trib")
    nfse10_regApTribSN = fields.Selection(compute="_compute_nfse10_reg_trib")
    nfse10_regEspTrib = fields.Selection(compute="_compute_nfse10_reg_trib")

    @api.depends("tax_framework")
    def _compute_nfse10_reg_trib(self):
        for rec in self:
            if rec.tax_framework == "4":  # MEI
                rec.nfse10_opSimpNac = "2"
                rec.nfse10_regApTribSN = False
                rec.nfse10_regEspTrib = "0"
            elif rec.tax_framework in ["1", "2"]:  # Simples Nacional
                rec.nfse10_opSimpNac = "3"
                rec.nfse10_regApTribSN = "1"  # Tributos federais e municipal pelo SN
                rec.nfse10_regEspTrib = "0"
            else:
                rec.nfse10_opSimpNac = "1"  # Não optante
                rec.nfse10_regApTribSN = False
                rec.nfse10_regEspTrib = "0"

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        if field_name == "nfse10_regTrib":
            return self._build_binding(
                class_name=class_obj._fields[field_name].comodel_name
            )
        return super()._export_many2one(field_name, xsd_required, class_obj)
