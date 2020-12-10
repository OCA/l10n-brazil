# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class L10n_br_pixConfig(models.Model):

    _name = 'l10n_br_pix.config'
    _description = 'Pix Configuration'

    @api.depends('environment', 'test_endpoint', 'production_endpoint')
    def _compute_endpoint(self):
        for record in self:
            if record.environment == 'prod':
                record.endpoint = record.production_endpoint
            else:
                record.endpoint = record.test_endpoint

    name = fields.Char(
        string='Name'
    )
    active = fields.Boolean(
        string='Active'
    )
    journal_id = fields.Many2one(
        string='Bank',
        comodel_name='account.journal',
        domain=[('type', '=', 'bank')],
    )
    pix_key_ids = fields.One2many(
        string='Keys',
        comodel_name='l10n_br_pix.key',
        inverse_name='pix_config_id',
    )
    pix_auth_cert = fields.Binary(
        string='Pix Certificate'
    )
    pix_auth_key = fields.Binary(
        string='Pix Key'
    )
    environment = fields.Selection(
        selection=[
            ('test', 'Test'),
            ('prod', 'Production')
        ],
        string='Environment',
        default='test',
        required=True
    )
    production_endpoint = fields.Char(
        string='Production Endpoint',
    )
    test_endpoint = fields.Char(
        string='Test Endpoint',
    )
    endpoint = fields.Char(
        compute='_compute_endpoint',
        string='Endpoint',
        readonly=True,
        store=True,
    )
