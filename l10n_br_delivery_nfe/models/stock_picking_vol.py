# Copyright (C) 2024 Diego Paradeda - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class StockPickingVol(models.Model):
    _name = "stock.picking.vol"
    _description = "Volume Data"
    # _inherit = "nfe.40.vol" TODO: consider using inherit in the future

    """
    NFe40 fields start
    ##################
    this section copies fields from nfe.40.vol
    sadly, _name/_inherit breaks spec_model
    inheriting would be better than recreating the same fields.
    TODO: learn how to inherit nfe mixin (https://github.com/OCA/l10n-brazil/pull/3091)
    """
    nfe40_vol_transp_id = fields.Many2one(comodel_name="nfe.40.transp")
    nfe40_qVol = fields.Char(string="Quantidade de volumes transportados")
    nfe40_esp = fields.Char(string="Espécie dos volumes transportados")
    nfe40_marca = fields.Char(string="Marca dos volumes transportados")
    nfe40_nVol = fields.Char(string="Numeração dos volumes transportados")

    nfe40_pesoL = fields.Float(
        string="Peso líquido (em kg)",
        digits=(
            12,
            3,
        ),
    )

    nfe40_pesoB = fields.Float(
        string="Peso bruto (em kg)",
        digits=(
            12,
            3,
        ),
    )

    nfe40_lacres = fields.One2many(
        "stock.picking.lacres", "nfe40_lacres_vol_id", string="lacres"
    )
    """
    NFe40 fields end
    ################
    """

    picking_id = fields.Many2one(
        comodel_name="stock.picking",
        string="Stock Picking",
    )
