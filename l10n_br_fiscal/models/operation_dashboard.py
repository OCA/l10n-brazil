# Copyright (C) 2020  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import json
from odoo import _, api, fields, models


class Operation(models.Model):
    _inherit = "l10n_br_fiscal.operation"

    @api.one
    def _kanban_dashboard(self):
        self.kanban_dashboard = json.dumps(
            self.get_operation_dashboard_datas())

    kanban_dashboard = fields.Text(compute='_kanban_dashboard')
    color = fields.Integer("Color Index", default=0)

    @api.multi
    def get_operation_dashboard_datas(self):
        title = ''
        if self.fiscal_type in ('sale', 'purchase'):
            title = _('Bills to pay') if self.fiscal_type == 'purchase' \
                else _('Invoices owed to you')

        (query, query_args) = self._get_confirmed_documents_query()
        self.env.cr.execute(query, query_args)
        query_results_confirmed = self.env.cr.dictfetchall()
        number_confirm = len(query_results_confirmed)

        (query, query_args) = self._get_authorized_documents_query()
        self.env.cr.execute(query, query_args)
        query_results_authorized = self.env.cr.dictfetchall()
        number_authorized = len(query_results_authorized)

        (query, query_args) = self._get_cancelled_documents_query()
        self.env.cr.execute(query, query_args)
        query_results_cancelled = self.env.cr.dictfetchall()
        number_cancelled = len(query_results_cancelled)

        return {
            'number_confirm': number_confirm,
            'number_authorized': number_authorized,
            'number_cancelled': number_cancelled,
            'title': title
        }

    def _get_confirmed_documents_query(self):
        """
        Returns a tuple containing as its first element the SQL query used to
        gather the bills in draft state data, and the arguments
        dictionary to use to run it as its second.
        """
        # there is no account_move_lines for draft invoices, so no relevant
        # residual_signed value
        return ("""SELECT doc.company_id
                  FROM l10n_br_fiscal_document doc
                  WHERE operation_id = %(operation_id)s
                  AND state_edoc = 'a_enviar';""", {'operation_id': self.id})

    def _get_authorized_documents_query(self):
        """
        Returns a tuple containing as its first element the SQL query used to
        gather the bills in draft state data, and the arguments
        dictionary to use to run it as its second.
        """
        # there is no account_move_lines for draft invoices, so no relevant
        # residual_signed value
        return ("""SELECT doc.company_id
                  FROM l10n_br_fiscal_document doc
                  WHERE operation_id = %(operation_id)s
                  AND state_edoc = 'autorizada';""",
                {'operation_id': self.id})

    def _get_cancelled_documents_query(self):
        """
        Returns a tuple containing as its first element the SQL query used to
        gather the bills in draft state data, and the arguments
        dictionary to use to run it as its second.
        """
        # there is no account_move_lines for draft invoices, so no relevant
        # residual_signed value
        return ("""SELECT doc.company_id
                  FROM l10n_br_fiscal_document doc
                  WHERE operation_id = %(operation_id)s
                  AND state_edoc = 'cancelada';""",
                {'operation_id': self.id})

    @api.multi
    def action_create_new(self):
        ctx = self._context.copy()
        model = 'l10n_br_fiscal.document'
        if self.fiscal_type == 'sale':
            ctx.update({'default_operation_type': 'out',
                        'default_operation_id': self.id})
        elif self.fiscal_type == 'purchase':
            ctx.update({'default_operation_type': 'in',
                        'default_operation_id': self.id})
        return {
            'name': _('Create invoice/bill'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': model,
            'view_id': self.env.ref('l10n_br_fiscal.document_form').id,
            'context': ctx,
        }

    @api.multi
    def open_action(self):
        """return action based on type for related journals"""

        _fiscal_type_map = {
            'purchase': 'in',
            'purchase_refund': 'in',
            'return_in': 'in',
            'sale': 'out',
            'sale_refund': 'out',
            'return_out': 'out',
            'other': 'out',
        }
        operation_type = _fiscal_type_map[self.fiscal_type]

        action_name = self._context.get('action_name', False)

        if not action_name:
            action_name = 'document_out_action' if operation_type == 'out' \
                else 'document_in_action'

        ctx = self._context.copy()
        ctx.pop('group_by', None)
        ctx.update({
            'default_operation_type': operation_type,
        })

        [action] = self.env.ref('l10n_br_fiscal.%s' % action_name).read()
        action['context'] = ctx
        action['domain'] = self._context.get('use_domain', [])
        action['domain'] += [
            ('operation_id.fiscal_type', '=', self.fiscal_type),
            ('operation_id', '=', self.id)
        ]
        if ctx.get('search_default_confirm'):
            action['domain'] += [('state_edoc', '=', 'a_enviar')]
        elif ctx.get('search_default_authorized'):
            action['domain'] += [('state_edoc', '=', 'autorizada')]
        return action
