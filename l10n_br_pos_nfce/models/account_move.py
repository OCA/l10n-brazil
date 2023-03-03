# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import locale
import logging

from odoo import models

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.edoc.nfce import ESTADO_CONSULTA_NFCE, ESTADO_QRCODE
except ImportError:
    _logger.error("Biblioteca erpbrasil.edoc não instalada")


FISCAL_PAYMENT_MODE = {
    "01": "Dinheiro",
    "02": "Cheque",
    "03": "Cartão de Crédito",
    "04": "Cartão de Débito",
    "05": "Crédito de Loja",
    "10": "Vale Alimentação",
    "11": "Vale Refeição",
    "12": "Vale Presente",
    "13": "Vale Combustível",
    "14": "Duplicata Mercanti",
    "15": "Boleto Bancário",
    "16": "Depósito Bancário",
    "17": "Pagamento Instantâneo (PIX)",
    "18": "Transferência bancária, Carteira Digital",
    "19": "Programa de fidelidade, Cashback, Crédito Virtual",
    "90": "Sem Pagamento",
    "99": "Outros",
}

NFCE_AMBIENTE_PRODUCAO = "1"
NFCE_AMBIENTE_HOMOLOGACAO = "2"

SIGLA_ESTADO = {
    "12": "AC",
    "27": "AL",
    "13": "AM",
    "16": "AP",
    "29": "BA",
    "23": "CE",
    "53": "DF",
    "32": "ES",
    "52": "GO",
    "21": "MA",
    "31": "MG",
    "50": "MS",
    "51": "MT",
    "15": "PA",
    "25": "PB",
    "26": "PE",
    "22": "PI",
    "41": "PR",
    "33": "RJ",
    "24": "RN",
    "11": "RO",
    "14": "RR",
    "43": "RS",
    "42": "SC",
    "28": "SE",
    "35": "SP",
    "17": "TO",
    "91": "AN",
}


class AccountMove(models.Model):

    _inherit = "account.move"

    def view_pdf(self):
        self.ensure_one()
        if self.document_type != "65":
            return super(AccountMove, self).view_pdf()
        else:
            report_name = "l10n_br_pos_nfce.report_danfe_nfce"
            data = self._prepare_nfce_danfe_values()
            return (
                self.env["ir.actions.report"]
                .search(
                    [("report_name", "=", report_name)],
                    limit=1,
                )
                .report_action(self, data=data)
            )

    def _prepare_nfce_danfe_values(self):
        locale.setlocale(locale.LC_MONETARY, "pt_BR.utf8")
        return {
            "company_cnpj": self.company_cnpj_cpf,
            "company_legal_name": self.company_legal_name,
            "company_street": self.company_street,
            "company_number": self.company_number,
            "company_district": self.company_district,
            "company_city": self.company_city_id.display_name,
            "company_state": self.company_state_id.name,
            "lines": self._prepare_nfce_danfe_line_values(),
            "total_product_quantity": len(
                self.line_ids.filtered(lambda line: line.product_id)
            ),
            "amount_total": locale.currency(self.amount_total),
            "amount_discount_value": locale.currency(self.amount_discount_value),
            "amount_freight_value": locale.currency(self.amount_freight_value),
            "payments": self._prepare_nfce_danfe_payment_values(),
            "amount_change": locale.currency(self.nfe40_vTroco),
            "nfce_url": self.estado_de_consulta_da_nfce(),
            "document_key": self.document_key,
            "document_number": self.document_number.zfill(9),
            "document_serie": self.document_serie.zfill(3),
            "document_date": self.document_date.astimezone().strftime(
                "%d/%m/%y %H:%M:%S"
            ),
            "authorization_protocol": self.authorization_protocol,
            "document_qrcode": self._monta_qrcode(),
            "system_env": self.nfe40_tpAmb,
            "unformatted_amount_freight_value": self.amount_freight_value,
            "unformatted_amount_discount_value": self.amount_discount_value,
        }

    def _prepare_nfce_danfe_line_values(self):
        lines_list = []
        lines = self.line_ids.filtered(lambda line: line.product_id)
        for line in lines:
            product_id = line.product_id
            vals = {
                "product_default_code": product_id.default_code,
                "product_name": product_id.name,
                "product_quantity": line.quantity,
                "product_uom": product_id.uom_name,
                "product_unit_value": locale.currency(product_id.lst_price),
                "product_unit_total": locale.currency(
                    line.quantity * product_id.lst_price
                ),
            }
            lines_list.append(vals)
        return lines_list

    def _prepare_nfce_danfe_payment_values(self):
        payments_list = []
        payments = self.nfe40_detPag
        for payment in payments:
            vals = {
                "method": FISCAL_PAYMENT_MODE[payment.nfe40_tPag],
                "value": locale.currency(payment.nfe40_vPag),
            }
            payments_list.append(vals)
        return payments_list

    def _monta_qrcode(self):
        import hashlib

        nfce_chave = self.document_key
        pre_qrcode = "{}|{}|{}|{}".format(
            nfce_chave,
            self.company_id.nfce_qrcode_version,
            self.nfe40_tpAmb,
            self.company_id.nfce_csc_token,
        )
        pre_qrcode_with_csc = pre_qrcode + f"{self.company_id.nfce_csc_code}"
        hash_object = hashlib.sha1(bytes(pre_qrcode_with_csc, "utf-8"))
        qr_hash = hash_object.hexdigest().upper()
        return (
            f"{ESTADO_QRCODE[SIGLA_ESTADO[self.company_state_id.ibge_code]][self.nfe40_tpAmb]}"
            + pre_qrcode
            + f"|{qr_hash}"
        )

    def estado_de_consulta_da_nfce(self):
        return ESTADO_CONSULTA_NFCE[SIGLA_ESTADO[self.company_state_id.ibge_code]][
            self.nfe40_tpAmb
        ]
