# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models
from odoo.exceptions import UserError

from ..constants import (
    REINF_ENVIRONMENTS,
    REINF_INSCRIPTION_CNPJ,
    REINF_INSCRIPTION_CPF,
)

# Number of positions of the CNPJ root, which is what the EFD-Reinf calls the
# inscription of the taxpayer when tpInsc is 1.
CNPJ_ROOT_LENGTH = 8


class ResCompany(models.Model):
    _inherit = "res.company"

    reinf_environment = fields.Selection(
        selection=REINF_ENVIRONMENTS,
        string="EFD-Reinf Environment",
        help="tpAmb of the EFD-Reinf events of this company. It has no default "
        "on purpose: choosing between production and restricted production is a "
        "decision of the taxpayer, and a wrong guess sends real data to the "
        "wrong environment. It is required to transmit anything.",
    )

    reinf_class_trib = fields.Char(
        string="EFD-Reinf Taxpayer Classification",
        size=2,
        help="classTrib of the R-1000: the classification of the taxpayer, in "
        "2 digits, as listed in the table of classifications of the manual of "
        "the EFD-Reinf.",
    )

    reinf_ind_escrituracao = fields.Boolean(
        string="Obligated to the ECD",
        help="indEscrituracao of the R-1000: whether the taxpayer is obligated "
        "to keep its accounting books in the ECD.",
    )

    reinf_ind_desoneracao = fields.Boolean(
        string="Payroll Relief (CPRB)",
        help="indDesoneracao of the R-1000: whether the payroll of the taxpayer "
        "is relieved by the social contribution on gross revenue.",
    )

    reinf_ind_acordo_isen_multa = fields.Boolean(
        string="International Agreement on Fines",
        help="indAcordoIsenMulta of the R-1000: whether an international "
        "agreement exempts the taxpayer from fines.",
    )

    reinf_contact_id = fields.Many2one(
        comodel_name="res.partner",
        string="EFD-Reinf Contact",
        help="Person the tax authority contacts about the EFD-Reinf. The "
        "R-1000 asks for the name and the CPF, so the partner needs a CPF.",
    )

    def _reinf_environment(self):
        """Return the environment to transmit with, or refuse to transmit.

        The environment is never guessed. Whoever calls a transmission asks
        here, so the answer is the same everywhere.
        """
        self.ensure_one()
        if not self.reinf_environment:
            raise UserError(
                _(
                    "The EFD-Reinf environment of the company %s is not set. "
                    "Choose between production and restricted production in the "
                    "company form before transmitting.",
                    self.display_name,
                )
            )
        # TODO In the transmission phase, this is where the lock against
        # transmitting to production from a restored database belongs: compare
        # the database identity with the one the environment was chosen in,
        # the way the neutralize of Odoo does.
        return self.reinf_environment

    def _reinf_inscription(self):
        """Return the (tpInsc, nrInsc) pair of the taxpayer.

        For a company the EFD-Reinf takes the root of the CNPJ, which is the
        first 8 positions, and not the whole number.
        """
        self.ensure_one()
        # cnpj_cpf_stripped of l10n_br_base already drops the mask and keeps the
        # letters of an alphanumeric CNPJ.
        digits = (self.cnpj_cpf_stripped or "").upper()
        if not digits:
            raise UserError(
                _(
                    "The company %s has no CNPJ or CPF, so no EFD-Reinf event "
                    "can be identified.",
                    self.display_name,
                )
            )
        if len(digits) > 11:
            return REINF_INSCRIPTION_CNPJ, digits[:CNPJ_ROOT_LENGTH]
        return REINF_INSCRIPTION_CPF, digits
