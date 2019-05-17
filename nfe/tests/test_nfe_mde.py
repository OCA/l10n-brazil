# -*- coding: utf-8 -*-
# # Copyright (C) 2016 Danimar Ribeiro <danimaribeiro@gmail.com>
# # License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from mock import patch
from odoo.tests import common


class TestNfeMde(common.TransactionCase):

    def setUp(self):
        super(TestNfeMde, self).setUp()
        self.mde = self.env['nfe.mde'].create(
            {'company_id': 1, 'chNFe': '123'})

    @patch('odoo.addons.nfe_mde.nfe_mde.send_event')
    @patch('odoo.addons.nfe_mde.nfe_mde.validate_nfe_configuration')
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
