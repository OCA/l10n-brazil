# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, api, fields

from odoo.addons.spec_driven_model.models import spec_models


class MDFeMunicipioDescarga(spec_models.SpecModel):
    _name = "l10n_br_mdfe.municipio.descarga"
    _inherit = "mdfe.30.infmundescarga"
    _description = "Informações de Descarga do Documento MDFe"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_cMunDescarga = fields.Char(compute="_compute_city_data")

    mdfe30_xMunDescarga = fields.Char(compute="_compute_city_data")

    mdfe30_infCTe = fields.One2many(compute="_compute_document_data")

    mdfe30_infNFe = fields.One2many(compute="_compute_document_data")

    mdfe30_infMDFeTransp = fields.One2many(compute="_compute_document_data")

    country_id = fields.Many2one(
        comodel_name="res.country.state",
        default=lambda self: self.env.ref("base.br"),
    )

    state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="State",
        domain="[('country_id', '=', country_id)]",
        required=True,
    )

    city_id = fields.Many2one(
        string="City",
        comodel_name="res.city",
        domain="[('state_id', '=', state_id)]",
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

    @api.depends("city_id")
    def _compute_city_data(self):
        for record in self:
            record.mdfe30_cMunDescarga = record.city_id.ibge_code
            record.mdfe30_xMunDescarga = record.city_id.name

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
