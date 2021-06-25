# Copyright 2021 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime

from .arquivo_certificado import ArquivoCertificado
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.bank.inter.boleto import BoletoInter
    from erpbrasil.bank.inter.api import ApiInter
except ImportError:
    _logger.error("Biblioteca erpbrasil.bank.inter não instalada")

BAIXAS = [
    ('acertos', 'Acertos'),
    ('protestado', 'Protestado'),
    ('devolucao', 'Devolução'),
    ('protestoaposbaixa', 'Protesto após baixa'),
    ('pagodiretoaocliente', 'Pago direto ao cliente'),
    ('substituicao', 'Substituição'),
    ('faltadesolucao', 'Falta de solução'),
    ('apedidodocliente', 'A pedido do cliente'),
]

class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    pdf_boleto_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='PDF Boleto',
        ondelete='cascade'
    )

    write_off_choice = fields.Selection(
        selection=BAIXAS,
        string='Drop Bank Slip Options',
        default='apedidodocliente',
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

    def drop_bank_slip(self):
        try:
            if self.write_off_choice:
                codigo_baixa = self.write_off_choice.upper()
            else:
                codigo_baixa = "APEDIDODOCLIENTE"
            order_id = self.payment_line_ids.order_id
            if self.own_number:
                with ArquivoCertificado(order_id.journal_id, 'w') as (key, cert):
                    self.api = ApiInter(
                        cert=(cert, key),
                        conta_corrente=(
                            order_id.company_partner_bank_id.acc_number +
                            order_id.company_partner_bank_id.acc_number_dig
                        )
                    )
                    self.api.boleto_baixa(self.own_number, codigo_baixa)
        except Exception as error:
            raise UserError(_(error))

    def search_bank_slip(self):
        try:
            for order in self.payment_line_ids:
                with ArquivoCertificado(order.order_id.journal_id, 'w') as (key, cert):
                    self.api = ApiInter(
                        cert=(cert, key),
                        conta_corrente=(
                            order.order_id.company_partner_bank_id.acc_number +
                            order.order_id.company_partner_bank_id.acc_number_dig
                        )
                    )
                    resultado = self.api.boleto_consulta(nosso_numero = self.own_number)
                    # self.update_data(resultado)
        except Exception as error:
            raise UserError(_(error))

    def update_data(self, resultado):
        pass
        # if resultado:
        #     date = datetime.strptime(resultado['dataVencimento'], '%d/%m/%Y').date()
        #     self.date_maturity = date
        #     self.debit = resultado['valorNominal']
