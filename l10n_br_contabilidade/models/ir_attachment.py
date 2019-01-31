# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def create(self, cr, uid, values, context=None):
        self.check(cr, uid, [], mode='write', context=context, values=values)

        res_model = values.get('res_model')
        if res_model == 'mis.report.instance':
            name_ext = values.get('name').split('.')

            if len(name_ext) > 1:
                res_id = values.get('res_id')
                report_instance_id = \
                    self.pool.get(res_model).browse(cr, uid, [res_id],
                                                    context=context)
                report_instance_id.\
                    remove_duplicated_filetype_attachments(name_ext[-1])

        return super(IrAttachment, self).create(cr, uid, values, context)
