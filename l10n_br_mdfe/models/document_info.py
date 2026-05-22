# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, api, fields

from odoo.addons.spec_driven_model.models import spec_models


class MDFeMunicipioDescarga(spec_models.SpecModel):
    _name = "l10n_br_mdfe.municipio.descarga"
    _inherit = "mdfe.30.infmundescarga"
    _description = "Informações de Descarga do Documento MDFe"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_cMunDescarga = fields.Char(related="city_id.ibge_code")

    mdfe30_xMunDescarga = fields.Char(related="city_id.name")

    mdfe30_infCTe = fields.One2many(compute="_compute_document_data")

    mdfe30_infNFe = fields.One2many(compute="_compute_document_data")

    mdfe30_infMDFeTransp = fields.One2many(compute="_compute_document_data")

    state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="State",
        compute="_compute_state_id",
    )

    city_id = fields.Many2one(
        string="City",
        comodel_name="res.city",
        required=True,
    )

    document_type = fields.Selection(
        selection=[
            ("nfe", "NF-e"),
            ("cte", "CT-e"),
            ("mdfe", "MDF-e"),
        ],
        default="nfe",
        required=True,
    )

    country_id = fields.Many2one(
        comodel_name="res.country",
        string="Country",
    )

    nfe_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.document.related",
        relation="mdfe_related_nfe_carregamento_rel",
    )

    cte_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.document.related",
        relation="mdfe_related_cte_carregamento_rel",
    )

    mdfe_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.document.related",
        relation="mdfe_related_mdfe_carregamento_rel",
    )

    @api.depends("document_type", "nfe_ids", "cte_ids")
    def _compute_document_data(self):
        for record in self:
            record.mdfe30_infCTe = [Command.clear()]
            record.mdfe30_infNFe = [Command.clear()]
            record.mdfe30_infMDFeTransp = [Command.clear()]

            if record.document_type == "nfe":
                record.mdfe30_infNFe = [
                    Command.create({"mdfe30_chNFe": nfe.mdfe30_chNFe})
                    for nfe in record.nfe_ids
                ]
            elif record.document_type == "cte":
                record.mdfe30_infCTe = [
                    Command.create({"mdfe30_chCTe": cte.mdfe30_chCTe})
                    for cte in record.cte_ids
                ]
            else:
                record.mdfe30_infMDFeTransp = [
                    Command.create({"mdfe30_chMDFe": mdfe.mdfe30_chMDFe})
                    for mdfe in record.mdfe_ids
                ]

    @api.depends("city_id.state_id")
    def _compute_state_id(self):
        for record in self:
            record.state_id = record.city_id.state_id

    @api.onchange("nfe_ids", "cte_ids", "mdfe_ids")
    def _onchange_document_ids(self):
        docs = self.nfe_ids or self.cte_ids or self.mdfe_ids
        if docs and not self.city_id:
            partner = docs[0].document_related_id.partner_id
            if partner and partner.city_id:
                self.city_id = partner.city_id
