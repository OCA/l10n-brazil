# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class L10nBrAccountMoveTemplate(models.Model):
    _name = 'l10n_br_account.move.template'
    _inherit = 'l10n_br_fiscal.data.abstract'
    _description = 'Modelo de partidas dobradas'

    code = fields.Char(required=False)
    model_id = fields.Many2one(
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
        string='Itens',
    )

    def generate_move(self, obj, move_lines):
        return self.item_ids.move_line_template_create(
            obj, move_lines)
