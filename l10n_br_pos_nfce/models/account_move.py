# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import binascii
import hashlib
import locale
import logging
import xml.etree.ElementTree as ET

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.edoc.nfce import ESTADO_CONSULTA_NFCE, ESTADO_QRCODE, NAMESPACES
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
            "company_ie": self.company_inscr_est,
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
            "document_number": self.document_number,
            "document_serie": self.document_serie,
            "document_date": self.document_date.astimezone().strftime(
                "%d/%m/%y %H:%M:%S"
            ),
            "authorization_protocol": self.authorization_protocol,
            "document_qrcode": self._monta_qrcode(),
            "system_env": self.nfe40_tpAmb,
            "unformatted_amount_freight_value": self.amount_freight_value,
            "unformatted_amount_discount_value": self.amount_discount_value,
            "contingency": True if not self.edoc_transmission == "1" else False,
            "homologation_environment": True if self.nfe_environment == "2" else False,
        }

    def _prepare_nfce_danfe_line_values(self):
        lines_list = []
        lines = self.line_ids.filtered(lambda line: line.product_id)
        for index, line in enumerate(lines):
            product_id = line.product_id
            vals = {
                "product_index": index + 1,
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
        if self.edoc_transmission == "1":
            return self._online_qrcode()
        else:
            return self._offline_qrcode()

    def _online_qrcode(self):
        nfce_chave = self.document_key
        nfce_qrcode_version = self.company_id.nfce_qrcode_version
        nfe40_tpAmb = self.nfe40_tpAmb
        nfce_csc_token = self.company_id.nfce_csc_token
        nfce_csc_code = self.company_id.nfce_csc_code
        ibge_code = self.company_state_id.ibge_code

        pre_qrcode = (
            f"{nfce_chave}|{nfce_qrcode_version}|{nfe40_tpAmb}|{nfce_csc_token}"
        )
        pre_qrcode_with_csc = f"{pre_qrcode}{nfce_csc_code}"
        hash_object = hashlib.sha1(pre_qrcode_with_csc.encode("utf-8"))
        qr_hash = hash_object.hexdigest().upper()

        estado_qrcode = ESTADO_QRCODE[SIGLA_ESTADO[ibge_code]][nfe40_tpAmb]

        return f"{estado_qrcode}{pre_qrcode}|{qr_hash}"

    def _offline_qrcode(self):
        ibge_code = self.company_state_id.ibge_code
        processador = self.fiscal_document_id._processador()
        for edoc in self.fiscal_document_id.serialize():
            xml_assinado = processador.assina_raiz(edoc, edoc.infNFe.Id)
            xml = ET.fromstring(xml_assinado)
            chave_nfce = self.document_key
            data_emissao = edoc.infNFe.ide.dhEmi[8:10]
            total_nfe = xml.find(
                ".//nfe:total/nfe:ICMSTot/nfe:vNF", namespaces=NAMESPACES
            ).text
            digest_value = xml.find(".//ds:DigestValue", namespaces=NAMESPACES).text
            digest_value_hex = binascii.hexlify(digest_value.encode()).decode()
            pre_qrcode_witouth_csc = f"{chave_nfce}|{self.company_id.nfce_qrcode_version}|{self.nfe40_tpAmb}|{data_emissao}|{total_nfe}|{digest_value_hex}|{self.company_id.nfce_csc_token}"  # noqa: B950
            pre_qrcode = f"{chave_nfce}|{self.company_id.nfce_qrcode_version}|{self.nfe40_tpAmb}|{data_emissao}|{total_nfe}|{digest_value_hex}|{self.company_id.nfce_csc_token}{self.company_id.nfce_csc_code}"  # noqa: B950
            hash_object = hashlib.sha1(pre_qrcode.encode("utf-8"))
            qr_hash = hash_object.hexdigest().upper()

            estado_qrcode = ESTADO_QRCODE[SIGLA_ESTADO[ibge_code]][self.nfe40_tpAmb]

        return f"{estado_qrcode}{pre_qrcode_witouth_csc}|{qr_hash}"

    def estado_de_consulta_da_nfce(self):
        return ESTADO_CONSULTA_NFCE[SIGLA_ESTADO[self.company_state_id.ibge_code]][
            self.nfe40_tpAmb
        ]


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    #
    # @override
    #
    #
    # The method was overwritten due to the need for it to also accept
    #   orders that were canceled and, consequently, had their invoice
    #   state changed to 'cancel'.
    #
    # FIXME: Use the concept of inheritance to fix this.
    def reconcile(self):
        """Reconcile the current move lines all together.
        :return: A dictionary representing a summary of what has been done during the reconciliation: # noqa: B950
                * partials:             A recorset of all account.partial.reconcile created during the reconciliation. # noqa: B950
                * full_reconcile:       An account.full.reconcile record created when there is nothing left to reconcile # noqa: B950
                                        in the involved lines.
                * tax_cash_basis_moves: An account.move recordset representing the tax cash basis journal entries. # noqa: B950
        """
        results = {}

        if not self:
            return results

        # List unpaid invoices
        not_paid_invoices = self.move_id.filtered(
            lambda move: move.is_invoice(include_receipts=True)
            and move.payment_state not in ("paid", "in_payment")
        )

        # ==== Check the lines can be reconciled together ====
        company = None
        account = None
        for line in self:
            if line.reconciled:
                raise UserError(
                    _(
                        "You are trying to reconcile some entries that are already reconciled."
                    )
                )
            if (
                not line.account_id.reconcile
                and line.account_id.internal_type != "liquidity"
            ):
                raise UserError(
                    _(
                        "Account %s does not allow reconciliation. First change the configuration of this account to allow it."  # noqa: B950
                    )
                    % line.account_id.display_name
                )
            if line.move_id.state not in ["posted", "cancel"]:
                raise UserError(_("You can only reconcile posted entries."))
            if company is None:
                company = line.company_id
            elif line.company_id != company:
                raise UserError(
                    _("Entries doesn't belong to the same company: %s != %s")
                    % (company.display_name, line.company_id.display_name)
                )
            if account is None:
                account = line.account_id
            elif line.account_id != account:
                raise UserError(
                    _("Entries are not from the same account: %s != %s")
                    % (account.display_name, line.account_id.display_name)
                )

        sorted_lines = self.sorted(
            key=lambda line: (line.date_maturity or line.date, line.currency_id)
        )

        # ==== Collect all involved lines through the existing reconciliation ====

        involved_lines = sorted_lines
        involved_partials = self.env["account.partial.reconcile"]
        current_lines = involved_lines
        current_partials = involved_partials
        while current_lines:
            current_partials = (
                current_lines.matched_debit_ids + current_lines.matched_credit_ids
            ) - current_partials
            involved_partials += current_partials
            current_lines = (
                current_partials.debit_move_id + current_partials.credit_move_id
            ) - current_lines
            involved_lines += current_lines

        # ==== Create partials ====

        partials = self.env["account.partial.reconcile"].create(
            sorted_lines._prepare_reconciliation_partials()
        )

        # Track newly created partials.
        results["partials"] = partials
        involved_partials += partials

        # ==== Create entries for cash basis taxes ====

        is_cash_basis_needed = (
            account.company_id.tax_exigibility
            and account.user_type_id.type in ("receivable", "payable")
        )
        if is_cash_basis_needed and not self._context.get("move_reverse_cancel"):
            tax_cash_basis_moves = partials._create_tax_cash_basis_moves()
            results["tax_cash_basis_moves"] = tax_cash_basis_moves

        # ==== Check if a full reconcile is needed ====

        if involved_lines[0].currency_id and all(
            line.currency_id == involved_lines[0].currency_id for line in involved_lines
        ):
            is_full_needed = all(
                line.currency_id.is_zero(line.amount_residual_currency)
                for line in involved_lines
            )
        else:
            is_full_needed = all(
                line.company_currency_id.is_zero(line.amount_residual)
                for line in involved_lines
            )

        if is_full_needed:

            # ==== Create the exchange difference move ====

            if self._context.get("no_exchange_difference"):
                exchange_move = None
            else:
                exchange_move = involved_lines._create_exchange_difference_move()
                if exchange_move:
                    exchange_move_lines = exchange_move.line_ids.filtered(
                        lambda line: line.account_id == account
                    )

                    # Track newly created lines.
                    involved_lines += exchange_move_lines

                    # Track newly created partials.
                    exchange_diff_partials = (
                        exchange_move_lines.matched_debit_ids
                        + exchange_move_lines.matched_credit_ids
                    )
                    involved_partials += exchange_diff_partials
                    results["partials"] += exchange_diff_partials

                    exchange_move._post(soft=False)

            # ==== Create the full reconcile ====

            results["full_reconcile"] = self.env["account.full.reconcile"].create(
                {
                    "exchange_move_id": exchange_move and exchange_move.id,
                    "partial_reconcile_ids": [(6, 0, involved_partials.ids)],
                    "reconciled_line_ids": [(6, 0, involved_lines.ids)],
                }
            )

        # Trigger action for paid invoices
        not_paid_invoices.filtered(
            lambda move: move.payment_state in ("paid", "in_payment")
        ).action_invoice_paid()

        return results
