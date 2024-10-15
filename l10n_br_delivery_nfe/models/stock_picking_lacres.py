# Copyright (C) 2024 Diego Paradeda - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class StockPickingLacres(models.Model):
    _name = "stock.picking.lacres"
    _description = "lacres"
    # _inherit = "nfe.40.lacres" TODO: consider using inherit in the future

    """
    NFe40 fields start
    ##################
    this section copies fields from nfe.40.vol
    sadly, _name/_inherit breaks spec_model
    inheriting would be better than recreating the same fields.
    """
    nfe40_lacres_vol_id = fields.Many2one(comodel_name="stock.picking.vol")
    nfe40_nLacre = fields.Char(string="Número dos Lacres")
    """
    NFe40 fields end
    ################
    """
