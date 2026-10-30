# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from werkzeug.exceptions import Forbidden, NotFound

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import content_disposition, request

XLSX_MODELS = frozenset(
    {
        "l10n_br_dere.declaration",
        "l10n_br_dere.table.period",
        "l10n_br_dere.event",
    }
)
XLSX_MIMETYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class DereXlsxController(http.Controller):
    @http.route(
        "/l10n_br_dere/xlsx/<string:model>/<int:res_id>",
        type="http",
        auth="user",
    )
    def download_xlsx(self, model, res_id, **_kwargs):
        if model not in XLSX_MODELS:
            raise Forbidden()
        record = request.env[model].browse(res_id)
        if not record.exists():
            raise NotFound()
        try:
            record.check_access("read")
        except AccessError as err:
            raise Forbidden() from err
        data = record._dere_xlsx_bytes()
        return request.make_response(
            data,
            headers=[
                ("Content-Type", XLSX_MIMETYPE),
                (
                    "Content-Disposition",
                    content_disposition(record._dere_xlsx_filename()),
                ),
            ],
        )
