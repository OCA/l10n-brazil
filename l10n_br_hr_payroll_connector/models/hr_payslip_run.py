from openerp import models, api
from openerp.addons.l10n_br_hr_payroll.models.profiling import (
    clear_prof_data,
    log_prof_data
)
import logging

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.session import ConnectorSession

_logger = logging.getLogger(__name__)


class HrPayslipRun(models.Model):
    _inherit = "hr.payslip.run"

    @api.multi
    def gerar_holerites(self):
        session = ConnectorSession(
            self.env.cr, self.env.uid, self.env.context)
        for contrato in self.contract_id:
            job_gerar_holerite.delay(session, self.id, contrato.id)
        self.verificar_holerites_gerados()
        self.busca_holerite_orfao()


@job
def job_gerar_holerite(session, lote_id, contrato_id):
    lote = session.env['hr.payslip.run'].browse(lote_id)
    clear_prof_data()
    contrato = session.env['hr.contract'].browse(contrato_id)
    lote._gerar_holerite(contrato)
    log_prof_data()
    clear_prof_data()
