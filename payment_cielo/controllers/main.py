# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.http import request


class CieloController(http.Controller):
    @http.route(
        "/payment/cielo/payment", type="http", auth="public", csrf=False, website=True
    )
    def cielo_payment_page(self, **kwargs):
        tx_id = kwargs.get("tx_id")
        if not tx_id:
            return request.render(
                "payment_cielo.cielo_status_simple",
                {"status": "error", "message": "ID da transação não encontrado"},
            )

        try:
            tx = request.env["payment.transaction"].sudo().browse(int(tx_id))
        except (ValueError, TypeError):
            return request.render(
                "payment_cielo.cielo_status_simple",
                {"status": "error", "message": "ID da transação inválido"},
            )

        if not tx.exists():
            return request.render(
                "payment_cielo.cielo_status_simple",
                {"status": "error", "message": "Transação não encontrada"},
            )

        return request.render(
            "payment_cielo.cielo_payment_page",
            {
                "tx": tx,
            },
        )

    @http.route(
        "/payment/cielo/s2s/create",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=True,
        website=True,
    )
    def cielo_s2s_form_process(self, **post):
        tx_id = post.get("transaction_id")
        if not tx_id:
            return "<h3>Erro: transação não informada</h3>"

        try:
            tx = request.env["payment.transaction"].sudo().browse(int(tx_id))
        except (ValueError, TypeError):
            return "<h3>Erro: ID de transação inválido</h3>"

        if not tx.exists():
            return "<h3>Erro: transação não encontrada</h3>"

        required_fields = [
            "card_number",
            "card_holder",
            "card_expiry",
            "card_cvv",
            "card_brand",
        ]
        missing_fields = [field for field in required_fields if not post.get(field)]

        if missing_fields:
            return f"<h3>Erro: campos obrigatórios não preenchidos: {', '.join(missing_fields)}</h3>"

        try:
            card_data = {
                "card_number": post.get("card_number").replace(" ", ""),
                "card_holder": post.get("card_holder"),
                "card_expiry": post.get("card_expiry"),
                "card_brand": post.get("card_brand"),
            }

            success = tx.cielo_s2s_do_transaction(card_data=card_data)

            if success:
                return request.redirect(
                    f"/payment/cielo/s2s/status/{tx.id}?status=success"
                )
            else:
                return request.redirect(
                    f"/payment/cielo/s2s/status/{tx.id}?status=error"
                )

        except Exception as e:
            tx.sudo().write(
                {
                    "state_message": str(e),
                    "date": request.env["ir.fields"].Datetime.now(),
                }
            )
            tx._set_transaction_cancel()
            return request.redirect(
                f"/payment/cielo/s2s/status/{tx.id}?status=error&message={str(e)}"
            )

    @http.route(
        "/payment/cielo/s2s/status/<int:tx_id>",
        type="http",
        auth="public",
        website=True,
    )
    def cielo_s2s_status(self, tx_id, **kwargs):
        tx = request.env["payment.transaction"].sudo().browse(tx_id)
        if not tx.exists():
            return request.render(
                "payment_cielo.cielo_status_template",
                {"message": "Transação não encontrada", "status": "error"},
            )

        status = kwargs.get("status", tx.state)
        message = kwargs.get("message", tx.state_message)

        if tx.state == "done":
            return request.render(
                "payment_cielo.cielo_status_template",
                {
                    "message": "Pagamento realizado com sucesso!",
                    "status": "success",
                    "tx": tx,
                },
            )
        elif tx.state == "authorized":
            return request.render(
                "payment_cielo.cielo_status_template",
                {
                    "message": "Pagamento autorizado com sucesso!",
                    "status": "success",
                    "tx": tx,
                },
            )
        else:
            return request.render(
                "payment_cielo.cielo_status_template",
                {
                    "message": f"Pagamento falhou: {message or 'Erro desconhecido'}",
                    "status": "error",
                    "tx": tx,
                },
            )
