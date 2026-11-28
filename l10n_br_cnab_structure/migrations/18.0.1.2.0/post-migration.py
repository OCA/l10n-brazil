# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Recalcula o nome das linhas da estrutura CNAB, agora em português."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["l10n_br_cnab.line"].with_context(active_test=False).search([])._compute_name()
