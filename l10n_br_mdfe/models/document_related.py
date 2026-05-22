# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class MDFeRelated(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document.related"
    _inherit = [
        "l10n_br_fiscal.document.related",
        "mdfe.30.infmdfetransp",
        "mdfe.30.tmdfe_infnfe",
        "mdfe.30.infcte",
    ]
    _mdfe30_odoo_module = (
        "odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_tipos_basico_v3_00"
    )
    _mdfe30_stacking_mixin = "mdfe.30.tmdfe_infnfe"

    mdfe30_chNFe = fields.Char(related="document_key")

    mdfe30_chCTe = fields.Char(related="document_key")

    mdfe30_chMDFe = fields.Char(related="document_key")

    mdfe30_peri = fields.One2many(comodel_name="l10n_br_mdfe.transporte.perigoso")

    mdfe30_infUnidTransp = fields.One2many(comodel_name="l10n_br_mdfe.transporte.inf")

    partner_name = fields.Char(
        string="Partner",
        compute="_compute_partner_info",
        store=True,
    )

    partner_city_id = fields.Many2one(
        comodel_name="res.city",
        string="City",
        compute="_compute_partner_info",
        store=True,
    )

    @api.depends("document_related_id")
    def _compute_partner_info(self):
        for record in self:
            partner = record.document_related_id.partner_id
            record.partner_name = partner.name if partner else False
            record.partner_city_id = partner.city_id if partner else False

    @api.onchange("document_related_id")
    def _onchange_document_related_id(self):
        res = super()._onchange_document_related_id()
        related = self.document_related_id
        if related and related.document_type_id.electronic:
            self.document_serie = related.document_serie
            self.document_number = related.document_number
        return res
