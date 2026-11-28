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

        Ordem de resolução:

        1. o parceiro informado na própria regra da UF;
        2. o `_get_tax_authority_partner` do `l10n_br_account_withholding`,
           quando esse módulo estiver instalado (ele procura o parceiro
           marcado como SEFAZ do estado de destino);
        3. o parceiro do grupo fiscal.

        Na 18.0 o `l10n_br_account_withholding` ainda não foi migrado, por
        isso ele deixou de ser dependência: o passo 2 é opcional.
        """
        self.ensure_one()
        if self.authority_partner_id:
            return self.authority_partner_id
        tax_group = self.tax_group_id
        if hasattr(tax_group, "_get_tax_authority_partner"):
            return tax_group._get_tax_authority_partner(move)
        return tax_group.partner_id
