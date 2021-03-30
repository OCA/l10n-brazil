# © 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    cnab_return_log_id = fields.Many2one(
        string='CNAB Return Log',
        comodel_name='l10n_br_cnab.return.log',
        readonly=True,
        inverse_name='move_id'
    )

    # Usados para deixar invisivel o campo
    # relacionado ao CNAB na visao
    is_cnab = fields.Boolean(
        string='Is CNAB ?'
    )

    @api.multi
    def unlink(self):

        # No caso de Ordens de Pagto vinculadas devido o
        # ondelete=restrict no campo move_line_id do account.payment.line
        # não é possível apagar uma move que já tenha uma Ordem de
        # Pagto confirmada ( processo chamado pelo action_cancel objeto
        # account.invoice ), acontece o erro abaixo de constraint:
        # psycopg2.IntegrityError: update or delete on table
        # "account_move_line" violates foreign key constraint
        # "account_payment_line_move_line_id_fkey" on table
        # "account_payment_line"
        cnab_already_start = False
        for l_aml in self.mapped('line_ids'):
            if l_aml._cnab_already_start():
                # Se exitir um caso já não é possível apagar
                cnab_already_start = l_aml._cnab_already_start()
                break

        if cnab_already_start:
            # Solicitar a Baixa do CNAB
            invoice = self.env['account.invoice'].search([
                ('move_id', '=', self.id)
            ])
            for l_aml in invoice.mapped('financial_move_line_ids'):
                l_aml.update_cnab_for_cancel_invoice()
            # A move está sendo apagada, isso deve estar sendo feito em
            #  outro metodo, porem as account.move.line continuam existindo,
            #  teste feito no modulo que implementa a biblioteca utilizada
            #  TODO: A move deveria ser mantida ? Teria algum problema ?
        else:
            self.mapped('line_ids').unlink()
            return super().unlink()
