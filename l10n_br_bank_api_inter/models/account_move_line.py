# Copyright 2021 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from .arquivo_certificado import ArquivoCertificado
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.bank.inter.boleto import BoletoInter
    from erpbrasil.bank.inter.api import ApiInter
except ImportError:
    _logger.error("Biblioteca erpbrasil.bank.inter não instalada")

class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    pdf_boleto_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='PDF Boleto',
        ondelete='cascade'
    )

    def generate_pdf_boleto(self):
        """
        Creates a new attachment with the Boleto PDF
        """
        if self.own_number and self.pdf_boleto_id:
            return

        order_id = self.payment_line_ids[0].order_id
        with ArquivoCertificado(order_id.journal_id, 'w') as (key, cert):
            partner_bank_id = self.journal_id.bank_account_id
            self.api = ApiInter(
                cert=(cert, key),
                conta_corrente=(
                    order_id.company_partner_bank_id.acc_number +
                    order_id.company_partner_bank_id.acc_number_dig
                )
            )
            datas = self.api.boleto_pdf(self.own_number)
            self.pdf_boleto_id = self.env['ir.attachment'].create(
                {
                    'name': (
                        "Boleto %s" % self.bank_payment_line_id.display_name),
                    'datas': datas,
                    'datas_fname': ("boleto_%s.pdf" %
                                    self.bank_payment_line_id.display_name),
                    'type': 'binary'
                }
            )

    def print_pdf_boleto(self):
        """
        Generates and downloads Boletos PDFs
        :return: actions.act_url
        """

        self.generate_pdf_boleto()

        if self.own_number:
            boleto_id = self.pdf_boleto_id
            base_url = self.env['ir.config_parameter'].get_param(
                'web.base.url')
            download_url = '/web/content/%s/%s?download=True' % (
                str(boleto_id.id), boleto_id.name)

            return {
                "type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url),
                "target": "new",
            }
