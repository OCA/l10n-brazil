# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class NFeAutXML(spec_models.SpecModel):
    """Person authorized to download the XML of a fiscal document.

    The autXML tag is not the person: it is the authorization of a person on
    that specific document. Hence it is a record of its own rather than a
    field stacked into res.partner, which is a global entity and could only
    ever hold a single authorization per partner.
    """

    _name = "l10n_br_nfe.autxml"
    _inherit = "nfe.40.autxml"
    _description = "Person Authorized to Download the NF-e XML"
    _rec_name = "partner_id"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Authorized Partner",
        required=True,
        ondelete="cascade",
    )

    nfe40_CNPJ = fields.Char(
        compute="_compute_nfe40_cnpj_cpf",
        compute_sudo=True,
    )

    nfe40_CPF = fields.Char(
        compute="_compute_nfe40_cnpj_cpf",
        compute_sudo=True,
    )

    _sql_constraints = [
        (
            "autxml_partner_document_uniq",
            'unique("nfe40_autXML_infNFe_id", partner_id)',
            "This partner is already authorized to download this document XML.",
        ),
    ]

    @api.depends("partner_id.nfe40_CNPJ", "partner_id.nfe40_CPF")
    def _compute_nfe40_cnpj_cpf(self):
        for record in self:
            record.nfe40_CNPJ = record.partner_id.nfe40_CNPJ
            record.nfe40_CPF = record.partner_id.nfe40_CPF

    @api.model
    def _prepare_import_dict(
        self, values, model=None, parent_dict=None, defaults_model=None
    ):
        """Resolve the partner from the CNPJ/CPF carried by the XML.

        parent_dict is deliberately not forwarded: it holds the issuer CNPJ,
        which would override the authorized partner's own document.
        """
        values = super()._prepare_import_dict(
            values, model, parent_dict, defaults_model
        )
        if not values.get("partner_id"):
            partner_values = {
                key: values.pop(key)
                for key in ("nfe40_CNPJ", "nfe40_CPF")
                if values.get(key)
            }
            if partner_values:
                values["partner_id"] = self.env["res.partner"].match_or_create_m2o(
                    partner_values, {}
                )
        return values
