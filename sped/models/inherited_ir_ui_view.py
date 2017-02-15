# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import api, fields, models
from odoo.modules.module import get_resource_from_path


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    copy_id = fields.Many2one(
        comodel_name='ir.ui.view',
        string=u'Copied View',
        ondelete='restrict',
        index=True,
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

    def _inverse_arch(self):
        for view in self:
            if not view.copy_id:
                super(IrUiView, view)._inverse_arch()
                continue

            data = dict(arch_db=view.copy_id.arch)

            if 'install_mode_data' in self._context:
                imd = self._context['install_mode_data']
                if '.' not in imd['xml_id']:
                    imd['xml_id'] = '%s.%s' % (imd['module'], imd['xml_id'])
                if self._name == imd['model'] and (not view.xml_id or view.xml_id == imd['xml_id']):
                    # we store the relative path to the resource instead of the absolute path, if found
                    # (it will be missing e.g. when importing data-only modules using base_import_module)
                    path_info = get_resource_from_path(imd['xml_file'])
                    if path_info:
                        data['arch_fs'] = '/'.join(path_info[0:2])

            view.write(data)

    @api.model
    def create(self, values):
        if values.get('copy_id'):
            values['type'] = self.browse(values['copy_id']).type

        return super(IrUiView, self).create(values)
