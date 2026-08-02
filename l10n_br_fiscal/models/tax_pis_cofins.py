# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models

from .. import tools
from ..constants.fiscal import (
    TAX_DOMAIN_COFINS,
    TAX_DOMAIN_COFINS_ST,
    TAX_DOMAIN_PIS,
    TAX_DOMAIN_PIS_ST,
)


class TaxPisCofins(models.Model):
    _name = "l10n_br_fiscal.tax.pis.cofins"
    _description = "Tax PIS/COFINS"
    # NOTE: l10n_br_fiscal.data.abstract now inherits
    # l10n_br_fiscal.data.editable.mixin, so we get the mixin
    # behavior through it while keeping code_unmasked,
    # date_start/date_end and sped_table.
    _inherit = "l10n_br_fiscal.data.abstract"

    code = fields.Char(required=True)

    name = fields.Text(required=True, index=True)

    piscofins_type = fields.Selection(
        selection=[
            ("ncm", _("NCM")),
            ("product", _("Product")),
            ("company", _("Company")),
        ],
        default="ncm",
        string="Type",
        required=True,
        index=True,
    )

    tax_pis_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax PIS",
        domain=[("tax_domain", "=", TAX_DOMAIN_PIS)],
    )

    tax_pis_st_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax PIS ST",
        domain=[("tax_domain", "=", TAX_DOMAIN_PIS_ST)],
    )

    tax_cofins_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax COFINS",
        domain=[("tax_domain", "=", TAX_DOMAIN_COFINS)],
    )

    tax_cofins_st_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax COFINS ST",
        domain=[("tax_domain", "=", TAX_DOMAIN_COFINS_ST)],
    )

    ncms = fields.Char(string="NCM")

    ncm_exception = fields.Char(string="NCM Exeption")

    not_in_ncms = fields.Char(string="Not in NCM")

    ncm_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.ncm",
        compute="_compute_ncms",
        store=True,
        readonly=True,
        string="NCMs",
    )

    sped_table = fields.Char()

    @api.depends("ncms")
    def _compute_ncms(self):
        ncm = self.env["l10n_br_fiscal.ncm"]
        for r in self:
            domain = []

            # Clear Field to recompute
            r.ncm_ids = False
            if r.ncms:
                domain = tools.domain_field_codes(r.ncms)

            if r.not_in_ncms:
                domain += tools.domain_field_codes(
                    field_codes=r.not_in_ncms, operator1="!=", operator2="not ilike"
                )

            if r.ncm_exception:
                domain += tools.domain_field_codes(
                    field_codes=r.ncm_exception, field_name="exception", code_size=2
                )

            if domain:
                r.ncm_ids = ncm.search(domain)

    def _get_xml_id_name(self):
        self.ensure_one()

        clean_code = self.code.strip()
        name_lower = self.name.lower()

        if "monofásico" in name_lower or "monofasico" in name_lower:
            return f"tax_piscofins_monofasico_{clean_code}"

        if "substituição tributária" in name_lower or " st " in name_lower:
            return f"tax_pis_cofins_st_{clean_code}"

        if "isenção" in name_lower or "isento" in name_lower:
            return f"tax_pis_cofins_isento_{clean_code}"

        if "suspensão" in name_lower:
            return f"tax_pis_cofins_susp_{clean_code}"

        if "sem incidência" in name_lower:
            return f"tax_pis_cofins_seminc_{clean_code}"

        is_zero = False
        if (
            self.tax_pis_id
            and self.tax_pis_id.percent_amount == 0
            and self.tax_cofins_id
            and self.tax_cofins_id.percent_amount == 0
        ):
            is_zero = True

        if is_zero and "monofásico" not in name_lower:
            return f"tax_pis_cofins_0_{clean_code}"

        if "r$" in name_lower:
            return f"tax_pis_cofins_value_{clean_code}"

        if "cumulativo" in name_lower and "não" not in name_lower:
            return "tax_pis_cofins_columativo"
        if "não cumulativo" in name_lower:
            return "tax_pis_cofins_nao_columativo"
        if "simples nacional" in name_lower:
            return "tax_pis_cofins_simples_nacional"
        if "diferenciada" in name_lower:
            return "tax_pis_cofins_diferenciado"

        return f"tax_pis_cofins_{clean_code}"
