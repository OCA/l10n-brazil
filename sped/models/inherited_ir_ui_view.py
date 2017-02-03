# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import api, fields, models


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    copy_id = fields.Many2one(
        comodel_name='ir.ui.view',
        string='Copied View',
        ondelete='restrict',
        index=True
    )
    # copy_id = fields.Many2one(
    # 'ir.ui.view', string='Copied View', index=True)
    # inherit_id = fields.Many2one(
    # 'ir.ui.view', string='Inherited View', index=True)

    def _compute_arch(self):
        for view in self:
            if view.copy_id:
                view.arch = view.copy_id.arch
            else:
                super(IrUiView, view)._compute_arch()

    @api.model
    def create(self, values):
        if values.get('copy_id'):
            values['type'] = self.browse(values['copy_id']).type

        return super(IrUiView, self).create(values)
