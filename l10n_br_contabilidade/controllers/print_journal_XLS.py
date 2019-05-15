from openerp import http
from openerp.http import request
from openerp.addons.web.controllers.main import serialize_exception,content_disposition
import base64


class PrintJournalXLS(http.Controller):
    @http.route('/web/binary/print_journal_xls', type='http', auth="public")
    @serialize_exception
    def print_journal_xls(self, id, filename=None, **kw):
        model = 'print.journal.webkit'
        field = 'diario_xls'

        Model = request.registry[model]
        cr, uid, context = request.cr, request.uid, request.context
        fields = [field]
        res = Model.read(cr, uid, [int(id)], fields, context)[0]
        filecontent = base64.b64decode(res.get(field) or '')

        if not filecontent:
            return request.not_found()
        else:
            if not filename:
                filename = 'livro_diario.xlsx'
                return request.make_response(filecontent,
                                          [('Content-Type',
                                            'application/octet-stream'),
                                           ('Content-Disposition',
                                            content_disposition(filename))])
