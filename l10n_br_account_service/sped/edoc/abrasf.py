# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2015 - Luis Felipe Mileo - www.kmee.com.br                    #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################


from openerp.addons.l10n_br_account.sped.edoc.document import Edoc


class Abrasf(Edoc):

    @classmethod
    def edoc_type(cls, edoc_name):
        """Override this method for every new parser, so that
        new_bank_statement_parser can return the good class from his name.
        """
        return edoc_name == 'abrasf'


    def _serializer(self, *args, **kwargs):
        """Implement a method in your parser to save the result of parsing
        self.filebuffer in self.result_row_list instance property.
        """
        return NotImplementedError


    def validate(self, *args, **kwargs):
        """Implement a method in your parser  to validate the
        self.result_row_list instance property and raise an error if not valid.
        """
        return True


    def _send(self, *args, **kwargs):
        """Implement a method in your parser to make some last changes on the
        result of parsing the datas, like converting dates, computing
        commission, ...
        """
        return NotImplementedError


    def send(self, *args, **kwargs):
        """This will be the method that will be called by wizard, button and so
        to parse a filebuffer by calling successively all the private method
        that need to be define for each parser.
        Return:
             [] of rows as {'key':value}
        Note: The row_list must contain only value that are present in the
        account.bank.statement.line object !!!
        """
        self._format(*args, **kwargs)
        self._pre(*args, **kwargs)
        if self.support_multi_send:
            while self._serializer(*args, **kwargs):
                self.validate(*args, **kwargs)
                self._send(*args, **kwargs)
                yield self.result_row_list
        else:
            self._serializer(*args, **kwargs)
            self.validate(*args, **kwargs)
            self._send(*args, **kwargs)
            yield self.result_row_list

    def report(self, *args, **kwargs):

        return NotImplementedError