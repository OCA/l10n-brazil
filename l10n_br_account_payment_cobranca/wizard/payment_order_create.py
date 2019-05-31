# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
#   @author Daniel Sadamo <daniel.sadamo@kmee.com.br>
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, api


class PaymentOrderCreate(models.TransientModel):
    _inherit = 'account.payment.line.create'

    @api.multi
    def _prepare_move_line_domain(self):
        """ Nenhuma linha deve ser adicionada novamente a nao ser que o
        retorno do cnab informe que o registro falhou

        :return:
        """
        domain = super(PaymentOrderCreate, self)._prepare_move_line_domain()

        paylines = self.env['account.payment.line'].search([
            ('state', 'in', ('draft', 'open', 'generated', 'uploaded')),
            ('move_line_id', '!=', False)])

        if paylines:
            move_lines_ids = [
                payline.move_line_id.id for payline in paylines
                if payline.move_line_id.state_cnab == 'not_accepted'
            ]
            domain += [('id', 'not in', move_lines_ids)]

        return domain
