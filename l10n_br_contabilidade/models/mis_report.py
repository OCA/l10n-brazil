# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from openerp import api, fields, models, _
from openerp.addons.mis_builder.models.aep import \
    AccountingExpressionProcessor as AEP

MIS_REPORT_MODE = [
    ('contabil', u'Contábil'),
    ('gerencial', 'Gerencial'),
]


class MisReport(models.Model):

    _inherit = 'mis.report'

    report_mode = fields.Selection(
        string=u'Modalidade de relatório',
        selection=MIS_REPORT_MODE,
        default='contabil'
    )
    considerations = fields.Text(
        string=u'Considerações finais'
    )

    @api.multi
    def _prepare_aep(self, root_account):
        self.ensure_one()
        aep = AEP(self.env)
        domain = "[('move_id.lancamento_de_fechamento', '=', False)]"

        for kpi in self.kpi_ids:

            # Limpando o domain existente
            kpi_expression = kpi.expression.replace(domain, '')

            # Inserindo o novo domain na expressão
            if not kpi.incluir_lancamentos_de_fechamento:
                kpi_expression = re.sub(r'(\w+\[[\d.,\s]+\])', '\\1' + domain,
                                        kpi_expression)
            kpi.expression = kpi_expression
            aep.parse_expr(kpi.expression)

        aep.done_parsing(root_account)
        return aep
