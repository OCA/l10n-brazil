# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class L10nBrAccountMoveTemplateLine(models.Model):
    _name = 'l10n_br_account.move.template.line'
    _description = 'Item de partida dobrada'

    template_id = fields.Many2one(
        comodel_name='l10n_br_account.move.template',
        string=u'Modelo',
        ondelete='cascade',
    )
    model_ids = fields.Many2many(
        comodel_name='ir.model',
        related='template_id.model_ids',
        readonly=True,
    )
    field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        string=u'Campo',
        required=True,
    )
    account_debit_id = fields.Many2one(
        comodel_name='account.account',
        string=u'Débito',
    )
    account_credit_id = fields.Many2one(
        comodel_name='account.account',
        string=u'Crédito',
    )

    @api.onchange('model_ids')
    def _onchange_model_ids(self):
        return {
            'domain': {
                'field_id': [
                    ('model_id', 'in', self.model_ids.ids),
                    ('ttype', 'in', ['float', 'monetary'])
                ]
            }
        }

    @api.multi
    def move_line_template_create(self, obj, lines=[]):
        for item in self:
            for line in obj:
                if not getattr(line, item.field_id.name, False):
                    continue

                value = getattr(line, item.field_id.name, 0.0)

                if item.account_debit_id:
                    data = {
                        'invl_id': line.id,
                        'name': line.name.split('\n')[0][:64],
                        'narration': item.field_id.name,
                        'debit': value,
                        'currency_id': line.currency_id.id,
                        'account_id': item.account_debit_id.id
                    }

                    lines.append((0, 0, data))

                if item.account_credit_id:
                    data = {
                        'invl_id': line.id,
                        'name': line.name.split('\n')[0][:64],
                        'narration': item.field_id.name,
                        'credit': value,
                        'currency_id': line.currency_id.id,
                        'account_id': item.account_credit_id.id
                    }

                    lines.append((0, 0, data))
        move_template = self.mapped('template_id')
        if move_template.parent_id:
            return move_template.parent_id.item_ids.move_line_template_create(
                    obj, lines)

        return lines
