# © 2012 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>

import logging

from odoo import api, fields, models

from ..constants import (
    AVISO_FAVORECIDO,
    CODIGO_FINALIDADE_TED,
    COMPLEMENTO_TIPO_SERVICO,
    ESTADOS_CNAB,
)

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base import misc
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")


class BankPaymentLine(models.Model):
    _inherit = "bank.payment.line"

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        mode = (
            self.env["account.payment.order"]
            .browse(self.env.context.get("order_id"))
            .payment_mode_id
        )
        if mode.doc_finality_code:
            res.update({"doc_finality_code": mode.doc_finality_code})
        if mode.ted_finality_code:
            res.update({"ted_finality_code": mode.ted_finality_code})
        if mode.complementary_finality_code:
            res.update(
                {"complementary_finality_code": mode.complementary_finality_code}
            )
        if mode.favored_warning:
            res.update({"favored_warning": mode.favored_warning})
        return res

    doc_finality_code = fields.Selection(
        selection=COMPLEMENTO_TIPO_SERVICO,
        string="Complemento do Tipo de Serviço",
        help="Campo P005 do CNAB",
    )

    ted_finality_code = fields.Selection(
        selection=CODIGO_FINALIDADE_TED,
        string="Código Finalidade da TED",
        help="Campo P011 do CNAB",
    )

    partner_pix_id = fields.Many2one(
        string="Pix Key",
        comodel_name="res.partner.pix",
        related="payment_line_ids.partner_pix_id",
    )

    pix_transfer_type = fields.Selection(
        string="pix transfer type identification",
        readonly=True,
        related="payment_line_ids.pix_transfer_type",
    )

    payment_mode_domain = fields.Selection(
        related="payment_line_ids.payment_mode_domain",
    )

    service_type = fields.Selection(
        related="payment_line_ids.service_type",
    )

    complementary_finality_code = fields.Char(
        string="Código de finalidade complementar",
        size=2,
        help="Campo P013 do CNAB",
    )

    favored_warning = fields.Selection(
        selection=AVISO_FAVORECIDO,
        string="Aviso ao Favorecido",
        default="0",
        help="Campo P006 do CNAB",
    )

    rebate_value = fields.Monetary(
        string="Valor do Abatimento",
        help="Campo G045 do CNAB",
    )

    discount_value = fields.Monetary(
        string="Valor do Desconto",
        help="Campo G046 do CNAB",
    )

    interest_value = fields.Monetary(
        string="Valor da Mora",
        help="Campo G047 do CNAB",
    )

    fee_value = fields.Monetary(
        string="Valor da Multa",
        help="Campo G048 do CNAB",
    )

    event_id = fields.One2many(
        string="Eventos CNAB",
        comodel_name="l10n_br_cnab.return.event",
        inverse_name="bank_payment_line_id",
        readonly=True,
    )

    own_number = fields.Char(
        string="Nosso Numero",
    )

    document_number = fields.Char(
        string="Número documento",
    )

    barcode = fields.Char(
        string="Barcode", readonly=True, related="payment_line_ids.barcode"
    )

    company_title_identification = fields.Char(
        string="Identificação Titulo Empresa",
    )

    is_export_error = fields.Boolean(
        string="Contem erro de exportação",
    )

    export_error_message = fields.Char(
        string="Mensagem de erro",
    )

    last_cnab_state = fields.Selection(
        selection=ESTADOS_CNAB,
        string="Último Estado do CNAB",
        help="Último Estado do CNAB antes da confirmação de "
        "pagamento nas Ordens de Pagamento",
    )

    mov_instruction_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Código da Instrução para Movimento",
        help="Campo G061 do CNAB",
    )

    def unlink(self):
        for record in self:
            if not record.last_cnab_state:
                continue

            move_line_id = self.env["account.move.line"].search(
                [
                    (
                        "company_title_identification",
                        "=",
                        record.company_title_identification,
                    )
                ]
            )
            move_line_id.cnab_state = record.last_cnab_state

        return super().unlink()

    @api.model
    def same_fields_payment_line_and_bank_payment_line(self):
        res = super().same_fields_payment_line_and_bank_payment_line()
        res.append("partner_pix_id")
        res.append("service_type")
        return res

    # TODO: Implementar métodos para outros tipos cnab.
    #   _prepare_pagamento_bank_line_vals
    #   _prepare_debito_automatico_bank_line_vals
    #   _prepare_[...]_bank_line_vals

    def _prepare_boleto_bank_line_vals(self):
        return {
            "valor": self.amount_currency,
            "data_vencimento": self.date.strftime("%Y/%m/%d"),
            "nosso_numero": self.own_number,
            "documento_sacado": misc.punctuation_rm(self.partner_id.cnpj_cpf),
            "nome_sacado": self.partner_id.legal_name.strip()[:40],
            "numero": self.document_number,
            "endereco_sacado": str(
                self.partner_id.street_name + ", " + str(self.partner_id.street_number)
            )[:40],
            "bairro_sacado": self.partner_id.district.strip(),
            "cep_sacado": misc.punctuation_rm(self.partner_id.zip),
            "cidade_sacado": self.partner_id.city_id.name,
            "uf_sacado": self.partner_id.state_id.code,
            # Codigo da Ocorrencia usado pode variar por Banco, CNAB e operação
            # ex.: UNICRED 240/400 é 01 - Remessa*, 02 - Pedido de Baixa e
            # 06 - Alteração de vencimento . Veja que está sendo informado
            # o campo Code do objeto.
            "identificacao_ocorrencia": self.mov_instruction_code_id.code,
        }
