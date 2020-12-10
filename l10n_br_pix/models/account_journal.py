# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class AccountJournal(models.Model):

    _inherit = 'account.journal'

    pix_qr_type = fields.Selection(
        string='Type of PIX QR Code',
        selection=[
            ('payer', 'Payer'),  # QRCODE é exibido pelo estabelecimento para o cliente
            ('receiver', 'Receiver'),  # QRCODE do cliente é lido pelo estabelecimento
        ],
        # A documentação da API do QR Recebedor ainda não foi lançada.
    )
