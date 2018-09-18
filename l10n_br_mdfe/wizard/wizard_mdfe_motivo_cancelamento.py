from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.exceptions import Warning as UserError


class MdfeCancelamentoWizard(models.TransientModel):
    _name = b'mdfe.cancelamento.wizard'

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

        mdfe = self.env['sped.documento'].browse(self.env.context['active_id'])

        mdfe.justificativa = self.motivo_cancelamento

        mdfe.cancelar_documento()

        return {'type': 'ir.actions.act_window_close'}
