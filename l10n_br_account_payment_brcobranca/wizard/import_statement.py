# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
import os


class CreditPartnerStatementImporter(models.TransientModel):
    _inherit = 'credit.statement.import'

    @api.multi
    def import_statement(self):
        """This Function import credit card agency statement"""
        moves = self.env['account.move']
        cnab_logs = self.env['cnab.return.log']
        for importer in self:
            journal = importer.journal_id
            ftype = importer._check_extension()
            result = journal.with_context(
                file_name=importer.file_name).multi_move_import(
                importer.input_statement,
                ftype.replace('.', '')
            )
            print('result === import statement ==>', result)
            if hasattr(result, 'journal_id'):
                print('result === import statement == if>', result)
                moves |= result
            if hasattr(result, 'cnab_date'):
                cnab_logs |= result

        print('MOVES', moves)
        if moves:
            xmlid = ('account', 'action_move_journal_line')
            action = self.env['ir.actions.act_window'].for_xml_id(*xmlid)
            if len(moves) > 1:
                action['domain'] = [('id', 'in', moves.ids)]
            else:
                ref = self.env.ref('account.view_move_form')
                action['views'] = [(ref.id, 'form')]
                action['res_id'] = moves.id if moves else False
            return action
        else:
            xmlid = ('l10n_br_account_payment_brcobranca', 'cnab_return_log_action')
            action = self.env['ir.actions.act_window'].for_xml_id(*xmlid)
            if len(cnab_logs) > 1:
                action['domain'] = [('id', 'in', cnab_logs.id)]
            ref = self.env.ref(
                'l10n_br_account_payment_brcobranca.cnab_return_log_form_view')
            action['views'] = [(ref.id, 'form')]
            action['res_id'] = cnab_logs.id if cnab_logs else False
            return action
