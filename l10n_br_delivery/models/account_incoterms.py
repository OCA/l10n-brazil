# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

# Modalidade do frete
MODFRETE_TRANSP = [
    ('0', '0 - Contratação do Frete por conta do Remetente (CIF)'),
    ('1', '1 - Contratação do Frete por conta do'
          ' destinatário/remetente (FOB)'),
    ('2', '2 - Contratação do Frete por conta de terceiros'),
    ('3', '3 - Transporte próprio por conta do remetente'),
    ('4', '4 - Transporte próprio por conta do destinatário'),
    ('9', '9 - Sem Ocorrência de transporte.'),
]


class AccountIncoterms(models.Model):
    _inherit = 'account.incoterms'

    freight_responsibility = fields.Selection(
        selection=MODFRETE_TRANSP,
        string='Frete por Conta',
        help='Informação usada na emissão de Documentos Fiscais',
        required=True,
        default='0'
    )
