# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models, _


class L10nBrAccountMoveTemplate(models.Model):
    _name = 'l10n_br_account.move.template'
    _description = 'Modelo de partidas dobradas'

    name = fields.Char(
        string=u'Descrição',
        required=True,
        index=True,
    )
    model_ids = fields.Many2many(
        comodel_name='ir.model',
    )
    parent_id = fields.Many2one(
        string='Parent',
        comodel_name='l10n_br_account.move.template',
    )
    child_ids = fields.One2many(
        string='Children',
        comodel_name='l10n_br_account.move.template',
        inverse_name='parent_id',
    )
    item_ids = fields.One2many(
        comodel_name='l10n_br_account.move.template.line',
        inverse_name='template_id',
        string=u'Itens',
    )

    def generate_move(self, obj, ref, journal_id, date, narration):

        lines = self.item_ids.move_line_template_create(
            obj, [])
        move_vals = {
            'ref': ref,
            'line_ids': lines,
            'journal_id': journal_id.id,
            'date': date,
            'narration': narration,
        }

        return move_vals
