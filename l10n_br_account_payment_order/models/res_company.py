# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

from ..constants import (
    SEQUENCIAL_CARTEIRA,
    SEQUENCIAL_EMPRESA,
    SEQUENCIAL_FATURA,
)


class ResCompany(models.Model):
    _inherit = 'res.company'

    own_number_type = fields.Selection(
        selection=[
            (SEQUENCIAL_EMPRESA, "Sequêncial único por empresa"),
            (SEQUENCIAL_FATURA, "Numero sequêncial da Fatura"),
            (SEQUENCIAL_CARTEIRA, "Sequêncial único por carteira"),
        ],
        string="Tipo de nosso número",
        default=SEQUENCIAL_FATURA,
    )

    own_number_sequence = fields.Many2one(
        comodel_name="ir.sequence", string="Sequência do Nosso Número"
    )

    environment = fields.Selection(
        string="Ambiente",
        selection=[("1", "HOMOLOGAÇÃO"), ("2", "PRODUÇÃO")],
        default="1",
    )

    @api.multi
    def get_own_number_sequence(self):
        self.ensure_one()
        return self.own_number_sequence.next_by_id()
