# Copyright (C) 2026 - TODAY, KMEE (<https://kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class L10nBrDuimpPagamento(models.Model):
    """Payments/DARFs reported by the DUIMP (``pagamentos``). Ported from
    ``l10n_br_di.pagamento``: registry only, no accounting entry is
    generated here (that is handled by the generated vendor bill).
    """

    _name = "l10n_br_duimp.pagamento"
    _description = "DUIMP Payment"

    declaracao_id = fields.Many2one(
        comodel_name="l10n_br_duimp.declaracao",
        string="Declaration",
        required=True,
        ondelete="cascade",
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="declaracao_id.currency_id",
        readonly=True,
    )

    codigo_receita = fields.Char(string="Revenue Code")
    codigo_tipo_pagamento = fields.Char(string="Payment Type Code")
    nome_tipo_pagamento = fields.Char(string="Payment Type")
    data_pagamento = fields.Date(string="Payment Date")
    numero_retificacao = fields.Char(string="Amendment Number")

    valor_receita = fields.Monetary(string="Revenue Amount")
    valor_juros_encargos = fields.Monetary(string="Interest/Charges")
    valor_multa = fields.Monetary(string="Penalty")
