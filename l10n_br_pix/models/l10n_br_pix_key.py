# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class L10nBrPixKey(models.Model):

    _name = 'l10n_br_pix.key'
    _description = 'Pix Key'

    name = fields.Char(
        string='Name',
        required=True,
    )
    active = fields.Boolean(
        string='Active',
    )
    pix_key_type = fields.Selection(
        string='Pix Key Type',
        selection=[
            ('cnpj_cpf', 'CNPJ/CPF'),
            ('phone', 'Phone'),
            ('email', 'Email'),
            ('other', 'Other'),
        ]
    )
    pix_key = fields.Text(
        string='Pix Key',
        required=True,
    )
    pix_config_id = fields.Many2one(
        string='Config',
        comodel_name='l10n_br_pix.config',
        required=True,
    )
    journal_id = fields.Many2one(
        string='Bank',
        related='pix_config_id.journal_id',
        comodel_name='account.journal',
        domain=[('type', '=', 'bank')],
        store=True,
        readonly=True,
        required=True,
    )
