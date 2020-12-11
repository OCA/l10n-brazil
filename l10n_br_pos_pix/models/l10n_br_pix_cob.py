# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _

CHANNEL_PIX = 'pix'


class L10nBrPixCob(models.Model):

    _inherit = 'l10n_br_pix.cob'

    pos_id = fields.Many2one("pos.config")

    @api.multi
    def _prepare_message(self):
        self.ensure_one()
        # result_json = json.loads(self.result_raw)
        msg = {
            "event": "payment_result",
            # "result_code": result_json["result_code"],
            "order_ref": self.name,
            "total_fee": self.valor_original,
            "journal_id": self.journal_id.id,
        }
        return msg

    @api.multi
    def informar_pagamento(self):
        self.ensure_one()
        msg = self._prepare_message()
        assert self.pos_id, "The record has empty value of pos_id field"
        return self.env["pos.config"]._send_to_channel_by_id(
            self._cr.dbname, self.pos_id.id, CHANNEL_PIX, msg
        )

    def consultar_cobranca(self):
        result = super(L10nBrPixCob, self).consultar_cobranca()
        self.informar_pagamento()
        return result

    @api.model
    def create_pix_cobranca(self, lines, pos_id, order_ref, terminal_ref, journal_id,
                            pay_amount, **kwargs):
        pix_cob = self.create({
            'name': order_ref,
            # 'pix_config_id': ?,
            # pix_key_id: ?,
            'pos_id': pos_id,
            'valor_original': pay_amount,
            'journal_id': journal_id,
        })
        pix_cob.criar_cobranca()
        return {"code_url": pix_cob.br_code_text}
