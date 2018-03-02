from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.exceptions import Warning as UserError


class NfeCancelamentoWizard(models.TransientModel):
    _name = b'nfe.cancelamento.wizard'

    motivo_cancelamento = fields.Char(
        string='Justificativa para Cancelamento de NF-e',
        required=True,
        size=255,
    )

    @api.multi
    def action_motivo_cancelamento(self):
        """
        
        :return: 
        """

        self.ensure_one()

        if len(self.motivo_cancelamento) < 10:
            raise UserError("A justificativa deve ter mais de 10 caracteres.")

        nfe = self.env['sped.documento'].browse(self.env.context['active_id'])

        nfe.justificativa = self.motivo_cancelamento

        nfe.cancela_nfe()

        return {'type': 'ir.actions.act_window_close'}
