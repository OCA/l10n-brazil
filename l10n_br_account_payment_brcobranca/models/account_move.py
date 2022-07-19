# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import json
import logging
import tempfile

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError

from ..constants.br_cobranca import get_brcobranca_api_url

logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    file_boleto_pdf_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="Boleto PDF",
        ondelete="restrict",
        copy=False,
    )

    # Usado para deixar invisivel o botão
    # Imprimir Boleto, quando não for o caso
    payment_method_code = fields.Char(related="payment_mode_id.payment_method_id.code")

    def gera_boleto_pdf(self):
        file_pdf = self.file_boleto_pdf_id
        self.file_boleto_pdf_id = False
        file_pdf.unlink()

        receivable_ids = self.mapped("financial_move_line_ids")

        boletos = receivable_ids.send_payment()
        if not boletos:
            raise UserError(
                _(
                    "It is not possible generated boletos\n"
                    "Make sure the Invoice are in Confirm state and "
                    "Payment Mode method are CNAB."
                )
            )

        pdf_string = self._get_brcobranca_boleto(boletos)

        inv_number = self.get_invoice_fiscal_number().split("/")[-1].zfill(8)
        file_name = "boleto_nf-" + inv_number + ".pdf"

        self.file_boleto_pdf_id = self.env["ir.attachment"].create(
            {
                "name": file_name,
                "store_fname": file_name,
                "res_model": self._name,
                "res_id": self.id,
                "datas": base64.b64encode(pdf_string),
                "mimetype": "application/pdf",
                "type": "binary",
            }
        )

    def _get_brcobranca_boleto(self, boletos):

        content = json.dumps(boletos)
        f = open(tempfile.mktemp(), "w")
        f.write(content)
        f.close()
        files = {"data": open(f.name, "rb")}

        brcobranca_api_url = get_brcobranca_api_url(self.env)
        brcobranca_service_url = brcobranca_api_url + "/api/boleto/multi"
        logger.info(
            "Connecting to %s to get Boleto of invoice %s",
            brcobranca_service_url,
            self.name,
        )
        res = requests.post(brcobranca_service_url, data={"type": "pdf"}, files=files)

        if str(res.status_code)[0] == "2":
            pdf_string = res.content
        else:
            raise UserError(res.text.encode("utf-8"))

        return pdf_string

    def _target_new_tab(self, attachment_id):
        if attachment_id:
            return {
                "type": "ir.actions.act_url",
                "url": "/web/content/{id}/{nome}".format(
                    id=attachment_id.id, nome=attachment_id.name
                ),
                "target": "new",
            }

    def view_boleto_pdf(self):
        if not self.file_boleto_pdf_id:
            self.gera_boleto_pdf()
        return self._target_new_tab(self.file_boleto_pdf_id)

    def _post(self, soft=True):
        super()._post(soft)

        for line in self.line_ids:
            if line.move_id and line.cnab_returned_ref:
                # Podem existir sequencias do nosso numero/own_number iguais entre
                # bancos diferentes, porém os Diario/account.journal
                # não pode ser o mesmo.
                # IMPORTANTE: No parser estou definindo o CNAB_RETURNED_REF do
                # que não quero usar aqui com account_move_line.document_number
                line_to_reconcile = self.env["account.move.line"].search(
                    [
                        ("own_number", "=", line.cnab_returned_ref),
                        ("journal_payment_mode_id", "=", self.journal_id.id),
                    ]
                )
                # Vincula a última Ordem de Debito enviada
                order_ids = line_to_reconcile.payment_line_ids.mapped("order_id")
                for order in order_ids:
                    for pay_line in order.payment_line_ids:
                        if pay_line.move_line_id == line_to_reconcile:
                            order.move_ids |= line.move_id

                # Conciliação Automatica entre a Linha da Fatura e a Linha criada
                if self.journal_id.return_auto_reconcile:
                    if line_to_reconcile:
                        (line + line_to_reconcile).reconcile()
                        line_to_reconcile.cnab_state = "done"
                        line_to_reconcile.payment_situation = "liquidada"
