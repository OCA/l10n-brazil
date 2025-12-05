# models/cnab_payment_rule.py

# Copyright (C) 2025 Escodoo (https://www.escodoo.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

# A constante TIPO_SERVICO é importada do módulo de dependência, conforme seu código
from odoo.addons.l10n_br_account_payment_order.constants import TIPO_SERVICO 


class CNABPaymentRule(models.Model):
    """Rules to select CNAB Payment Way and Service Type based on conditions"""

    _name = "l10n_br_cnab.payment.rule"
    _description = "CNAB Payment Selection Rule"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)

    cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.structure",
        ondelete="cascade",
        required=True,
    )

    match_bank_type = fields.Selection(
        [("same", "Same Bank"), ("other", "Other Bank"), ("any", "Any")],
        default="any",
        required=True,
    )
    match_partner_type = fields.Selection(
        [("employee", "Employee"), ("supplier", "Supplier"), ("any", "Any")],
        default="any",
        required=True,
    )

    payment_way_id = fields.Many2one(
        comodel_name="cnab.payment.way",
        required=True,
        domain="[('cnab_structure_id', '=', cnab_structure_id)]",
    )

    service_type = fields.Selection(
        selection="_get_service_type_selection",
        required=True,
    )

    @api.model
    def _get_service_type_selection(self):
        """
        Retorna a lista de tipos de serviço (TIPO_SERVICO) filtrada pelos
        tipos configurados nos lotes da estrutura CNAB selecionada.
        """
        structure = False
        
        if len(self) == 1 and self.cnab_structure_id:
            structure = self.cnab_structure_id
        elif self._context.get('cnab_structure_id'):
            structure_id = self._context['cnab_structure_id']
            structure = self.env['l10n_br_cnab.structure'].browse(structure_id)
        
        if structure and structure.batch_ids:
            allowed_service_types = set(structure.batch_ids.mapped("service_type"))

            return [
                (code, name)
                for code, name in TIPO_SERVICO
                if code in allowed_service_types
            ]
        
        return TIPO_SERVICO

    @api.onchange("cnab_structure_id")
    def _onchange_cnab_structure_id(self):
        """
        Limpa o valor de service_type e atualiza o contexto para forçar 
        a atualização da lista de opções (selection) na UI.
        """
        self.service_type = False
        
        context = {}
        if self.cnab_structure_id:
            context['cnab_structure_id'] = self.cnab_structure_id.id
            
        return {'context': context}

    @api.constrains("service_type", "cnab_structure_id")
    def _check_service_type_allowed(self):
        """
        Garante que o service_type selecionado é permitido pela estrutura 
        CNAB no momento da criação ou salvamento no banco de dados.
        """
        for record in self.filtered(lambda r: r.cnab_structure_id and r.service_type):
            
            allowed_service_types = set(
                record.cnab_structure_id.batch_ids.mapped("service_type")
            )

            if record.service_type not in allowed_service_types:
                service_type_display = dict(TIPO_SERVICO).get(
                    record.service_type, record.service_type
                )
                
                raise ValidationError(
                    _(
                        "The selected Service Type (%s) is not allowed for the "
                        "CNAB Structure '%s'. Please select a valid service type "
                        "configured in the batches of this structure."
                    )
                    % (service_type_display, record.cnab_structure_id.display_name)
                )