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

from document import ElectronicDocument


class DefaultEdoc(ElectronicDocument):
    def __init__(self, edoc_list, edoc_name, *args, **kwargs):
        super(DefaultEdoc, self).__init__(
            edoc_list, edoc_name,
            **kwargs)
        self.support_multi_send = True

    @classmethod
    def edoc_type(cls, edoc_name):
        """Override this method for every new parser, so that
        new_bank_statement_parser can return the good class from his name.
        """
        return edoc_name == 'default'

    def _check(self, *args, **kwargs):
        """Implement a method in your parser  to validate the
        self.result_row_list instance property and raise an error if not valid.
        """
        return True

    def _serializer(self, *args, **kwargs):
        """Implement a method in your parser to save the result of parsing
        self.filebuffer in self.result_row_list instance property.
        """
        return True

    # def _send(self, *args, **kwargs):
    #     """Implement a method in your parser to make some last changes on the
    #     result of parsing the datas, like converting dates, computing
    #     commission, ...
    #     """
    #     self.result_row_list = True

    def validate(self, *args, **kwargs):
        """Implement a method in your parser to make some last changes on the
        result of parsing the datas, like converting dates, computing
        commission, ...
        """
        return False
