# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class HrContractChange(models.Model):
    _inherit = 'l10n_br_hr.contract.change'

    payment_mode_id = fields.Many2one(
        comodel_name='payment.mode',
        string='Forma de Pagamento padrão do holerite',
    )

    def _gerar_dicionario_dados(self, change):
        vals = super(HrContractChange, self)._gerar_dicionario_dados(change)
        contract = change.contract_id
        vals.update(
            payment_mode_id=contract.payment_mode_id.id,
        )

        return vals

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        super(HrContractChange, self)._onchange_contract_id()

        contract = self.contract_id
        if self.change_type == 'lotacao-local':
            self.payment_mode_id = contract.payment_mode_id

    @api.multi
    def apply_contract_changes(self):
        """
        Aplica a alteração no contrato, e se for a primeira alteração daquele
        tipo cria um registro de alteração inicial.
        :return:
        """
        for alteracao in self:
            super(HrContractChange, self).apply_contract_changes()
            if self.change_type == 'lotacao-local':
                # alias para o contrato corrente
                contract = alteracao.contract_id
                # Setar variavel de contexto para indicar que a alteração
                # partiu do menu de alterações contratuais.
                contract.with_context(
                    alteracaocontratual=True).payment_mode_id = \
                    alteracao.payment_mode_id
