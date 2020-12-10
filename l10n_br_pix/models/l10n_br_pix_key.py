# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class L10nBrPixKey(models.Model):

    _name = 'l10n_br_pix.key'
    _description = 'Pix Key'

    @api.depends('pix_key')
    def _compute_qr_code(self):
        for record in self:
            if not record.pix_key:
                continue
            try:
                record.qr_code = base64.b64encode(self.env['ir.actions.report'].barcode(
                    'QR',
                    record.pix_key,
                    width='300',
                    height='300',
                ))
            except Exception:
                raise UserError(_('Error when gereration QRCODE'))

    name = fields.Char(
        string='Name',
        required=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        required=True,
    )
    pix_key_type = fields.Selection(
        string='Pix Key Type',
        selection=[
            ('cnpj_cpf', 'CNPJ/CPF'),
            ('phone', 'Phone'),
            ('email', 'Email'),
            ('random', 'Random'),
        ]
    )
    pix_key = fields.Text(
        string='Pix Key',
        required=True,
    )
    pix_config_id = fields.Many2one(
        string='Config',
        comodel_name='l10n_br_pix.config',
    )
    journal_id = fields.Many2one(
        string='Bank',
        comodel_name='account.journal',
        domain=[('type', '=', 'bank')],
        store=True,
        readonly=True,
    )
    qr_code = fields.Binary(
        string='QR Code',
        compute='_compute_qr_code',
        store=True,
        readonly=True,
    )

    # TODO:
    #   Owner of the key;
    #   Multi Company;
