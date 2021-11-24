# Copyright (C) 2020 - Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo.exceptions import UserError

from odoo import api, models, fields, _

_logger = logging.getLogger(__name__)

try:
    from febraban.cnab240.statement import StatementParser
except ImportError:
    _logger.debug("febraban python not found.")
    StatementParser = None


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    @api.model
    def _check_cnab(self, data_file):
        if not StatementParser:
            return False
        try:
            cnab = StatementParser.parseText(data_file.decode())
        except Exception as e:
            _logger.debug(e)
            return False
        return cnab

    @api.model
    def _prepare_cnab_transaction_line(self, line):
        name = line.occurrenceText()
        if line.bank_history_code:
            name += " " + line.bank_history_code
        if line.bank_history_description:
            name += " : " + line.bank_history_description
        if line.document_number:
            name += " : " + line.document_number

        date = (
            line.date_account[-4:] + '-' +
            line.date_account[2:4] + '-' +
            line.date_account[0:2]
        )

        vals = {
            'date': fields.Date.to_date(date),
            'name': name,
            'amount': float(line.amount),
            # 'ref': Can other banks send more data?
            # 'unique_import_id':
        }
        return vals

    def _parse_file(self, data_file):
        cnab = self._check_cnab(data_file)
        if not cnab:
            return super()._parse_file(data_file)

        transactions = []
        try:
            for transaction in cnab.lines:
                vals = self._prepare_cnab_transaction_line(transaction)
                if vals:
                    transactions.append(vals)
        except Exception as e:
            raise UserError(_(
                "The following problem occurred during import. "
                "The file might not be valid.\n\n %s") % e.message)

        vals_bank_statement = {
            'name': cnab.account_number,
            'transactions': transactions,
            'balance_start': int(cnab.start_amount_in_cents) / 100,
            'balance_end_real': int(cnab.stop_amount_in_cents) / 100,
        }
        return cnab.currency, cnab.account_number.strip("0"), [vals_bank_statement]
