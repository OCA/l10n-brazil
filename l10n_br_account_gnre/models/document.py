# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, _, fields, models


class Document(models.Model):
    """Cria a conta a pagar quando a guia é emitida.

    Espelha o `create_wh_invoices` do `l10n_br_account_withholding`, com uma
    diferença de tempo: lá a fatura a pagar nasce no `_post()` da compra, aqui
    nasce quando a guia é montada, porque é a guia que define o valor e o
    credor finais depois do agrupamento.
    """

    _inherit = "l10n_br_fiscal.document"

    def _prepare_gnre_payable(self, obligations):
        """Values of the payable invoice against the favoured state."""
        self.ensure_one()
        first = obligations[0]
        config = first.config_id
        journal = config.journal_id or self.env["account.journal"].search(
            [
                ("type", "=", "purchase"),
                ("company_id", "=", self.company_id.id),
            ],
            limit=1,
        )
        name = _("GNRE %(state)s %(revenue)s") % {
            "state": first.fiscal_state_id.code,
            "revenue": first.revenue_code,
        }
        return {
            "company_id": self.company_id.id,
            "partner_id": first.authority_partner_id.id,
            "move_type": "in_invoice",
            "journal_id": journal.id,
            "date": fields.Date.context_today(self),
            "invoice_date": fields.Date.context_today(self),
            "invoice_date_due": first.date_due,
            "invoice_origin": self.display_name,
            "invoice_line_ids": [
                Command.create(
                    {
                        "name": name,
                        "quantity": 1.0,
                        "price_unit": sum(obligations.mapped("amount_total")),
                        "tax_ids": [Command.clear()],
                    }
                )
            ],
        }

    def _create_gnre_payable(self, obligations):
        """Create and link the payable invoice of a guide."""
        self.ensure_one()
        if not obligations.mapped("authority_partner_id"):
            # Sem credor resolvido nao da para faturar: melhor a guia existir
            # sem o titulo do que um titulo contra parceiro errado.
            return self.env["account.move"]

        payable = self.env["account.move"].create(
            self._prepare_gnre_payable(obligations)
        )
        config = obligations[0].config_id
        if config.payable_account_id:
            payable.line_ids.filtered(
                lambda line: line.account_id.account_type == "liability_payable"
            ).write({"account_id": config.payable_account_id.id})
        payable.message_post_with_view(
            "mail.message_origin_link",
            values={"self": payable, "origin": self},
            subtype_id=self.env.ref("mail.mt_note").id,
        )
        obligations.write({"payable_move_id": payable.id})
        return payable

    def _create_gnre_guide(self, obligations):
        guide = super()._create_gnre_guide(obligations)
        guide._create_gnre_payable(obligations)
        return guide
