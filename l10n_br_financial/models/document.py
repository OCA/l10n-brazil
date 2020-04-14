# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO
)


class Document(models.Model):

    _inherit = "l10n_br_fiscal.document"

    financial_move_ids = fields.One2many(
        comodel_name='account.payment',
        inverse_name='document_id',
    )

    def _generate_financial_account_moves(self, move_lines):
        if not self.financial_move_ids:
            self.generate_financial_move()
        self.financial_move_ids.generate_move(move_lines)

    def generate_financial_move(self):
        """ Cria o lançamento financeiro do record fiscal
        :return:
        """
        for record in self:
            # if record.state_fiscal not in \
            #         SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO:
            #     continue

            # if record.emissao == TIPO_EMISSAO_PROPRIA and \
            #     record.entrada_saida == ENTRADA_SAIDA_ENTRADA:
            #     continue

            financial_move = self.financial_ids.prepare_financial_move()
            if financial_move:
                vals = [(6, 0, {})]
                vals.extend(financial_move)
                record.write({'financial_move_ids': vals})

                # record.financial_move_ids.action_confirm()

    def _exec_after_SITUACAO_EDOC_AUTORIZADA(self, old_state, new_state):
        super(Document, self)._exec_after_SITUACAO_EDOC_AUTORIZADA(
            old_state, new_state
        )
        self.generate_financial_move()

    #
    # @api.onchange('payment_term_id', 'date_invoice', 'amount_total')
    # def _onchange_payment_term_date_invoice(self):
    #     date_invoice = self.date_invoice
    #     if not date_invoice:
    #         date_invoice = fields.Date.context_today(self)
    #     if self.payment_term_id and self.invoice_line_ids:
    #         pterm = self.payment_term_id
    #         pterm_list = pterm.with_context(currency_id=self.company_id.currency_id.id).compute(value=self.amount_total or 1, date_ref=date_invoice)[0]
    #
    #         financial_ids = [
    #             (6, 0, [])
    #         ]
    #
    #         for item in pterm_list:
    #             financial_ids.append((0, 0, {
    #                 'invoice_id': self.id,
    #                 'date_maturity': item[0],
    #                 'amount': item[1],
    #                 'partner_id': self.partner_id.id,
    #                 'journal_id': 7,
    #                 'payment_type': '2receive',
    #                 'partner_type': 'customer',
    #                 'payment_method_id': 1,
    #                 'currency_id': self.currency_id.id,
    #                 'payment_date': item[0],
    #                 'company_id': self.currency_id.id,
    #                 'state': 'draft',
    #             }))
    #         self.financial_ids = financial_ids
    #         self.date_due = max(line[0] for line in pterm_list)
    #     elif self.date_due and (date_invoice > self.date_due):
    #         self.date_due = date_invoice
    #
    #
