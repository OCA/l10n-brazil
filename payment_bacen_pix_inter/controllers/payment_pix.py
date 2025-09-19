import base64

from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request


class PaymentPixController(http.Controller):
    @http.route("/payment/pix/<int:txid>", type="http", auth="public")
    def pix_page(self, txid, **kwargs):
        tx = (
            request.env["payment.transaction"]
            .sudo()
            .search([("id", "=", txid)], limit=1)
        )
        if not tx or not tx.bacenpix_qrcode:
            raise NotFound()

        from io import BytesIO

        import qrcode

        # Gera QR code
        qr_img = qrcode.make(tx.bacenpix_qrcode)
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        qrcode_base64 = base64.b64encode(buffer.getvalue()).decode()

        values = {
            "tx": tx,
            "qrcode_base64": qrcode_base64,
            "amount": tx.amount,
            "reference": tx.reference,
            "pix_code": tx.bacenpix_qrcode,
        }

        return request.render("payment_bacen_pix_inter.pix_inter_page_template", values)
