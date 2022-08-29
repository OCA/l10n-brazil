# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br) - Fernando Marcato
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"
    # TODO: Verificar campos da NFC-e, CF-E e PAF
