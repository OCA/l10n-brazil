# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class GnreStateConfig(models.Model):
    """Acrescenta à regra por UF o que só faz sentido com contabilidade."""

    _inherit = "l10n_br_gnre.state.config"

    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Diário",
        company_dependent=True,
        domain="[('type', '=', 'purchase')]",
        help="Diário da fatura a pagar. Sem ele, usa o diário de compras "
        "padrão da empresa.",
    )

    payable_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Conta a Pagar",
        company_dependent=True,
        domain="[('account_type', '=', 'liability_payable')]",
        help="Conta específica da guia. Sem ela, usa a conta padrão do " "parceiro.",
    )

    def _gnre_authority(self, move):
        """Resolve a Secretaria da Fazenda favorecida.

        Reusa o `_get_tax_authority_partner` do `l10n_br_account_withholding`,
        que já sabe procurar o parceiro marcado como SEFAZ do estado, em vez de
        duplicar a busca aqui.
        """
        self.ensure_one()
        if self.authority_partner_id:
            return self.authority_partner_id
        return self.tax_group_id._get_tax_authority_partner(move)
