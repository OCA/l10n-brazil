# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2016 Trustcode - www.trustcode.com.br                         #
#              Danimar Ribeiro <danimaribeiro@gmail.com>                      #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
###############################################################################

from mock import patch
from odoo.tests import common


class TestNfeMde(common.TransactionCase):

    def setUp(self):
        super(TestNfeMde, self).setUp()
        self.mde = self.env['nfe.mde'].create(
            {'company_id': 1, 'chNFe': '123'})

    @patch('openerp.addons.nfe_mde.nfe_mde.send_event')
    @patch('openerp.addons.nfe_mde.nfe_mde.validate_nfe_configuration')
    def test_action_known_emission(self, validate, send_event):
        validate.return_value = True
        send_event.return_value = {'file_returned': 'file.xml',
                                   'code': '135', 'message': 'Sucesso'}

        self.mde.action_known_emission()

        self.assertEqual(self.mde.state, 'ciente', 'Estado do mde inválido')
        self.assertEqual(len(self.mde.document_event_ids), 1,
                         'Nenhum documento criado')

        send_event.return_value = {'file_returned': 'file.xml',
                                   'code': '100', 'message': 'Erro'}

        self.mde.action_known_emission()
        self.assertEqual(len(self.mde.document_event_ids), 2,
                         'Nenhum documento criado')
        self.assertEqual(self.mde.document_event_ids[1].status, '100',
                         'Estado do mde inválido')
