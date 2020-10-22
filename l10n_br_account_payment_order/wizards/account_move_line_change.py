# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class AccountMoveLineChange(models.TransientModel):

    _name = 'account.move.line.change'

    @api.model
    def default_get(self, fields_list):
        res = super(AccountMoveLineChange, self).default_get(fields_list)
        if self.env.context.get('active_model') == 'account.move.line':
            active_ids = self.env.context.get('active_ids')
            res['account_move_line_ids'] = active_ids
            if active_ids and len(active_ids) == 1:
                move_line_id = self.account_move_line_ids.browse(
                    active_ids
                )
                if move_line_id.date_maturity:
                    res['date_maturity'] = move_line_id.date_maturity
                if move_line_id.payment_mode_id:
                    res['payment_mode_id'] = move_line_id.payment_mode_id.id
        return res

    account_move_line_ids = fields.Many2many(
        comodel_name='account.move.line',
        string='Move Line',
        readonly=True,
    )
    change_type = fields.Selection(
        selection=[
            ('change_date_maturity', 'Vencimento'),
            ('change_payment_mode', 'Modo de Pagamento'),
            ('baixa', 'Baixa'),
        ],
        string='Tipo Alteração',
    )
    date_maturity = fields.Date(
        string="Date Maturity"
    )
    payment_mode_id = fields.Many2one(
        comodel_name='account.payment.mode',
    )
    # Muitas opções são permitidas, verificar manual do cnab 240.
    # Entretanto inicialmente só vamos implementar as mais simples.

    def _pre_process_change(self):
        pass

    def _change_date_maturity(self):
        for aml in self.account_move_line_ids:
            if aml.date_maturity != self.date_maturity:
                aml.date_maturity = self.date_maturity

    def _change_payment_mode(self):
        for aml in self.account_move_line_ids:
            if aml.payment_mode_id != self.payment_mode_id:
                aml.payment_mode_id = self.payment_mode_id

    def _change_baixa(self):
        NotImplementedError

    def _post_process_change(self):
        pass

    @api.multi
    def doit(self):
        self._pre_process_change()
        if self.change_type == 'change_date_maturity':
            self._change_date_maturity()
        elif self.change_type == 'change_payment_mode':
            self._change_payment_mode()
        elif self.change_type == 'baixa':
            self._change_baixa()
        self._post_process_change()
