# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from openerp import api, fields, models, _


class MisReportInstance(models.Model):

    _inherit = 'mis.report.instance'

    year_reference = fields.Char(
        string='Reference Year',
        size=4,
    )

    @api.multi
    def remove_duplicated_filetype_attachments(self, format):
        for record in self:
            duplicated_format_attachments = self.env['ir.attachment'].search(
                [('res_model', '=', record._name),
                 ('res_id', '=', record.id)]).filtered(
                lambda a: a.name.split('.')[-1] == format)

            duplicated_format_attachments.unlink()

    @api.multi
    def _compute_attachments(self):
        for record in self:
            record.attachment_ids = self.env['ir.attachment'].search(
                [
                    ('res_model','=',record._name),
                    ('res_id','=',record.id),
                ]
            )

    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='mis_rep_inst_ir_attach_rel',
        column1='mis_report_instance_id',
        column2='attachment_id',
        string=u'Anexos gerados',
        compute='_compute_attachments'
    )
    
    @api.multi
    def print_pdf(self):
        return super(MisReportInstance,
                     self.with_context(mis_report_instance='pdf')).print_pdf()

    @api.multi
    def export_xls(self):
        res = super(MisReportInstance,
                     self.with_context(mis_report_instance='xls',
                                       xls_export= 1)).export_xls()
        res.update(dict(report_name='mis.report.instance.xls2'))
        return res
    

class Report(models.Model):
    _inherit = "report"

    @api.v7
    def get_pdf(self, cr, uid, ids, report_name, html=None, data=None,
                context=None):
        res = super(Report, self).get_pdf(
            cr, uid, ids, report_name, html=html, data=data, context=context)

        if context.get('mis_report_instance'):
            name = 'mis_builder_report_{}.{}'.format(
                fields.Datetime.now(),
                context.get('mis_report_instance'))

            attach_obj = self.pool.get('ir.attachment')

            attach_obj.create(cr, uid,
                {
                    'name': name,
                    'datas': base64.b64encode(res),
                    'datas_fname': name,
                    'description': 'TESTE ' + name,
                    'res_model': 'mis.report.instance',
                    'res_id': context.get('active_ids')[0],
                    'type': 'binary',
                }, context
            )
        return res

    @api.v8
    def get_pdf(self, docids, report_name, html=None, data=None):
        return self._model.get_pdf(self._cr, self._uid,
                                   docids.ids, report_name,
                                   html=html, data=data, context=self._context)
