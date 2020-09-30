# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime
from ..febraban.cnab import Cnab

from odoo import api, models, fields

_logger = logging.getLogger(__name__)


class L10n_brCnab(models.Model):
    _inherit = 'l10n_br.cnab'

    @api.multi
    def reprocessar_arquivo_retorno(self):
        cnab_type, arquivo_parser = Cnab.detectar_retorno(self.arquivo_retorno)
        data_arquivo = str(arquivo_parser.header.arquivo_data_de_geracao)
        self.sequencial_arquivo = str(arquivo_parser.header.sequencial_arquivo)
        self.data_arquivo = datetime.strptime(data_arquivo.zfill(6), "%d%m%y")

        self.bank_account_id = self._busca_conta(
            arquivo_parser.header.codigo_do_banco,
            arquivo_parser.header.cedente_agencia,
            arquivo_parser.header.cedente_conta,
        )

        self.num_lotes = len(arquivo_parser.lotes)
        self.num_eventos = arquivo_parser.trailer.totais_quantidade_registros
        for lote in arquivo_parser.lotes:

            header = lote.header or arquivo_parser.header
            trailer = lote.trailer or arquivo_parser.trailer

            lote_id = self.lote_id and self.lote_id[0]
            bankless_line_id = \
                lote_id.evento_id.filtered(
                    lambda e: not e.bank_payment_line_id)
            bankless_line_id.unlink()

            for evento in lote.eventos:
                if not lote_id:
                    lote_id, lote_bank_account_id = self._cria_lote(
                        header, lote, evento, trailer)

                if cnab_type == '240':
                    self._reprocessa_lote_240(evento, lote_id)
                else:
                    self._reprocessa_lote_400(evento, lote_id)

            # TODO: Verificar necessidade de atualizar dados do Account.Move
            return self.write({'state': 'done'})

    @api.multi
    def processar_arquivo_retorno(self):
        cnab_type, arquivo_parser = Cnab.detectar_retorno(self.arquivo_retorno)
        # if not arquivo_parser.header.arquivo_codigo == u'2':
        #     raise exceptions.Warning(
        #         u"Este não é um arquivo de retorno!"
        #     )
        data_arquivo = str(arquivo_parser.header.arquivo_data_de_geracao)
        self.sequencial_arquivo = str(arquivo_parser.header.sequencial_arquivo)
        self.data_arquivo = datetime.strptime(data_arquivo.zfill(6), "%d%m%y")

        if self.search([
            ('data_arquivo', '=', self.data_arquivo),
            ('sequencial_arquivo', '=', self.sequencial_arquivo),
            ('id', '!=', self.id)]):
            self.state = 'error'
            self.motivo_erro = u"O arquivo %s, de %s - sequencial %s, " \
                               u"ja se encontra importado." % \
                               (self.filename,
                                datetime.strftime(fields.Datetime.from_string(
                                    self.data_arquivo), "%d/%m/%Y"),
                                self.sequencial_arquivo)
            return

        self.bank_account_id = self._busca_conta(
            arquivo_parser.header.codigo_do_banco,
            arquivo_parser.header.cedente_agencia,
            arquivo_parser.header.cedente_conta,
        )

        self.num_lotes = len(arquivo_parser.lotes)
        self.num_eventos = arquivo_parser.trailer.totais_quantidade_registros
        for lote in arquivo_parser.lotes:

            header = lote.header or arquivo_parser.header
            trailer = lote.trailer or arquivo_parser.trailer

            lote_id = False
            total_amount = 0.0
            lines = []
            inv_list = []
            for evento in lote.eventos:
                if not lote_id:
                    lote_id, lote_bank_account_id = self._cria_lote(
                        header, lote, evento, trailer)

                if cnab_type == '240':
                    self._lote_240(evento, lote_id)
                else:
                    line_vals, line_amount, invoices = \
                        self._lote_400(evento, lote_id)
                    for inv in invoices:
                        inv_list.append(inv)
                    if line_vals and line_amount:
                        for line in line_vals:
                            lines.append(line)
                        total_amount += line_amount

            if total_amount and lines:
                counterpart_account_id = self.env['account.journal'].browse(
                    lines[0][2]['journal_id']).default_debit_account_id.id

                lines.append(
                    (0, 0, {
                        'name': 'cobranca',
                        'debit': total_amount,
                        'account_id': counterpart_account_id,
                        'journal_id': lines[0][2]['journal_id'],
                        'date_maturity': False,
                        'partner_id': False,
                    })
                )
                move = self.env['account.move'].create({
                    'name': 'RetornoCnab_' + fields.Datetime.now(),
                    'ref':
                        'Retorno Gerado em %s' %
                        datetime.strftime(datetime.strptime(
                            data_arquivo.zfill(6), "%d%m%y"), "%d/%m/%Y"),
                    'date': str(datetime.now()),
                    'line_ids': lines,
                    'journal_id': lines[0][2]['journal_id']
                })
                move.post()

                for inv in inv_list:
                    if inv.state != 'open':
                        continue
                    inv_move_lines = inv.move_line_receivable_id
                    pay_move_lines = move.line_ids.filtered(
                        lambda x: x.account_id == inv_move_lines.account_id and
                                  x.partner_id == inv_move_lines.partner_id and
                                  x.name == inv_move_lines.transaction_ref
                    )
                    move_lines = pay_move_lines | inv_move_lines
                    move_lines.reconcile()

        return self.write({'state': 'done'})
