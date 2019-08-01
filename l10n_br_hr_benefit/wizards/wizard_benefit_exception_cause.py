# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import unicode_literals, division, print_function

from openerp import api, fields, models
from openerp.exceptions import Warning


class WizardBenefitExceptionCause(models.TransientModel):
    _name = b'wizard.benefit.exception.cause'

    # benefit_line_id = fields.Many2one(
    #     comodel_name='hr.contract.benefit.line',
    # )
    message = fields.Text(
        string='Motivo da rejeição',
        required=True
    )

    @api.one
    def reject_add_message(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        if not active_ids or not active_model:
            raise Warning('Aconteceu algo de errado')
        record = self.env[active_model].browse(active_ids)
        record.exception_message = self.message
        record.state = 'exception'
