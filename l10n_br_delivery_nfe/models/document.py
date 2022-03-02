# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

MODFRETE_TRANSP = [
    ("0", "0 - Contratação do Frete por conta do Remetente (CIF)"),
    ("1", "1 - Contratação do Frete por conta do" " destinatário/remetente (FOB)"),
    ("2", "2 - Contratação do Frete por conta de terceiros"),
    ("3", "3 - Transporte próprio por conta do remetente"),
    ("4", "4 - Transporte próprio por conta do destinatário"),
    ("9", "9 - Sem Ocorrência de transporte."),
]


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    @api.depends("incoterm_id")
    def _compute_nfe40_modFrete(self):
        for record in self:
            if record.incoterm_id:
                record.nfe40_modFrete = record.incoterm_id.freight_responsibility
            else:
                record.nfe40_modFrete = "9"

    # Com a adição deste campo e do parametro related em nfe40_modFrete o campo é preenchido na importação
    modFrete = fields.Selection(
        MODFRETE_TRANSP,
        string="Modalidade do frete",
        help="Modalidade do frete"
             "\n0- Contratação do Frete por conta do Remetente (CIF);"
             "\n1- Contratação do Frete por conta do destinatário/remetente (FOB);"
             "\n2- Contratação do Frete por conta de terceiros;"
             "\n3- Transporte próprio por conta do remetente;"
             "\n4- Transporte próprio por conta do destinatário;"
             "\n9- Sem Ocorrência de transporte.")

    nfe40_modFrete = fields.Selection(
        compute=_compute_nfe40_modFrete,
        related='modFrete',
    )

    # Alterar o nome do campo related de partner_id para transporter_id resolve o bug de sobrescrever o parceiro
    nfe40_transporta = fields.Many2one(
        comodel_name="res.partner",
        related="carrier_id.transporter_id",
        string="Dados do transportador",
    )

    transporter_id = fields.Many2one(
        comodel_name='res.partner',
        help='The partner that is doing the delivery service.',
        string='Transportadora'
    )


