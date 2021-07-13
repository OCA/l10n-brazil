# © 2012 KMEE INFORMATICA LTDA
#   @author  Luiz Felipe do Divino Costa <luiz.divino@kmee.com.br>
#   @author  Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import re
from datetime import datetime

from odoo import api, fields, models

from ..constants import (
    COD_REGISTROS_REJEITADOS_CNAB400,
    CODIGO_OCORRENCIAS,
    CODIGO_OCORRENCIAS_CNAB200,
    RETORNO_400_BAIXA,
    RETORNO_400_CONFIRMADA,
    RETORNO_400_LIQUIDACAO,
    RETORNO_400_REJEITADA,
    RETORNOS_TRATADOS,
    STATE_CNAB,
    STR_EVENTO_FORMAT,
)

_logger = logging.getLogger(__name__)

TIPO_OPERACAO = {
    "C": "Lançamento a Crédito",
    "D": "Lançamento a Débito",
    "E": "Extrato para Conciliação",
    "G": "Extrato para Gestão de Caixa",
    "I": "Informações de Títulos Capturados do Próprio Banco",
    "R": "Arquivo Remessa",
    "T": "Arquivo Retorno",
}

TIPO_SERVICO = {
    "01": "Cobrança",
    "03": "Boleto de Pagamento Eletrônico",
    "04": "Conciliação Bancária",
    "05": "Débitos",
    "06": "Custódia de Cheques",
    "07": "Gestão de Caixa",
    "08": "Consulta/Informação Margem",
    "09": "Averbação da Consignação/Retenção",
    "10": "Pagamento Dividendos",
    "11": "Manutenção da Consignação",
    "12": "Consignação de Parcelas",
    "13": "Glosa da Consignação (INSS)",
    "14": "Consulta de Tributos a pagar",
    "20": "Pagamento Fornecedor",
    "22": "Pagamento de Contas, Tributos e Impostos",
    "23": "Interoperabilidade entre Contas de Instituições de Pagamentos",
    "25": "Compror",
    "26": "Compror Rotativo",
    "29": "Alegação do Pagador",
    "30": "Pagamento Salários",
    "32": "Pagamento de honorários",
    "33": "Pagamento de bolsa auxílio",
    "34": "Pagamento de prebenda (remuneração a padres e sacerdotes)",
    "40": "Vendor",
    "41": "Vendor a Termo",
    "50": "Pagamento Sinistros Segurados",
    "60": "Pagamento Despesas Viajante em Trânsito",
    "70": "Pagamento Autorizado",
    "75": "Pagamento Credenciados",
    "77": "Pagamento de Remuneração",
    "80": "Pagamento Representantes / Vendedores Autorizados",
    "90": "Pagamento Benefícios",
    "98": "Pagamentos Diversos",
}

TIPO_INSCRICAO_EMPRESA = {
    0: "Isento / Não informado",
    1: "CPF",
    2: "CGC / CNPJ",
    3: "PIS / PASEP",
    9: "Outros",
}


class L10nBrCnab(models.Model):
    _name = "l10n_br.cnab"
    _description = "l10n_br CNAB"

    display_name = fields.Char(compute="_compute_display_name", store=True, index=True)

    return_file = fields.Binary(string="Arquivo Retorno")
    filename = fields.Char(string="Filename")
    bank_account_id = fields.Many2one(
        string="Conta cedente", comodel_name="res.partner.bank"
    )
    cnab_date = fields.Date(
        string="Data CNAB", required=True, default=datetime.now().date()
    )
    date_file = fields.Date(string="Data Criação no Banco")
    sequential_file = fields.Char(string="Sequencial do Arquivo")
    reason_error = fields.Char(string="Motivo do Erro")
    lot_id = fields.One2many(
        string="Lotes", comodel_name="l10n_br.cnab.lote", inverse_name="cnab_id"
    )
    name = fields.Char(string="Name")
    number_events = fields.Integer(string="Número de Eventos")
    number_lots = fields.Integer(string="Número de Lotes")
    state = fields.Selection(string="Estágio", selection=STATE_CNAB, default="draft")

    @api.depends("name")
    def _compute_display_name(self):
        self.display_name = self.name

    def _busca_conta(self, banco, agencia, conta):
        return (
            self.env["res.partner.bank"]
            .search(
                [
                    # ('acc_number', '=', str(banco)),
                    ("bra_number", "=", str(agencia)),
                    ("acc_number", "=", str(conta)),
                ]
            )
            .id
        )

    def _cria_lote(self, header, lote, evento, trailer):

        if lote.header:
            lote_bank_account_id = self._busca_conta(
                lote.header.codigo_do_banco,
                lote.header.cedente_agencia,
                lote.header.cedente_conta,
            ).id
        else:
            lote_bank_account_id = self.bank_account_id

        vals = {
            "account_bank_id": lote_bank_account_id.id,
            "servico_operacao": header.literal_retorno,
            "tipo_servico": header.literal_servico,
            "qtd_registros": trailer.totais_quantidade_registros,
            "total_valores": float(trailer.valor_total_titulos) / 100,
            "cnab_id": self.id,
        }

        lote_id = self.env["l10n_br.cnab.lote"].create(vals)

        return lote_id, lote_bank_account_id

    def _lote_400(self, evento, lote_id):

        bank_payment_line_id = self.env["bank.payment.line"].search(
            [("nosso_numero", "=", evento.nosso_numero)], limit=1
        )

        vals_evento = {
            "bank_payment_line_id": bank_payment_line_id.id,
            "data_ocorrencia": datetime.strptime(
                str(evento.data_ocorrencia).zfill(6), STR_EVENTO_FORMAT
            )
            if evento.data_ocorrencia
            else "",
            "data_real_pagamento": datetime.strptime(
                str(evento.data_credito).zfill(6), STR_EVENTO_FORMAT
            )
            if evento.data_credito
            else "",
            "identificacao_titulo_empresa": evento.identificacao_titulo_empresa,
            "invoice_id": bank_payment_line_id.payment_line_ids[
                :1
            ].move_line_id.invoice_id.id,
            "juros_mora_multa": float(evento.juros_mora_multa) / 100,
            "lote_id": lote_id.id,
            "nosso_numero": str(evento.nosso_numero),
            "ocorrencias": CODIGO_OCORRENCIAS_CNAB200[evento.codigo_ocorrencia],
            "outros_creditos": float(evento.outros_creditos) / 100,
            "partner_id": bank_payment_line_id.partner_id.id,
            "seu_numero": evento.numero_documento,
            "str_motiv_a": COD_REGISTROS_REJEITADOS_CNAB400.get(int(evento.erros[0:2]))
            if evento.erros[0:2]
            else "",
            "str_motiv_b": COD_REGISTROS_REJEITADOS_CNAB400.get(int(evento.erros[2:4]))
            if evento.erros[2:4]
            else "",
            "str_motiv_c": COD_REGISTROS_REJEITADOS_CNAB400.get(int(evento.erros[4:6]))
            if evento.erros[4:6]
            else "",
            "str_motiv_d": COD_REGISTROS_REJEITADOS_CNAB400.get(int(evento.erros[6:8]))
            if evento.erros[6:8]
            else "",
            "tarifa_cobranca": float(evento.tarifa_cobranca),
            "valor": float(evento.valor) / 100,
            "valor_abatimento": float(evento.valor_abatimento) / 100,
            "valor_desconto": float(evento.valor_desconto) / 100,
            "valor_iof": float(evento.valor_iof) / 100,
            "valor_pagamento": evento.valor_principal,
        }
        cnab_event_id = self.env["l10n_br.cnab.evento"].create(vals_evento)

        amount = 0.0
        line_values = []
        invoices = []
        codigo_ocorrencia = evento.codigo_ocorrencia
        if codigo_ocorrencia and bank_payment_line_id:
            cnab_state = False
            bank_state = False
            if codigo_ocorrencia in RETORNO_400_CONFIRMADA:
                cnab_state = "accepted"
                bank_state = "aberta"
            elif codigo_ocorrencia in RETORNO_400_REJEITADA:
                cnab_state = "not_accepted"
                bank_state = "inicial"
            elif codigo_ocorrencia in RETORNO_400_LIQUIDACAO:
                cnab_state = "accepted"
                bank_state = "liquidada"
            elif codigo_ocorrencia in RETORNO_400_BAIXA:
                cnab_state = "accepted"
                if codigo_ocorrencia == 9:
                    bank_state = "baixa"
                else:
                    bank_state = "baixa_liquidacao"
            else:
                cnab_event_id.str_motiv_e = (
                    str(codigo_ocorrencia) + ": Ocorrência não tratada"
                )

            if cnab_state:

                for pay_order_line_id in bank_payment_line_id.payment_line_ids:
                    pay_order_line_id.move_line_id.state_cnab = cnab_state
                    pay_order_line_id.move_line_id.nosso_numero = str(
                        evento.nosso_numero
                    )
                    move_line = pay_order_line_id.move_line_id
                    invoice = move_line.invoice_id
                    payment_mode = invoice.payment_mode_id
                    if bank_state == "liquidada" and invoice.state == "open":
                        ident_titulo_empresa = evento.identificacao_titulo_empresa
                        line_dict = {
                            "name": evento.nosso_numero,
                            "nosso_numero": evento.nosso_numero,
                            "numero_documento": evento.numero_documento,
                            "identificacao_titulo_empresa": ident_titulo_empresa,
                            "credit": float(evento.valor_principal)
                            + float(evento.tarifa_cobranca),
                            "account_id": payment_mode.default_account_id.id
                            or invoice.account_id.id,
                            "journal_id": bank_payment_line_id.order_id.journal_id.id,
                            "date_maturity": datetime.strptime(
                                str(evento.data_vencimento).zfill(6), STR_EVENTO_FORMAT
                            )
                            if evento.data_vencimento
                            else "",
                            "date": datetime.strptime(
                                str(evento.data_ocorrencia).zfill(6), STR_EVENTO_FORMAT
                            )
                            if evento.data_ocorrencia
                            else "",
                            "partner_id": bank_payment_line_id.partner_id.id,
                        }

                        line_values.append((0, 0, line_dict))
                        amount += float(evento.valor_principal)
                        invoices.append(invoice)

                        invoice_line_tax_id = invoice.invoice_line_ids.filtered(
                            lambda i: i.price_subtotal == float(evento.tarifa_cobranca)
                        )
                        if invoice_line_tax_id:
                            # amount += float(evento.tarifa_cobranca)

                            line_dict_tarifa = dict(line_dict)
                            line_dict_tarifa.update(
                                {
                                    "name": str(evento.nosso_numero) + " - Tarifa",
                                    "credit": 0,
                                    "debit": float(evento.tarifa_cobranca),
                                    "account_id": payment_mode.default_tax_account_id.id
                                    or invoice.account_id.id,
                                }
                            )
                            line_values.append((0, 0, line_dict_tarifa))

                        # TODO: Juros / iof / Desconto / Abatimento /
                        #  Outros Créditos
                        # if evento.juros_mora_multa:
                        #     amount += float(evento.juros_mora_multa)
                        #     line_dict_multa = dict(line_dict)
                        #     line_dict_multa.update({
                        #         'name': str(evento.nosso_numero) + ' - Juros',
                        #         'credit': float(evento.juros_mora_multa),
                        #         'account_id': invoice.account_id.id,
                        #     })
                        #     line_values.append((0, 0, line_dict_multa))

                    if bank_state:
                        move_line.situacao_pagamento = bank_state
                    if cnab_state:
                        move_line.state_cnab = cnab_state

        return line_values, amount, invoices

    def _lote_240(self, evento, lote_id):
        data_evento = str(evento.credito_data_real)
        data_evento = fields.Date.from_string(
            data_evento[4:] + "-" + data_evento[2:4] + "-" + data_evento[0:2]
        )
        lote_bank_account_id = self.env["res.partner.bank"].search(
            [
                ("bra_number", "=", evento.favorecido_agencia),
                ("bra_number_dig", "=", evento.favorecido_agencia_dv),
                ("acc_number", "=", evento.favorecido_conta),
                ("acc_number_dig", "=", evento.favorecido_conta_dv),
            ]
        )
        lote_bank_account_id = (
            lote_bank_account_id.ids[0] if lote_bank_account_id else False
        )
        favorecido_partner = self.env["res.partner.bank"].search(
            [("owner_name", "ilike", evento.favorecido_nome)]
        )
        favorecido_partner = (
            favorecido_partner[0].partner_id.id if favorecido_partner else False
        )
        bank_payment_line_id = self.env["bank.payment.line"].search(
            [("name", "=", evento.credito_seu_numero)]
        )
        ocorrencias_dic = dict(CODIGO_OCORRENCIAS)
        ocorrencias = [
            evento.ocorrencias[0:2],
            evento.ocorrencias[2:4],
            evento.ocorrencias[4:6],
            evento.ocorrencias[6:8],
            evento.ocorrencias[8:10],
        ]
        vals_evento = {
            "data_real_pagamento": data_evento,
            "segmento": evento.servico_segmento,
            "favorecido_nome": favorecido_partner,
            "favorecido_conta_bancaria": lote_bank_account_id,
            "nosso_numero": str(evento.credito_nosso_numero),
            "seu_numero": evento.credito_seu_numero,
            "tipo_moeda": evento.credito_moeda_tipo,
            "valor_pagamento": evento.credito_valor_pagamento,
            "ocorrencias": evento.ocorrencias,
            "str_motiv_a": ocorrencias_dic[ocorrencias[0]] if ocorrencias[0] else "",
            "str_motiv_b": ocorrencias_dic[ocorrencias[1]] if ocorrencias[1] else "",
            "str_motiv_c": ocorrencias_dic[ocorrencias[2]] if ocorrencias[2] else "",
            "str_motiv_d": ocorrencias_dic[ocorrencias[3]] if ocorrencias[3] else "",
            "str_motiv_e": ocorrencias_dic[ocorrencias[4]] if ocorrencias[4] else "",
            "lote_id": lote_id.id,
            "bank_payment_line_id": bank_payment_line_id.id,
        }
        self.env["l10n_br.cnab.evento"].create(vals_evento)
        if evento.ocorrencias and bank_payment_line_id:
            if "00" in ocorrencias:
                bank_state = "paid"
                cnab_state = "accepted"

            else:
                bank_state = "exception"
                cnab_state = "not_accepted"

            bank_payment_line_id.state2 = bank_state
            for payment_line in bank_payment_line_id.payment_line_ids:
                payment_line.move_line_id.state_cnab = cnab_state

    def _reprocessa_lote_240(self, evento, lote_id):
        raise NotImplementedError("FALTA FAZER")

    def _reprocessa_lote_400(self, evento, lote_id):
        bank_payment_line_id = self.env["bank.payment.line"].search(
            [
                (
                    "identificacao_titulo_empresa",
                    "=",
                    evento.identificacao_titulo_empresa,
                )
            ],
            limit=1,
        )

        cnab_event_id = self.env["l10n_br.cnab.evento"].search(
            [
                ("lote_id", "=", lote_id.id),
                ("bank_payment_line_id", "!=", False),
                ("bank_payment_line_id", "=", bank_payment_line_id.id),
            ]
        )

        vals_evento = {
            "bank_payment_line_id": cnab_event_id.bank_payment_line_id.id
            or bank_payment_line_id.id,
            "data_ocorrencia": datetime.strptime(
                str(evento.data_ocorrencia).zfill(6), STR_EVENTO_FORMAT
            )
            if evento.data_ocorrencia
            else "",
            "data_real_pagamento": datetime.strptime(
                str(evento.data_credito).zfill(6), STR_EVENTO_FORMAT
            )
            if evento.data_credito
            else "",
            "identificacao_titulo_empresa": evento.identificacao_titulo_empresa,
            "invoice_id": cnab_event_id.invoice_id.id
            or bank_payment_line_id.payment_line_ids[:1].move_line_id.invoice_id.id,
            "juros_mora_multa": cnab_event_id.juros_mora_multa
            or float(evento.juros_mora_multa) / 100,
            "lote_id": cnab_event_id.lote_id.id or lote_id.id,
            "nosso_numero": str(evento.nosso_numero),
            "ocorrencias": CODIGO_OCORRENCIAS_CNAB200[evento.codigo_ocorrencia],
            "outros_creditos": cnab_event_id.outros_creditos
            or float(evento.outros_creditos) / 100,
            "partner_id": bank_payment_line_id.partner_id.id,
            "seu_numero": evento.numero_documento,
            "str_motiv_a": COD_REGISTROS_REJEITADOS_CNAB400.get(int(evento.erros[0:2]))
            if evento.erros[0:2]
            else "",
            "str_motiv_b": COD_REGISTROS_REJEITADOS_CNAB400.get(int(evento.erros[2:4]))
            if evento.erros[2:4]
            else "",
            "str_motiv_c": COD_REGISTROS_REJEITADOS_CNAB400.get(int(evento.erros[4:6]))
            if evento.erros[4:6]
            else "",
            "str_motiv_d": COD_REGISTROS_REJEITADOS_CNAB400.get(int(evento.erros[6:8]))
            if evento.erros[6:8]
            else "",
            "tarifa_cobranca": cnab_event_id.tarifa_cobranca
            or float(evento.tarifa_cobranca),
            "valor": cnab_event_id.valor or float(evento.valor) / 100,
            "valor_abatimento": cnab_event_id.valor_abatimento
            or float(evento.valor_abatimento) / 100,
            "valor_desconto": cnab_event_id.valor_desconto
            or float(evento.valor_desconto) / 100,
            "valor_iof": cnab_event_id.valor_iof or float(evento.valor_iof) / 100,
            "valor_pagamento": cnab_event_id.valor_pagamento or evento.valor_principal,
        }

        if not cnab_event_id:
            cnab_event_id = cnab_event_id.create(vals_evento)
        else:
            cnab_event_id.write(vals_evento)

        codigo_ocorrencia = evento.codigo_ocorrencia
        if codigo_ocorrencia and bank_payment_line_id:

            if not any(codigo_ocorrencia in x for x in RETORNOS_TRATADOS):
                cnab_event_id.str_motiv_e = (
                    str(codigo_ocorrencia) + ": Ocorrência não tratada"
                )

            bank_payment_line_id.nosso_numero = str(evento.nosso_numero)
            for pay_order_line_id in bank_payment_line_id.payment_line_ids:
                pay_order_line_id.move_line_id.nosso_numero = str(evento.nosso_numero)
                pay_order_line_id.nosso_numero = str(evento.nosso_numero)
                debit_move_line = pay_order_line_id.move_line_id
                credit_move_line = self.env["account.move.line"].search(
                    [
                        "|",
                        ("nosso_numero", "=", evento.nosso_numero),
                        ("name", "=", evento.nosso_numero),
                        ("credit", ">", 0),
                    ]
                )

                if not credit_move_line and debit_move_line.full_reconcile_id:
                    credit_move_line = (
                        debit_move_line.full_reconcile_id.reconciled_line_ids
                        - debit_move_line
                    )

                if not credit_move_line:
                    return
                    # raise UserError(
                    #     'Não foi encontrada uma linha correspondente para a '
                    #     'linha de nosso_numero: %s' % evento.nosso_numero)

                line_values = {
                    "name": evento.nosso_numero,
                    "nosso_numero": evento.nosso_numero,
                    "numero_documento": evento.numero_documento,
                    "identificacao_titulo_empresa": evento.identificacao_titulo_empresa,
                    "date_maturity": datetime.strptime(
                        str(evento.data_vencimento).zfill(6), STR_EVENTO_FORMAT
                    )
                    if evento.data_vencimento
                    else "",
                    "date": datetime.strptime(
                        str(evento.data_ocorrencia).zfill(6), STR_EVENTO_FORMAT
                    )
                    if evento.data_ocorrencia
                    else "",
                }

                credit_move_line.with_context(reprocessing=True).write(line_values)

    @api.model
    def processar_retorno_multi(self):
        active_ids = self._context.get("active_ids")

        for cnab_id in self.browse(active_ids):
            if cnab_id.state in ["draft"]:
                cnab_id.processar_arquivo_retorno()

    @api.model
    def reprocessar_retorno_multi(self):
        active_ids = self._context.get("active_ids")

        for cnab_id in self.browse(active_ids):
            if cnab_id.state in ["done"]:
                cnab_id.reprocessar_arquivo_retorno()

    def reprocessar_arquivo_retorno(self):
        raise NotImplementedError

    def processar_arquivo_retorno(self):
        raise NotImplementedError

    def _get_name(self, data, filename):
        cnab_ids = self.search([("cnab_date", "=", data)], order="id desc")
        cnab_idx = 1
        if cnab_ids:
            search_result = list(
                filter(
                    lambda x: x is not None,
                    [
                        re.search(r"\((\d)\)", name)
                        for name in self.search(
                            [("cnab_date", "=", data), ("id", "!=", self.id)],
                            order="id desc",
                        ).mapped("name")
                    ],
                )
            )
            if search_result:
                cnab_idx = max(int(result.group(1)) for result in search_result) + 1

        cnab_name = "{}({}){}".format(
            data, cnab_idx, " - " + filename if filename else ""
        )
        return cnab_name

    def write(self, vals):
        if any(v in vals for v in ["data", "filename"]):
            data = vals.get("data") or self.data
            filename = vals.get("filename") or self.filename

            name = self._get_name(data, filename)
            vals.update({"name": name})
        return super().write(vals)

    @api.model
    def create(self, vals):
        name = self._get_name(vals.get("data"), vals.get("filename"))
        vals.update({"name": name})
        return super().create(vals)
