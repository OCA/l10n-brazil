# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class WizardMultiChartsAccounts(models.TransientModel):
    _inherit = 'wizard.multi.charts.accounts'

    def execute(self):
        """This function is called at the confirmation of the wizard to
        generate the COA from the templates. It will read all the provided
        information to create the accounts, the banks, the journals, the
        taxes, the tax codes, the accounting properties... accordingly for
        the chosen company.

        This is override in Brazilian Localization to copy CFOP
        from fiscal positions template to fiscal positions.

        :Parameters:
            - 'cr': Database cursor.
            - 'uid': Current user.
            - 'ids': orm_memory id used to read all data.
            - 'context': Context.
        """
        result = super(WizardMultiChartsAccounts, self).execute()

        obj_multi = self[0]
        obj_fp_template = self.env['account.fiscal.position.template']
        obj_fp = self.env['account.fiscal.position']

        chart_template_id = obj_multi.chart_template_id.id
        company_id = obj_multi.company_id.id

        fp_template_ids = obj_fp_template.search(
            [('chart_template_id', '=', chart_template_id)])

        for fp_template in fp_template_ids:
            if fp_template.cfop_id:
                fp_id = obj_fp.search(
                    [('name', '=', fp_template.name),
                     ('company_id', '=', company_id)])
                if fp_id:
                    fp_id.write(
                        {'cfop_id': fp_template.cfop_id.id})
        return result
