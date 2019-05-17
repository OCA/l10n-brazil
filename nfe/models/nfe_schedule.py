# -*- coding: utf-8 -*-
# Copyright (C) 2015 Trustcode - www.trustcode.com.br
#              Danimar Ribeiro <danimaribeiro@gmail.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api, fields


class NfeSchedule(models.TransientModel):
    _name = 'nfe.schedule'

    state = fields.Selection(
        string="Estado",
        selection=[('init', 'Não iniciado'), ('done', 'Finalizado')],
        default='init'
    )

    @api.model
    def schedule_download(self, raise_error=False, domain=()):
        companies = self.env['res.company'].search([
            ('nfe_a1_file', '!=', False)
        ])
        return companies.query_nfe_batch(raise_error=raise_error)

    @api.multi
    def execute_download(self):
        for record in self:
            record.schedule_download(raise_error=True)
