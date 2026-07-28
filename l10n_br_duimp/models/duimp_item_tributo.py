# Copyright (C) 2026 - TODAY, KMEE (<https://kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

from ..constants.duimp import DUIMP_TRIBUTO_TYPE_SELECTION


class L10nBrDuimpItemTributo(models.Model):
    _name = "l10n_br_duimp.item.tributo"
    _description = "DUIMP Item Tribute"
    _order = "item_id, tipo"

    item_id = fields.Many2one(
        comodel_name="l10n_br_duimp.item",
        string="Item",
        required=True,
        ondelete="cascade",
    )

    declaracao_id = fields.Many2one(
        comodel_name="l10n_br_duimp.declaracao",
        related="item_id.declaracao_id",
        store=True,
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="declaracao_id.currency_id",
    )

    tipo = fields.Selection(
        selection=DUIMP_TRIBUTO_TYPE_SELECTION,
        string="Type",
        required=True,
    )

    regime_codigo = fields.Char(string="Regime Code")
    regime_nome = fields.Char(string="Regime")

    base_calculo = fields.Monetary(string="Tax Base")
    aliquota_ad_valorem = fields.Float(string="Rate (%)", digits=(12, 4))
    valor_devido = fields.Monetary(string="Amount Due")
    valor_recolher = fields.Monetary(string="Amount to Collect")
