# @ 2020 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import sys
import os
import traceback
from datetime import datetime

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.account_move_base_import.parser.parser import new_move_parser


class AccountJournal(models.Model):
    _inherit = "account.journal"

    import_type = fields.Selection(
        selection_add=[('cnab400', 'CNAB 400'), ('cnab240', 'CNAB 240')]
    )

    return_auto_reconcile = fields.Boolean(
        string="Automatic Reconcile payment returns",
        help="Enable automatic payment return reconciliation.",
        default=False,
    )

    @api.multi
    def _write_extra_move_lines(self, parser, move):
        """Insert extra lines after the main statement lines.

        After the main statement lines have been created, you can override this
        method to create extra statement lines.

            :param:    browse_record of the current parser
            :param:    result_row_list: [{'key':value}]
            :param:    profile: browserecord of account.statement.profile
            :param:    statement_id: int/long of the current importing
              statement ID
            :param:    context: global context
        """

        move_line_obj = self.env['account.move.line']

        for line in move.line_ids:
            if line.invoice_id:
                # Pesquisando pelo Nosso Numero e Invoice evito o problema
                # de existirem move lines com o mesmo valor no campo
                # nosso numero, que pode acontecer qdo existem mais de um banco
                # configurado para gerar Boletos
                # IMPORTANTE: No parser estou definindo o REF do que não quero
                # usar aqui com account_move_line.document_number
                line_to_reconcile = move_line_obj.search([
                    ('own_number', '=', line.ref),
                    ('invoice_id', '=', line.invoice_id.id)
                ])

                # Conciliação Automatica entre a Linha da Fatura e a Linha criada
                if self.return_auto_reconcile:
                    if line_to_reconcile:
                        (line + line_to_reconcile).reconcile()

    def multi_move_import(self, file_stream, ftype="csv"):
        """Create multiple bank statements from values given by the parser for
        the given profile.

        :param int/long profile_id: ID of the profile used to import the file
        :param filebuffer file_stream: binary of the provided file
        :param char: ftype represent the file extension (csv by default)
        :return: list: list of ids of the created account.bank.statement
        """
        filename = self._context.get("file_name", None)
        if filename:
            (filename, __) = os.path.splitext(filename)
        parser = new_move_parser(self, ftype=ftype, move_ref=filename)
        res_move = self.env["account.move"]
        res_cnab_log = self.env['cnab.return.log']
        for result_row_list in parser.parse(file_stream):
            result = self._move_import(
                parser,
                file_stream,
                result_row_list=result_row_list,
                ftype=ftype,
            )

            if hasattr(result, 'journal_id'):
                res_move |= result
            if hasattr(result, 'cnab_date'):
                res_cnab_log |= result
        if res_move:
            return res_move
        else:
            return res_cnab_log

    def _move_import(
            self, parser, file_stream, result_row_list=None, ftype="csv"):

        # Overwrite this method to create the CNAB Return Log and change
        # the warning message when the file don't has any line to create
        # the Journal Entry, because in CNAB exist the case where
        # the file just has only Log information.

        # Call super when file is not CNAB
        if ftype == 'csv':
            super()._move_import(
                parser, file_stream, result_row_list=None, ftype="csv")

        move_obj = self.env["account.move"]
        move_line_obj = self.env["account.move.line"]
        attachment_obj = self.env["ir.attachment"]
        if result_row_list is None:
            result_row_list = parser.result_row_list

        # Original Method
        # Check all key are present in account.bank.statement.line!!
        # if not result_row_list:
        #    raise UserError(_("Nothing to import: " "The file is empty"))
        if not result_row_list and not parser.cnab_return_log_line:
            raise UserError(_("Nothing to import: " "The file is empty"))

        # Creation of CNAB Return Log
        context = self.env.context
        now_user_tz = fields.Datetime.context_timestamp(
            self, datetime.now())
        cnab_return_log = self.env['cnab.return.log'].create({
            'name': 'Retorno CNAB - ' + str(
                datetime.strftime(now_user_tz, '%d/%m/%Y - %H:%M')),
            'filename': context.get('file_name'),
        })
        qty_cnab_log_lines = 0
        amount_total_title = 0.0
        amount_total_received = 0.0
        for cnab_return_log_line in parser.cnab_return_log_line:
            amount_total_title += cnab_return_log_line.get('title_value')
            if cnab_return_log_line.get('payment_value'):
                amount_total_received += \
                    cnab_return_log_line.get('payment_value')
            cnab_return_log_line['cnab_return_log_id'] = cnab_return_log.id
            self.env['cnab.return.log.line'].create(cnab_return_log_line)
            qty_cnab_log_lines += 1

        cnab_return_log.number_events = qty_cnab_log_lines
        cnab_return_log.amount_total_title = amount_total_title
        cnab_return_log.amount_total_received = amount_total_received

        attachment_data = {
            'name': context.get('file_name'),
            'datas': file_stream,
            'datas_fname': context.get('file_name'),
            'res_model': 'cnab.return.log',
            'res_id': cnab_return_log.id,
        }
        attachment_obj.create(attachment_data)

        if not result_row_list:
            return cnab_return_log

        parsed_cols = list(
            parser.get_move_line_vals(result_row_list[0]).keys()
        )

        for col in parsed_cols:
            if col not in move_line_obj._fields:
                raise UserError(
                    _(
                        "Missing column! Column %s you try to import is not "
                        "present in the move line!"
                    )
                    % col
                )
        move_vals = self.prepare_move_vals(result_row_list, parser)
        move = move_obj.create(move_vals)
        try:
            # Record every line in the bank statement
            move_store = []
            for line in result_row_list:
                parser_vals = parser.get_move_line_vals(line)
                values = self.prepare_move_line_vals(parser_vals, move)
                move_store.append(values)
            move_line_obj.with_context(check_move_validity=False).create(
                move_store
            )
            self._write_extra_move_lines(parser, move)
            if self.create_counterpart:
                self._create_counterpart(parser, move)
            # Check if move is balanced
            move.assert_balanced()
            # Computed total amount of the move
            move._amount_compute()
            # Attach data to the move
            attachment_data = {
                "name": "statement file",
                "datas": file_stream,
                "datas_fname": "%s.%s" % (fields.Date.today(), ftype),
                "res_model": "account.move",
                "res_id": move.id,
            }
            attachment_obj.create(attachment_data)
            # If user ask to launch completion at end of import, do it!
            if self.launch_import_completion:
                move.button_auto_completion()
            # Write the needed log infos on profile
            self.write_logs_after_import(move, len(result_row_list))
        except UserError:
            # "Clean" exception, raise as such
            raise
        except Exception:
            error_type, error_value, trbk = sys.exc_info()
            st = "Error: %s\nDescription: %s\nTraceback:" % (
                error_type.__name__,
                error_value,
            )
            st += "".join(traceback.format_tb(trbk, 30))
            raise ValidationError(
                _(
                    "Statement import error "
                    "The statement cannot be created: %s"
                )
                % st
            )

        # CNAB Return Log
        move.cnab_return_log_id = cnab_return_log.id
        cnab_return_log.move_id = move.id

        # Lançamento Automatico do Diário
        if self.return_auto_reconcile:
            move.post()

        return move
