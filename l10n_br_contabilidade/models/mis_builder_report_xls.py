# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from openerp import fields

from openerp.addons.mis_builder.report.mis_builder_xls import (
    MisBuilderXls,
    MisBuilderXlsParser
)


class MisBuilderXls(MisBuilderXls):

    def create_source_xls(self, cr, uid, ids, data, context=None):
        res = super(MisBuilderXls, self).create_source_xls(
            cr, uid, ids, data, context=context)

        attach_obj = self.pool.get('ir.attachment')

        data = base64.b64encode(res[0])
        name = 'mis_builder_report_{}.xls'.format(fields.Datetime.now())
        attach_obj.create(
            cr, uid,
            {
                'name': name,
                'datas': data,
                'datas_fname': name,
                'description': u'MIS builder report',
                'res_model': 'mis.report.instance',
                'res_id': ids[0]
            },
        context=context)

        return res

MisBuilderXls('report.mis.report.instance.xls2',
              'mis.report.instance',
              parser=MisBuilderXlsParser)
