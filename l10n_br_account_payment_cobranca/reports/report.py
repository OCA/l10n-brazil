# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.api import Environment
from odoo.report.interface import report_int
from odoo.report.render import render


class ExternalPdf(render):
    def __init__(self, pdf):
        render.__init__(self)
        self.pdf = pdf
        self.output_type = "pdf"

    def _render(self):
        return self.pdf


class ReportCustom(report_int):
    """
        Custom report for return boletos
    """

    def create(self, cr, uid, ids, datas, context=False):
        if not context:
            context = {}

        env = Environment(cr, uid, {})

        active_ids = context.get("active_ids")
        active_model = context.get("active_model")

        ids_move_lines = []

        if active_model == "account.invoice":
            for invoices in env["account.invoice"].browse(active_ids):
                receivable_ids = invoices.mapped("move_line_receivable_id")
                if receivable_ids:
                    ids_move_lines = receivable_ids
        elif active_model == "account.move.line":
            ids_move_lines = env["account.move.line"].browse(active_ids)

        if not ids_move_lines:
            return False

        pdf_string = ids_move_lines.generate_boleto()
        self.obj = ExternalPdf(pdf_string)
        self.obj.render()
        return self.obj.pdf, "pdf"


ReportCustom("report.l10n_br_account_payment_boleto.report")
