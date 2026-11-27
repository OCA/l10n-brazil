# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class ProductProduct(spec_models.SpecModel):
    _name = "product.product"
    _inherit = [
        "product.product",
        "mdfe.30.prodpred",
    ]

    mdfe30_xProd = fields.Char(related="name")

    mdfe30_cEAN = fields.Char(related="barcode")

    mdfe30_NCM = fields.Char(related="ncm_id.code_unmasked")

    mdfe30_tpCarga = fields.Selection(default="05")

    mdfe30_infLotacao = fields.Many2one(comodel_name="l10n_br_mdfe.product.lotacao")


class MDFeProductLotacao(spec_models.SpecModel):
    _name = "l10n_br_mdfe.product.lotacao"
    _inherit = "mdfe.30.inflotacao"
    _description = "Informações De Lotação MDFe"

    product_id = fields.Many2one(comodel_name="product.product")

    mdfe30_infLocalCarrega = fields.Many2one(
        comodel_name="l10n_br_mdfe.product.lotacao.local",
        required=True,
    )

    mdfe30_infLocalDescarrega = fields.Many2one(
        comodel_name="l10n_br_mdfe.product.lotacao.local",
        required=True,
    )


class MDFeProductLotacaoLocal(spec_models.SpecModel):
    _name = "l10n_br_mdfe.product.lotacao.local"
    _inherit = ["mdfe.30.inflocalcarrega", "mdfe.30.inflocaldescarrega"]
    _description = "Informações De Localização da Lotação MDFe"

    local_type = fields.Selection(
        selection=[
            ("CEP", "CEP"),
            ("coord", "Coordenadas"),
        ],
        default="CEP",
    )

    mdfe30_choice_tlocal = fields.Selection(
        selection=[("mdfe30_CEP", "CEP"), ("mdfe30_latitude", "Latitude/Longitude")],
        string="Tipo de Local",
        compute="_compute_choice",
    )

    @api.depends("local_type")
    def _compute_choice(self):
        for record in self:
            if record.local_type == "CEP":
                record.mdfe30_choice_tlocal = "mdfe30_CEP"
            else:
                record.mdfe30_choice_tlocal = "mdfe30_latitude"
