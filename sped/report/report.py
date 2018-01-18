# -*- encoding: utf-8 -*-
# Copyright 2014 KMEE INFORMATICA LTDA
#       Rodolfo Leme Bertozo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from __future__ import with_statement
import odoo
from odoo.report.interface import report_int


class report_custom(report_int):
    '''
        Custom report for return danfe
    '''

    def create(self, cr, uid, ids, datas, context=None):
        if not context:
            context = dict()
        env = odoo.api.Environment(cr, uid, context)
        datas['ids'] = ids
        records = env['sped.documento'].browse(ids)
        pdf = records.gera_pdf()
        return pdf, 'pdf'

report_custom('report.report_sped_documento')
