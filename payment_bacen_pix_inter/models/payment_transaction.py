import base64
import json
import logging
import re
import tempfile

from requests import Session

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

PIX_SCOPE = {
    "pix_add": "cob.write",
    "pix_get": "cob.read",
}


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    # Campos PIX Inter
    bacenpix_txid = fields.Char("TXID Pix Inter", readonly=True)
    pix_qrcode = fields.Text("Copia e Cola PIX", readonly=True)
    pix_location = fields.Char("Location PIX", readonly=True)
    inter_pix_status = fields.Selection(
        [
            ("ATIVA", "Ativa"),
            ("CONCLUIDA", "Concluída"),
            ("REMOVIDA_PELO_USUARIO_RECEBEDOR", "Removida"),
            ("REMOVIDA_PELO_PSP", "Removida pelo PSP"),
        ],
        string="Status PIX",
        readonly=True,
    )

    def _inter_get_api_url(self, provider_id):
        """
        Retorna a URL base da API do Banco Inter
        com base no estado do provider.
        """
        if provider_id.state == "test":
            return "https://cdpj-sandbox.partners.uatinter.co/"
        elif provider_id.state == "enabled":
            return "https://cdpj.partners.bancointer.com.br/"
        return ""

    def _generate_pix_cert_files(self, provider_id):
        """Gera arquivos temporários de certificado e chave privada"""
        cert = base64.b64decode(provider_id.bacenpix_certificate)
        key = (
            base64.b64decode(provider_id.bacenpix_private_key)
            if provider_id.bacenpix_private_key
            else None
        )
        cert_path = tempfile.mkstemp()[1]
        with open(cert_path, "wb") as f:
            f.write(cert)

        if key:
            key_path = tempfile.mkstemp()[1]
            with open(key_path, "wb") as f:
                f.write(key)
            return (cert_path, key_path)
        return cert_path

    def _prepare_pix_session_request(self, provider_id):
        """Prepara sessão HTTP com certificados"""
        session = Session()
        session.verify = True
        session.cert = self._generate_pix_cert_files(provider_id)
        return session

    def _generate_pix_header(self, token, provider_id):
        """Gera headers para requisições da API"""
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

    def _get_pix_token(self, provider_id, scope):
        """
        Gera token específico para PIX com escopo fornecido
        """
        _logger.info("Obtendo token PIX para escopo: %s", scope)
        base_url = self._inter_get_api_url(provider_id)
        url = base_url + "oauth/v2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        body = {
            "client_id": provider_id.bacenpix_client_id,
            "client_secret": provider_id.bacenpix_client_secret,
            "scope": PIX_SCOPE[scope],
            "grant_type": "client_credentials",
        }

        session = self._prepare_pix_session_request(provider_id)
        response = session.post(url, headers=headers, data=body, timeout=30)

        try:
            response.raise_for_status()
            token_data = response.json()
            token = token_data.get("access_token")
            if not token:
                raise UserError(_("Token PIX não encontrado na resposta da API"))
            _logger.info("Token PIX gerado com sucesso para escopo: %s", scope)
            return token
        except Exception as e:
            _logger.error("Erro ao obter token PIX: %s", str(e))
            raise UserError(_(f"Erro ao obter token PIX: {str(e)}")) from e

    def _prepare_pix_data_inter(self):
        """Monta payload para criar cobrança PIX"""
        invoice = self.invoice_ids[0] if self.invoice_ids else None

        if not invoice:
            raise UserError(
                _("Não é possível gerar PIX sem fatura ou pedido associado")
            )

        partner = (invoice.partner_id if invoice else None).commercial_partner_id

        valor = round(float(self.amount), 2)
        expiracao_segundos = 3600  # 1 hora

        # Monta dados do devedor baseado no tipo de pessoa
        if partner.is_company:
            devedor_data = {
                "cnpj": re.sub(r"\D", "", partner.cnpj_cpf or ""),
                "nome": partner.legal_name or partner.name,
            }
        else:
            devedor_data = {
                "cpf": re.sub(r"\D", "", partner.cnpj_cpf or ""),
                "nome": partner.legal_name or partner.name,
            }

        pix_data = {
            "calendario": {"expiracao": expiracao_segundos},
            "valor": {"original": f"{valor:.2f}"},
            "chave": self.provider_id.bacen_pix_key,
            "devedor": devedor_data,
            "solicitacaoPagador": f"Pagamento ref {self.reference or self.id}",
        }

        return pix_data

    def generate_pix(self):
        """Gera cobrança PIX compatível com Banco Inter"""
        self.ensure_one()

        if self.provider_code != "inter_pix":
            return super().generate_pix()

        if self.state not in ["draft", "pending"]:
            raise UserError(
                _("PIX só pode ser gerado para transações em rascunho ou pendentes")
            )

        try:
            pix_data = self._prepare_pix_data_inter()
            response = self.add_pix_inter(self.provider_id, pix_data)

            if not response or "txid" not in response:
                raise UserError(_("Resposta do banco não contém TXID do PIX"))

            # Salva dados retornados
            self.write(
                {
                    "bacenpix_txid": response["txid"],
                    "bacenpix_location": response.get("location"),
                    "bacenpix_qrcode": response.get("pixCopiaECola"),
                    "inter_pix_status": response.get("status", "ATIVA"),
                    "state": "pending",
                }
            )

            _logger.info(
                "Cobrança PIX Inter gerada com sucesso. TXID: %s",
                self.bacenpix_txid,
            )

            return response

        except Exception as e:
            _logger.error("Erro ao gerar PIX Inter: %s", str(e), exc_info=True)
            raise UserError(_(f"Erro ao gerar PIX Inter: {str(e)}")) from e

    def add_pix_inter(self, provider_id, vals):
        """Cria cobrança Pix imediata usando API V2"""
        token = self._get_pix_token(provider_id, "pix_add")
        base_url = self._inter_get_api_url(provider_id)
        url = base_url + "pix/v2/cob"
        headers = self._generate_pix_header(token, provider_id)
        session = self._prepare_pix_session_request(provider_id)

        try:
            _logger.info("Enviando cobrança PIX para: %s", url)
            _logger.info("Payload PIX: %s", json.dumps(vals, indent=2))

            response = session.post(url, headers=headers, json=vals, timeout=30)
            _logger.info("Resposta HTTP PIX: %s", response.status_code)
            _logger.info("Resposta texto PIX: %s", response.text)

            if response.status_code in [200, 201]:
                return response.json()
            elif response.status_code == 400:
                raise UserError(_(f"Erro nos dados PIX enviados: {response.text}"))
            elif response.status_code == 401:
                raise UserError(
                    _("Erro de autorização ao acessar a API PIX do Banco Inter")
                )
            else:
                raise UserError(
                    _(
                        f"Erro da API PIX do Banco Inter "
                        f"({response.status_code}): {response.text}"
                    )
                )
        except Exception as e:
            _logger.error("Erro ao criar cobrança PIX: %s", str(e), exc_info=True)
            raise UserError(_(f"Erro ao criar cobrança PIX: {str(e)}")) from e

    def get_pix_inter(self, provider_id, txid):
        """Consulta uma cobrança PIX pelo TXID"""
        token = self._get_pix_token(provider_id, "pix_get")
        base_url = self._inter_get_api_url(provider_id)
        url = base_url + f"pix/v2/cob/{txid}"
        headers = self._generate_pix_header(token, provider_id)
        session = self._prepare_pix_session_request(provider_id)

        try:
            _logger.info("Consultando cobrança PIX para TXID: %s", txid)
            response = session.get(url, headers=headers, timeout=30)
            _logger.info("Resposta HTTP PIX GET: %s", response.status_code)
            _logger.info("Resposta texto PIX GET: %s", response.text)

            if response.status_code in [200, 201]:
                data = response.json()

                # Atualiza status local se for a própria transação
                if self.bacenpix_txid == txid:
                    current_status = data.get("status")
                    if current_status:
                        self.inter_pix_status = current_status

                        # Atualiza estado da transação baseado no status PIX
                        if current_status == "CONCLUIDA":
                            self._set_done()
                        elif current_status in [
                            "REMOVIDA_PELO_USUARIO_RECEBEDOR",
                            "REMOVIDA_PELO_PSP",
                        ]:
                            self._set_canceled()

                return data

            elif response.status_code == 404:
                raise UserError(_(f"Cobrança PIX não encontrada para TXID {txid}"))
            elif response.status_code == 401:
                raise UserError(
                    _("Erro de autorização ao consultar PIX no Banco Inter")
                )
            else:
                raise UserError(
                    _(
                        f"Erro ao consultar PIX no Banco Inter "
                        f"({response.status_code}): {response.text}"
                    )
                )
        except Exception as e:
            _logger.error("Erro ao consultar cobrança PIX: %s", str(e), exc_info=True)
            raise UserError(_(f"Erro ao consultar PIX: {str(e)}")) from e

    def _get_processing_values(self):
        """Override para adicionar valores específicos do PIX"""
        res = super()._get_processing_values()

        if self.provider_code == "inter_pix":
            if not self.bacenpix_txid:
                self.generate_pix()

            if not self.bacenpix_txid:
                raise UserError(_("Cobrança PIX não disponível"))

            pix_url = f"/payment/pix/{self.id}"
            res.update(
                {
                    "redirect_url": pix_url,
                    "redirect_method": "GET",
                    "state": "pending",
                    "is_processed": True,
                    "redirect_form_html": self.env["ir.ui.view"]._render_template(
                        "payment_bacen_pix_inter.pix_inter_redirect_template",
                        {
                            "redirect_url": pix_url,
                            "reference": self.reference,
                            "bacenpix_qrcode": self.bacenpix_qrcode,
                            "amount": self.amount,
                        },
                    ),
                }
            )

        _logger.info("Valores de processamento PIX: %s", res)
        return res

    @api.model
    def _cron_update_pix_status(self):
        """Cron job para atualizar status das cobranças PIX pendentes"""
        pending_pix_transactions = self.search(
            [
                ("provider_code", "=", "inter_pix"),
                ("state", "in", ["draft", "pending"]),
                ("bacenpix_txid", "!=", False),
                ("inter_pix_status", "in", ["ATIVA"]),
            ]
        )

        for transaction in pending_pix_transactions:
            try:
                transaction.get_pix_inter(
                    transaction.provider_id, transaction.bacenpix_txid
                )
            except Exception as e:
                _logger.error(
                    "Erro ao atualizar status PIX da transação %s: %s",
                    transaction.id,
                    str(e),
                )

    def action_update_pix_status(self):
        """Action para atualizar status PIX manualmente"""
        self.ensure_one()

        if not self.bacenpix_txid:
            raise ValidationError(_("Transação não possui TXID do PIX"))

        if self.provider_code != "inter_pix":
            raise ValidationError(
                _("Esta ação é apenas para transações PIX do Banco Inter")
            )

        return self.get_pix_inter(self.provider_id, self.bacenpix_txid)

    def action_create_pix(self):
        """Action para criar cobrança PIX manualmente"""
        self.ensure_one()

        if self.state not in ["draft"]:
            raise ValidationError(_("PIX só pode ser criado em transações em rascunho"))

        if self.provider_code != "inter_pix":
            raise ValidationError(
                _("Este método é apenas para transações PIX do Banco Inter")
            )

        return self.generate_pix()

    @api.model
    def create(self, vals):
        """Override create para processar PIX automaticamente"""
        transaction = super().create(vals)

        # Se for transação PIX, pode criar automaticamente dependendo da configuração
        if (
            transaction.provider_code == "inter_pix"
            and transaction.operation == "online_redirect"
            and transaction.state == "draft"
        ):
            # A geração do PIX será feita no _get_processing_values quando necessário
            pass

        return transaction
