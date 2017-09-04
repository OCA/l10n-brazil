# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FinancialMove(models.Model):
    _inherit = b'financial.move'

    cheque_id = fields.Many2one(
        comodel_name='financeiro.cheque',
        string=u'Cheques'
    )

    document_type_id = fields.Many2one(
        string=u'Tipo de documento',
    )

    amount_document = fields.Float(
        string=u'Valor',
    )

    @api.onchange('cheque_id', 'cheque_id.valor')
    def _set_amount_document(self):
        if self.cheque_id and self.cheque_id.valor:
            self.amount_document = self.cheque_id.valor

    @api.model
    def create(self, vals):
        move = super(FinancialMove, self).create(vals)
        if move.cheque_id:
            move.cheque_id.valor_residual -= move.amount_document
        return move

    @api.multi
    def unlink(self):
        for move in self:
            if move.cheque_id:
                move.cheque_id.valor_residual += move.amount_document
        return super(FinancialMove, self).unlink()

    @api.multi
    def action_confirm(self):
        for record in self:
            record.change_state('open')
            if record.participante_id:
                record.participante_id._compute_credit()
