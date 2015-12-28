# -*- coding: utf-8 -*-
"""Add process_camt method to account.bank.statement.import."""
##############################################################################
#
#    Copyright (C) 2013-2015 Therp BV <http://therp.nl>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
import StringIO
from openerp import api, models
from .file_cnab240_parser import Cnab240Parser as cnabparser


_logger = logging.getLogger(__name__)


class AccountBankStatementImport(models.TransientModel):
    """  """
    _inherit = 'account.bank.statement.import'

    @api.model
    def _check_cnab(self, data_file):
        if cnabparser is None:
            return False
        try:
            cnab_file = cnabparser.parse(StringIO.StringIO(data_file))
        except:
            return False
        return cnab_file

    @api.model
    def _find_bank_account_id(self, account_number):
        """ Get res.partner.bank ID """
        bank_account_id = None
        if account_number:
            bank_account_ids = self.env['res.partner.bank'].search(
                [('acc_number', '=', str(account_number))], limit=1)
            if bank_account_ids:
                bank_account_id = bank_account_ids[0].id
        return bank_account_id

    def _parse_file(self, cr, uid, data_file, context=None):
        """Parse a CNAB file."""
        parser = cnabparser()
        try:
            _logger.debug("Try parsing with CNAB.")
            return parser.parse(data_file)
        except ValueError:
            # Not a CNAB file, returning super will call next candidate:
            _logger.debug("Statement file was not a CNAB  file.",
                          exc_info=True)
            return super(AccountBankStatementImport, self)._parse_file(
                cr, uid, data_file, context=context)
