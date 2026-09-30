# Copyright (C) 2026 Luis Felipe Mileo - KMEE <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    l10n_br_sped_referential_code = fields.Char(
        string="Conta referencial da RFB",
        size=60,
        help="Codigo da conta no plano de contas referencial da Receita "
        "Federal em que esta conta desagua. E o mesmo de-para nas duas "
        "escrituracoes: alimenta o registro I051 da ECD e os registros J051, "
        "K156, K356, P100 e P150 da ECF. Quem tem o plano referencial "
        "carregado num modulo de de-para preenche este campo por la.",
    )
