# Copyright (C) 2026 - TODAY, KMEE (<https://kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class L10nBrDuimpAcrescimoDeducao(models.Model):
    """Additions (+) and deductions (-) reported by the DUIMP
    (``acrescimosDeducoes``). Ported from ``l10n_br_di.valor``: a positive
    ``valor`` is an addition, a negative one is a deduction, both already
    converted to BRL, with the negotiated currency and implicit exchange
    rate kept for auditing.
    """

    _name = "l10n_br_duimp.acrescimo.deducao"
    _inherit = "l10n_br_duimp.mixin"
    _description = "DUIMP Addition/Deduction"

    declaracao_id = fields.Many2one(
        comodel_name="l10n_br_duimp.declaracao",
        related="item_id.declaracao_id",
        store=True,
    )

    item_id = fields.Many2one(
        comodel_name="l10n_br_duimp.item",
        string="Item",
        required=True,
        ondelete="cascade",
    )

    codigo = fields.Char(string="Code")
    denominacao = fields.Char(string="Description")

    moeda_negociada_codigo = fields.Char(string="Currency Code (Siscomex)")
    moeda_negociada_id = fields.Many2one(
        comodel_name="res.currency",
        string="Negotiated Currency",
    )
    moeda_empresa_id = fields.Many2one(
        comodel_name="res.currency",
        related="declaracao_id.currency_id",
    )

    valor = fields.Monetary(
        string="Amount (BRL)",
        currency_field="moeda_empresa_id",
        help="Amount already converted to BRL. Positive for an addition, "
        "negative for a deduction.",
    )
    valor_moeda_negociada = fields.Monetary(
        string="Amount (Currency)",
        currency_field="moeda_negociada_id",
    )
    moeda_taxa = fields.Float(string="Exchange Rate", digits=(12, 8))
