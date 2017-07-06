# -*- coding: utf-8 -*-
# (c) 2017 KMEE INFORMATICA LTDA - Daniel Sadamo <daniel.sadamo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from __future__ import (
    division, print_function, unicode_literals, absolute_import
)

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError

STATE = [
    ('draft', u'Rascunho'),
    ('open', u'Confirmada'),
    ('sent', u'Enviado'),
]


class AbstractArquivosGovernoWorkflow(models.AbstractModel):
    _name = b'abstract.arquivos.governo.workflow'

    state = fields.Selection(
        selection=STATE, index=True,
        readonly=True, default='draft',
        track_visibility='onchange', copy=False
    )

    @api.model
    def _avaliable_transition(self, old_state, new_state):
        allowed = [
            ('draft', 'open'),
            ('open', 'draft'),
            ('open', 'sent'),
        ]
        return (old_state, new_state) in allowed

    @api.multi
    def change_state(self, new_state):
        for record in self:
            if record._avaliable_transition(record.state, new_state):
                record.state = new_state
            else:
                raise UserError(_("This state transition is not allowed"))

    @api.multi
    def action_draft(self):
        for record in self:
            record.change_state('draft')

    @api.multi
    def action_open(self):
        for record in self:
            record.change_state('open')

    @api.multi
    def action_sent(self):
        for record in self:
            record.change_state('sent')
