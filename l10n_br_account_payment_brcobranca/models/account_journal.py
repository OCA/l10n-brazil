# @ 2020 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import os
import sys
import traceback

from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.account_move_base_import.parser.parser import new_move_parser


class AccountJournal(models.Model):
    _inherit = "account.journal"

    import_type = fields.Selection(
        selection_add=[("cnab400", "CNAB 400"), ("cnab240", "CNAB 240")]
    )

    return_auto_reconcile = fields.Boolean(
        string="Automatic Reconcile payment returns",
        help="Enable automatic payment return reconciliation.",
        default=False,
    )

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

        move_line_obj = self.env["account.move.line"]

        for line in move.line_ids:
            if line.invoice_id:
                # Pesquisando pelo Nosso Numero e Invoice evito o problema
                # de existirem move lines com o mesmo valor no campo
                # nosso numero, que pode acontecer qdo existem mais de um banco
                # configurado para gerar Boletos
                # IMPORTANTE: No parser estou definindo o REF do que não quero
                # usar aqui com account_move_line.document_number
                line_to_reconcile = move_line_obj.search(
                    [
                        ("own_number", "=", line.ref),
                        ("invoice_id", "=", line.invoice_id.id),
                    ]
                )

                # Conciliação Automatica entre a Linha da Fatura e a Linha criada
                if self.return_auto_reconcile:
                    if line_to_reconcile:
                        (line + line_to_reconcile).reconcile()
                        line_to_reconcile.cnab_state = "done"
                        line_to_reconcile.payment_situation = "liquidada"

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
        res_cnab_log = self.env["l10n_br_cnab.return.log"]
        for result_row_list in parser.parse(file_stream):
            result = self._move_import(
                parser,
                file_stream,
                result_row_list=result_row_list,
                ftype=ftype,
            )

            if len(result) > 1 or hasattr(result, "journal_id"):
                res_move |= result
            if hasattr(result, "filename"):
                res_cnab_log |= result
        if res_move:
            return res_move
        else:
            return res_cnab_log

    def _move_import(self, parser, file_stream, result_row_list=None, ftype="csv"):

        # Overwrite this method to create the CNAB Return Log and change
        # the warning message when the file don't has any line to create
        # the Journal Entry, because in CNAB exist the case where
        # the file just has only Log information.

        # Call super when file is not CNAB
        if ftype == "csv":
            super()._move_import(parser, file_stream, result_row_list=None, ftype="csv")

        attachment_obj = self.env["ir.attachment"]
        if result_row_list is None:
            result_row_list = parser.result_row_list

        # Original Method
        # Check all key are present in account.bank.statement.line!!
        # if not result_row_list:
        #    raise UserError(_("Nothing to import: " "The file is empty"))
        if not result_row_list and not parser.cnab_return_events:
            raise UserError(_("Nothing to import: " "The file is empty"))

        # Creation of CNAB Return Log
        cnab_return_log, file_name = self._create_cnab_return_log(parser)

        attachment_data = {
            "name": file_name,
            "datas": file_stream,
            "datas_fname": file_name,
            "res_model": "l10n_br_cnab.return.log",
            "res_id": cnab_return_log.id,
        }
        attachment_obj.create(attachment_data)

        if not result_row_list:
            return cnab_return_log

        moves = self._get_moves(parser, result_row_list)

        cnab_return_log.move_ids = moves.ids
        for move in moves:
            # CNAB Return Log
            move.cnab_return_log_id = cnab_return_log.id
            # Lançamento Automatico do Diário
            if self.return_auto_reconcile:
                move.post()

        return moves

    def _create_cnab_return_log(self, parser):
        context = self.env.context
        cnab_return_log = self.env["l10n_br_cnab.return.log"].create(
            {
                "name": "Banco "
                + parser.bank.short_name
                + " - Conta "
                + parser.journal.bank_account_id.acc_number,
                "filename": context.get("file_name"),
                "cnab_date_import": fields.Datetime.now(),
                "bank_account_id": parser.journal.bank_account_id.id,
            }
        )
        qty_cnab_return_events = (
            amount_total_title
        ) = (
            amount_total_received
        ) = (
            amount_total_tariff_charge
        ) = (
            amount_total_interest_fee
        ) = amount_total_discount = amount_total_rebate = 0.0

        for cnab_return_event in parser.cnab_return_events:
            amount_total_title += cnab_return_event.get("title_value")
            if cnab_return_event.get("payment_value"):
                amount_total_received += cnab_return_event.get("payment_value")
            if cnab_return_event.get("tariff_charge"):
                amount_total_tariff_charge += cnab_return_event.get("tariff_charge")
            if cnab_return_event.get("rebate_value"):
                amount_total_rebate += cnab_return_event.get("rebate_value")
            if cnab_return_event.get("discount_value"):
                amount_total_discount += cnab_return_event.get("discount_value")
            if cnab_return_event.get("interest_fee_value"):
                amount_total_interest_fee += cnab_return_event.get("interest_fee_value")
            cnab_return_event["cnab_return_log_id"] = cnab_return_log.id
            self.env["l10n_br_cnab.return.event"].create(cnab_return_event)
            qty_cnab_return_events += 1

        cnab_return_log.number_events = qty_cnab_return_events
        cnab_return_log.amount_total_title = amount_total_title
        cnab_return_log.amount_total_received = amount_total_received
        cnab_return_log.amount_total_tariff_charge = amount_total_tariff_charge
        cnab_return_log.amount_total_interest_fee = amount_total_interest_fee
        cnab_return_log.amount_total_discount = amount_total_discount
        cnab_return_log.amount_total_rebate = amount_total_rebate

        return cnab_return_log, context.get("file_name")

    def _get_moves(self, parser, result_row_list):
        move_obj = self.env["account.move"]
        move_line_obj = self.env["account.move.line"]
        moves = self.env["account.move"]
        # Cada retorno precisa ser feito um único account.move para que o campo
        # Date tanto da account.move quanto o account.move.line tenha o mesmo
        # valor e sejam referentes a Data de Credito daquele lançamento
        # especifico.
        for result_row in result_row_list:
            parsed_cols = list(parser.get_move_line_vals(result_row[0]).keys())
            for col in parsed_cols:
                if col not in move_line_obj._fields:
                    raise UserError(
                        _(
                            "Missing column! Column %s you try to import is not "
                            "present in the move line!"
                        )
                        % col
                    )

            move_vals = self.prepare_move_vals(result_row, parser)

            # O campo referente a Data de Credito no account.move é o date que
            # no account.move.line existe um related desse campo a forma de
            # obter e preencher ele por enquanto e feito da forma abaixo,
            # verificar se possível melhorar isso.
            data_credito = ""
            for row in result_row:
                if row.get("type") == "liquidado":
                    data_credito = row.get("date")
                    break
            move_vals["date"] = data_credito

            move = move_obj.create(move_vals)
            moves |= move
            try:
                # Record every line in the bank statement
                move_store = []
                for line in result_row:
                    parser_vals = parser.get_move_line_vals(line)
                    values = self.prepare_move_line_vals(parser_vals, move)
                    move_store.append(values)
                move_line_obj.with_context(check_move_validity=False).create(move_store)
                self._write_extra_move_lines(parser, move)
                if self.create_counterpart:
                    self._create_counterpart(parser, move)
                # Check if move is balanced
                move.assert_balanced()
                # Computed total amount of the move
                move._amount_compute()
                # No caso do CNAB o arquivo usado está sendo armazenado no
                # objeto l10n_br_cnab.return.log já que um arquivo pode gerar
                # diversos account.move
                # Attach data to the move
                # attachment_data = {
                #    "name": "statement file",
                #    "datas": file_stream,
                #    "datas_fname": "%s.%s" % (fields.Date.today(), ftype),
                #    "res_model": "account.move",
                #    "res_id": move.id,
                # }
                # attachment_obj.create(attachment_data)
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
                    _("Statement import error " "The statement cannot be created: %s")
                    % st
                )

        return moves
