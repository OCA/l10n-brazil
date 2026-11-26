# Copyright (C) 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# Copyright (C) 2026 - TODAY, KMEE (<https://kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

from ..constants.duimp import DUIMP_ENVIRONMENT_SELECTION, DUIMP_ENVIRONMENT_VALIDATION
from .duimp_webservice import DuimpInMemoryTokenStore, DuimpWebservice


class ResCompany(models.Model):
    _inherit = "res.company"

    duimp_environment = fields.Selection(
        selection=DUIMP_ENVIRONMENT_SELECTION,
        string="DUIMP Environment (Siscomex)",
        default=DUIMP_ENVIRONMENT_VALIDATION,
    )

    import_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Import Fiscal Operation",
        domain=[("state", "=", "approved")],
        help="Default fiscal operation used when generating the vendor "
        "bill from a DUIMP.",
    )

    def _get_duimp_webservice(self):
        self.ensure_one()
        certificate = self.sudo()._get_br_ecertificate(only_ecpf=True)
        environment = self.duimp_environment or DUIMP_ENVIRONMENT_VALIDATION
        token_store = DuimpInMemoryTokenStore(f"{self.id}.{environment}")
        return DuimpWebservice(
            certificate=certificate,
            environment=environment,
            token_store=token_store,
        )
