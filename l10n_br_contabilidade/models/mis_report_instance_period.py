# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class MisReportInstancePeriod(models.Model):
    _inherit = 'mis.report.instance.period'

    incluir_lancamentos_de_fechamento = fields.Boolean(
        string=u'Incluir lançamentos de fechamento?'
    )

    @api.multi
    def _get_additional_move_line_filter(self):
        self.ensure_one()
        res = super(MisReportInstancePeriod, self)._get_additional_move_line_filter()
        if not self.incluir_lancamentos_de_fechamento:
            res.append(('move_id.lancamento_de_fechamento', '=', False))
        return res
