# Copyright 2021 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging
from datetime import date

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_bank_api_inter.parser.inter_file_parser import InterFileParser

from .arquivo_certificado import ArquivoCertificado

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.bank.inter.api import ApiInter
except ImportError:
    _logger.error("Biblioteca erpbrasil.bank.inter não instalada")

BAIXAS = [
    ("acertos", "Acertos"),
    ("pagodiretoaocliente", "Pago direto ao cliente"),
    ("substituicao", "Substituição"),
    ("apedidodocliente", "A pedido do cliente"),
]

ESTADO = [
    ("emaberto", "Em Aberto"),
    ("pago", "Pago"),
    ("expirado", "Expirado"),
    ("vencido", "Vencido"),
    ("baixado", "Baixado"),
    ("cancelado", "Cancelado"),
]


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    pdf_boleto_id = fields.Many2one(
        comodel_name="ir.attachment", string="PDF Boleto", ondelete="cascade"
    )

    write_off_choice = fields.Selection(
        selection=BAIXAS,
        string="Drop Bank Slip Options",
        default="apedidodocliente",
    )

    bank_inter_state = fields.Selection(
        selection=ESTADO,
        string="State",
        default="emaberto",
    )

    write_off_by_api = fields.Boolean(
        string="Slip write off by Bank Inter Api",
        default=False,
        readonly=True,
    )

    def generate_pdf_boleto(self):
        """
        Creates a new attachment with the Boleto PDF
        """
        if self.own_number and self.pdf_boleto_id:
            return

        order_id = self.payment_line_ids[0].order_id
        with ArquivoCertificado(order_id.journal_id, "w") as (key, cert):
            api = ApiInter(
                cert=(cert, key),
                conta_corrente=(
                    order_id.company_partner_bank_id.acc_number
                    + order_id.company_partner_bank_id.acc_number_dig
                ),
                client_id=self.journal_payment_mode_id.bank_client_id,
                client_secret=self.journal_payment_mode_id.bank_secret_id,
            )
            datas = api.boleto_pdf(self.own_number)
            datas_json = json.loads(datas.decode("utf-8"))
            self.pdf_boleto_id = self.env["ir.attachment"].create(
                {
                    "name": ("Boleto %s" % self.name),
                    "datas": datas_json["pdf"],
                    "type": "binary",
                    "res_id": self.id,
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
            base_url = self.env["ir.config_parameter"].get_param("web.base.url")
            download_url = "/web/content/%s/%s?download=True" % (
                str(boleto_id.id),
                boleto_id.name,
            )

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
            if self.bank_inter_state != "pago":
                if self.own_number:
                    with ArquivoCertificado(order_id.journal_id, "w") as (key, cert):
                        api = ApiInter(
                            cert=(cert, key),
                            conta_corrente=(
                                order_id.company_partner_bank_id.acc_number
                                + order_id.company_partner_bank_id.acc_number_dig
                            ),
                            client_id=self.journal_payment_mode_id.bank_client_id,
                            client_secret=self.journal_payment_mode_id.bank_secret_id,
                        )
                        api.boleto_baixa(self.own_number, codigo_baixa)
                self.bank_inter_state = "baixado"
        except Exception as error:
            raise UserError(_(error))

    def search_bank_slip(self):
        try:
            parser = InterFileParser(self.journal_payment_mode_id)
            for order in self.payment_line_ids:
                with ArquivoCertificado(order.order_id.journal_id, "w") as (key, cert):
                    api = ApiInter(
                        cert=(cert, key),
                        conta_corrente=(
                            order.order_id.company_partner_bank_id.acc_number
                            + order.order_id.company_partner_bank_id.acc_number_dig
                        ),
                        client_id=self.journal_payment_mode_id.bank_client_id,
                        client_secret=self.journal_payment_mode_id.bank_secret_id,
                    )
                    resposta = api.consulta_boleto_detalhado(
                        nosso_numero=self.own_number
                    )

                    parser.parse(resposta)

                    if resposta["situacao"].lower() != self.bank_inter_state:
                        if resposta["situacao"] == "pago":
                            move_id = self.env["account.move"].create(
                                {
                                    "date": date.today(),
                                    "ref": self.ref,
                                    "journal_id": self.journal_payment_mode_id.id,
                                    "company_id": self.company_id.id,
                                    "line_ids": [
                                        (
                                            0,
                                            0,
                                            {
                                                "account_id": self.account_id.id,
                                                "partner_id": self.partner_id.id,
                                                "debit": self.move_id.line_ids[
                                                    0
                                                ].credit,
                                                "credit": self.move_id.line_ids[
                                                    0
                                                ].debit,
                                                "date_maturity": self.date_maturity,
                                            },
                                        ),
                                        (
                                            0,
                                            0,
                                            {
                                                "account_id": self.account_id.id,
                                                "partner_id": self.company_id.id,
                                                "debit": self.move_id.line_ids[
                                                    1
                                                ].credit,
                                                "credit": self.move_id.line_ids[
                                                    1
                                                ].debit,
                                                "date_maturity": self.date_maturity,
                                            },
                                        ),
                                    ],
                                }
                            )
                            move_id.post()
                            (move_id.line_ids[0] + self).reconcile()

                        if resposta["situacao"] == "cancelado":
                            self.write_off_by_api = True
                            self.write_off_choice = resposta[
                                "motivoCancelamento"
                            ].lower()

                    self.bank_inter_state = resposta["situacao"].lower()
        except Exception as error:
            raise UserError(_(error))

    def all_search_bank_slip(self):
        try:
            move_line_ids = self.env["account.move.line"].search(
                [("bank_inter_state", "in", ["emaberto", "vencido"])]
            )
            for move_line in move_line_ids:
                move_line.search_bank_slip()
        except Exception as error:
            raise UserError(_(error))
