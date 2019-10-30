# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import unicode_literals

from odoo import api, fields, models, _


class L10nBrAccountDocumentEventWizard(models.TransientModel):

    _name = b'l10n_br_account.document_event.wizard'

    mensagem = fields.Text(
        'Mensagem',
        required=True
    )
    # FIXME: Buscar os dados através de uma constante do
    #   l10n_br_account.document_event
    event_type = fields.Selection(
        selection=[('-1', u'Exception'),
                   ('0', u'Envio Lote'),
                   ('1', u'Consulta Recibo'),
                   ('2', u'Cancelamento'),
                   ('3', u'Inutilização'),
                   ('4', u'Consulta NFE'),
                   ('5', u'Consulta Situação'),
                   ('6', u'Consulta Cadastro'),
                   ('7', u'DPEC Recepção'),
                   ('8', u'DPEC Consulta'),
                   ('9', u'Recepção Evento'),
                   ('10', u'Download'),
                   ('11', u'Consulta Destinadas'),
                   ('12', u'Distribuição DFe'),
                   ('13', u'Manifestação')],
        string='Selection',
    )

    def evento_cancelamento(self):
        pass

    def evento_inutilizacao(self):
        pass

    @api.multi
    def doit(self):
        for wizard in self:
            if wizard.event_type == '2':
                wizard.evento_cancelamento()
            elif wizard.event_type == '3':
                wizard.evento_inutilizacao()
        return True
