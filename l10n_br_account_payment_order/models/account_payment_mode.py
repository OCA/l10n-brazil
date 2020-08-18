# Copyright (C) 2012-Today - KMEE (<http://kmee.com.br>).
#  @author Luis Felipe Miléo - mileo@kmee.com.br
#  @author Renato Lima - renato.lima@akretion.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class AccountPaymentMode(models.Model):
    _inherit = 'account.payment.mode'

    internal_sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        string='Sequência',
    )

    instrucoes = fields.Text(
        string='Instruções de cobrança',
    )

    invoice_print = fields.Boolean(
        string='Gerar relatorio na conclusão da fatura?'
    )

    _sql_constraints = [(
        "internal_sequence_id_unique",
        "unique(internal_sequence_id)",
        _("Sequência já usada! Crie uma sequência unica para cada modo"),
        )
    ]
