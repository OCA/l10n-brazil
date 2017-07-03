# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, exceptions, _


class AccountInvoiceConfirm(models.Model):
    """
    This wizard will confirm the all the selected draft invoices
    """
    _inherit = 'account.invoice.confirm'

    @api.multi
    def invoice_confirm(self):
        proxy = self.env['account.invoice']
        for record in proxy.browse(self._context.get('active_ids')):
            if record.state not in ['draft', 'proforma', 'proforma2']:
                raise exceptions.Warning(
                    _('Warning!'),
                    _("Selected invoice(s) cannot be confirmed as they are "
                      "not in 'Draft' or 'Pro-Forma' state."))
            record.signal_workflow('invoice_validate')

        return {'type': 'ir.actions.act_window_close'}
