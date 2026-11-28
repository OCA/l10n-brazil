# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

GNRE_DOCUMENT_TYPE = "23"

# Códigos de valor do layout 2.00, elemento itensGNRE/item/valor.
VALUE_TYPE_ICMS = "11"
VALUE_TYPE_FCP = "12"

# Modalidades do elemento tipoGnre.
GNRE_TYPE_SIMPLE = "0"
GNRE_TYPE_MULTI_DOCUMENT = "1"
GNRE_TYPE_MULTI_REVENUE = "2"


_logger = logging.getLogger(__name__)

GNRE_TRANSMISSION_STATE = [
    ("draft", "Não transmitida"),
    ("sent", "Enviada"),
    ("pending", "Pendente no portal"),
    ("processed", "Processada"),
    ("rejected", "Rejeitada"),
]

# Recepção do lote (manual, item 4.1.6): 100 é o lote recebido.
RECEPTION_OK = "100"

# Situação do processamento do lote (manual, quadro IV).
LOT_WAITING = ("400", "401")
LOT_DONE = ("402", "403")
LOT_ERROR = "404"

# Situação de cada guia no resultado (lote_gnre_result_v2.00).
GUIDE_PROCESSED = "0"
GUIDE_PENDING = "4"

# O portal descarta mensagens acima de 600 KB (manual, item 4.1.5).
GNRE_MAX_MESSAGE_SIZE = 600 * 1024

# Limites do lote publicados na página Automação do portal GNRE.
GNRE_MAX_GUIDES_PER_LOT = 50
GNRE_MAX_ITEMS_PER_LOT = 300


def _value(node):
    """Plain text of an enum, a string or an xsdata wildcard.

    The portal answers wrap enums in elements that carry attributes, such as
    the extra field type: an object whose value is an enum whose value is the
    text, so the unwrapping goes down to the text.
    """
    if node is None:
        return False
    value = node
    while not isinstance(value, str | bytes) and hasattr(value, "value"):
        value = value.value
    if hasattr(value, "text"):
        value = value.text
    if isinstance(value, bytes):
        value = value.decode()
    return value if isinstance(value, str) else str(value)


class Document(models.Model):
    """A guia GNRE, materializada como documento fiscal do tipo 23.

    A guia não tem linhas de produto: o que ela tem são itens, e cada item vem
    de uma obrigação de recolhimento. As notas que originaram os itens ficam em
    `document_related_ids`, que é o mecanismo que a localização já usa para
    documentos referenciados.
    """

    _inherit = "l10n_br_fiscal.document"

    gnre_obligation_ids = fields.One2many(
        comodel_name="l10n_br_gnre.obligation",
        inverse_name="guide_id",
        string="Obrigações",
        readonly=True,
    )

    gnre_obligation_count = fields.Integer(
        compute="_compute_gnre_obligation_count",
    )

    gnre_fiscal_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="UF Favorecida",
        readonly=True,
        help="Uma guia atende uma única UF favorecida.",
    )

    gnre_type = fields.Selection(
        selection=[
            (GNRE_TYPE_SIMPLE, "GNRE Simples"),
            (GNRE_TYPE_MULTI_DOCUMENT, "GNRE Múltiplos Documentos de Origem"),
            (GNRE_TYPE_MULTI_REVENUE, "GNRE Múltiplas Receitas"),
        ],
        string="Tipo da GNRE",
        readonly=True,
    )

    @api.depends("gnre_obligation_ids")
    def _compute_gnre_obligation_count(self):
        for record in self:
            record.gnre_obligation_count = len(record.gnre_obligation_ids)

    @api.model
    def _gnre_document_type(self):
        document_type = self.env["l10n_br_fiscal.document.type"].search(
            [("code", "=", GNRE_DOCUMENT_TYPE)], limit=1
        )
        if not document_type:
            raise UserError(_("Tipo de documento fiscal 23 (GNRE) não encontrado."))
        return document_type

    @api.model
    def _gnre_type_for(self, obligations):
        """Pick the tipoGnre that matches what is actually in the guide."""
        documents = obligations.mapped("document_id")
        revenues = set(obligations.mapped("revenue_code"))
        if len(revenues) > 1:
            return GNRE_TYPE_MULTI_REVENUE
        if len(documents) > 1:
            return GNRE_TYPE_MULTI_DOCUMENT
        return GNRE_TYPE_SIMPLE

    @api.model
    def _prepare_gnre_guide(self, obligations):
        first = obligations[0]
        return {
            "company_id": first.company_id.id,
            "document_type_id": self._gnre_document_type().id,
            "document_date": fields.Datetime.now(),
            "partner_id": first.authority_partner_id.id,
            "gnre_fiscal_state_id": first.fiscal_state_id.id,
            "gnre_type": self._gnre_type_for(obligations),
        }

    @api.model
    def _create_gnre_guide(self, obligations):
        """Turn a batch of obligations into one guide.

        The batch is expected to come from `group_for_guides`, which already
        guarantees a single favoured state, a coherent due date and at most
        100 items.
        """
        if not obligations:
            raise UserError(_("Nenhuma obrigação para gerar a guia."))

        states = obligations.mapped("fiscal_state_id")
        if len(states) > 1:
            raise UserError(_("Uma guia não pode misturar mais de uma UF favorecida."))

        guide = self.create(self._prepare_gnre_guide(obligations))
        guide._gnre_reference_origin(obligations)
        obligations.write({"guide_id": guide.id, "state": "grouped"})
        return guide

    def _gnre_reference_origin(self, obligations):
        """Link the notes that originated the items to this guide."""
        self.ensure_one()
        related = self.env["l10n_br_fiscal.document.related"]
        for document in obligations.mapped("document_id"):
            related.create(
                {
                    "document_id": self.id,
                    "document_related_id": document.id,
                    "document_type_id": document.document_type_id.id,
                    "document_serie": document.document_serie,
                    "document_number": document.document_number,
                    "document_date": document.document_date,
                    "document_key": document.document_key,
                }
            )

    def action_view_gnre_obligations(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Obrigações"),
            "res_model": "l10n_br_gnre.obligation",
            "view_mode": "tree,form",
            "domain": [("guide_id", "=", self.id)],
        }

    def action_gnre_render_xml(self):
        """Return the lote XML for the selected guides."""
        return self.env["l10n_br_gnre.xml"].render_lote(self)

    gnre_transmission_state = fields.Selection(
        selection=GNRE_TRANSMISSION_STATE,
        string="Situação no Portal",
        default="draft",
        readonly=True,
        copy=False,
    )

    gnre_environment = fields.Selection(
        related="company_id.gnre_environment",
    )

    gnre_receipt_number = fields.Char(
        string="Recibo do Lote", readonly=True, copy=False
    )

    gnre_receipt_date = fields.Char(string="Data do Recibo", readonly=True, copy=False)

    gnre_lot_position = fields.Integer(readonly=True, copy=False)

    gnre_status_code = fields.Char(
        string="Código do Retorno", readonly=True, copy=False
    )

    gnre_status_message = fields.Char(
        string="Mensagem do Retorno", readonly=True, copy=False
    )

    gnre_rejection = fields.Text(
        string="Motivos da Rejeição", readonly=True, copy=False
    )

    gnre_digitable_line = fields.Char(
        string="Linha Digitável", readonly=True, copy=False
    )

    gnre_bar_code = fields.Char(string="Código de Barras", readonly=True, copy=False)

    gnre_pix_payload = fields.Char(string="Pix Copia e Cola", readonly=True, copy=False)

    gnre_payment_due = fields.Char(
        string="Data Limite de Pagamento", readonly=True, copy=False
    )

    gnre_pdf_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="PDF da Guia",
        readonly=True,
        copy=False,
    )

    def _gnre_guides(self):
        document_type = self._gnre_document_type()
        return self.filtered(lambda d: d.document_type_id == document_type)

    def _gnre_client(self):
        """Return the nfelib GNRE client for the company of the guides."""
        return self.company_id._gnre_client()

    def _gnre_attach(self, name, data, mimetype):
        self.ensure_one()
        if isinstance(data, str):
            data = data.encode()
        return self.env["ir.attachment"].create(
            {
                "name": name,
                "res_model": self._name,
                "res_id": self.id,
                "raw": data,
                "mimetype": mimetype,
            }
        )

    def _gnre_attach_exchange(self, client, label):
        """Keep the XML sent and received, as the edocs of the localization do."""
        for guide in self:
            for kind, data in (
                ("envio", getattr(client, "last_request_xml", None)),
                ("retorno", getattr(client, "last_response_xml", None)),
            ):
                if data:
                    guide._gnre_attach(
                        f"gnre-{label}-{kind}-{guide.id}.xml", data, "application/xml"
                    )

    def _gnre_split_lots(self):
        """Split the guides in lotes within the limits of the portal.

        The Automação page of the portal admits at most 50 guides and 300 items
        per lote (100 items per guide is already enforced when grouping).
        """
        lots = []
        lot = self.browse()
        items = 0
        for guide in self:
            count = len(guide.gnre_obligation_ids)
            if lot and (
                len(lot) >= GNRE_MAX_GUIDES_PER_LOT
                or items + count > GNRE_MAX_ITEMS_PER_LOT
            ):
                lots.append(lot)
                lot = self.browse()
                items = 0
            lot |= guide
            items += count
        if lot:
            lots.append(lot)
        return lots

    def action_gnre_transmit(self):
        """Send the selected guides, one lote per portal limit, keeping receipts."""
        guides = self._gnre_guides().filtered(
            lambda g: g.gnre_transmission_state in ("draft", "rejected")
        )
        if not guides:
            raise UserError(_("Nenhuma guia GNRE para transmitir."))
        if len(guides.company_id) > 1:
            raise UserError(_("Um lote de GNRE não pode misturar empresas."))
        results = [lot._gnre_send_lot() for lot in guides._gnre_split_lots()]
        return all(results)

    def _gnre_send_lot(self):
        guides = self
        xml = self.env["l10n_br_gnre.xml"].render_lote(guides)
        if len(xml.encode()) > GNRE_MAX_MESSAGE_SIZE:
            raise UserError(
                _("O lote passa de 600 KB, o limite do portal. Envie menos guias.")
            )

        client = guides._gnre_client()
        try:
            receipt = client.envia_lote(xml)
        except Exception as error:  # the portal answer is kept, not raised
            _logger.warning("GNRE transmission failed: %s", error)
            guides.write(
                {
                    "gnre_transmission_state": "rejected",
                    "gnre_status_code": False,
                    "gnre_status_message": str(error)[:255],
                }
            )
            return False
        guides._gnre_attach_exchange(client, "lote")
        guides._gnre_process_receipt(receipt)
        return True

    def _gnre_process_receipt(self, receipt):
        situation = receipt.situacaoRecepcao
        code = _value(situation.codigo) if situation else False
        message = _value(situation.descricao) if situation else False
        if code != RECEPTION_OK or not receipt.recibo:
            self.write(
                {
                    "gnre_transmission_state": "rejected",
                    "gnre_status_code": code,
                    "gnre_status_message": message,
                }
            )
            return
        for position, guide in enumerate(self):
            guide.write(
                {
                    "gnre_transmission_state": "sent",
                    "gnre_receipt_number": _value(receipt.recibo.numero),
                    "gnre_receipt_date": _value(receipt.recibo.dataHoraRecibo),
                    "gnre_lot_position": position,
                    "gnre_status_code": code,
                    "gnre_status_message": message,
                    "gnre_rejection": False,
                }
            )

    def action_gnre_check_result(self):
        """Read the result of the lotes of the selected guides."""
        guides = self._gnre_guides().filtered(
            lambda g: g.gnre_transmission_state in ("sent", "pending")
            and g.gnre_receipt_number
        )
        if not guides:
            raise UserError(_("Nenhuma guia GNRE aguardando o resultado do lote."))
        for receipt_number in set(guides.mapped("gnre_receipt_number")):
            lot = guides.filtered(
                lambda g, number=receipt_number: g.gnre_receipt_number == number
            ).sorted("gnre_lot_position")
            client = lot._gnre_client()
            try:
                result = client.consulta_lote(receipt_number, incluir_pdf_guias=True)
            except Exception as error:  # try again on the next check
                _logger.warning("GNRE result query failed: %s", error)
                lot.write({"gnre_status_message": str(error)[:255]})
                continue
            lot._gnre_attach_exchange(client, "resultado")
            lot._gnre_process_result(result)
        return True

    def _gnre_process_result(self, result):
        situation = result.situacaoProcess
        code = _value(situation.codigo) if situation else False
        message = _value(situation.descricao) if situation else False
        values = {"gnre_status_code": code, "gnre_status_message": message}
        if code in LOT_WAITING or not result.resultado:
            self.write(values)
            return
        if code == LOT_ERROR or code not in LOT_DONE:
            self.write(dict(values, gnre_transmission_state="rejected"))
            return

        pdf = _value(result.resultado.pdfGuias)
        results = result.resultado.guia
        for guide in self:
            found = guide._gnre_match_result(results)
            if not found:
                guide.write(dict(values, gnre_transmission_state="pending"))
                continue
            guide._gnre_apply_guide_result(found, values, pdf)

    def _gnre_match_result(self, results):
        """Find the result of this guide in the lote.

        The portal answers in the order of the lote; state and amount are
        checked so a reordered answer never lands on the wrong guide.
        """
        self.ensure_one()

        def same(found):
            state = _value(found.ufFavorecida)
            amount = _value(found.valorGNRE)
            if state and state != self.gnre_fiscal_state_id.code:
                return False
            total = sum(self.gnre_obligation_ids.mapped("amount_total"))
            return not amount or abs(float(amount) - total) < 0.005

        position = self.gnre_lot_position
        if position < len(results) and same(results[position]):
            return results[position]
        return next((found for found in results if same(found)), False)

    def _gnre_apply_guide_result(self, found, values, pdf):
        self.ensure_one()
        situation = _value(found.situacaoGuia)
        reasons = []
        if found.motivosRejeicao:
            for reason in found.motivosRejeicao.motivo:
                field_name = _value(getattr(reason, "campo", None))
                reasons.append(
                    " ".join(
                        p
                        for p in (
                            _value(reason.codigo),
                            _value(reason.descricao),
                            f"({field_name})" if field_name else "",
                        )
                        if p
                    )
                )
        values = dict(
            values,
            gnre_rejection="\n".join(reasons) or False,
            gnre_digitable_line=_value(found.linhaDigitavel),
            gnre_bar_code=_value(found.codigoBarras),
            gnre_pix_payload=_value(found.qrcodePayload),
            gnre_payment_due=_value(found.dataLimitePagamento),
        )
        if situation == GUIDE_PROCESSED:
            values["gnre_transmission_state"] = "processed"
            if pdf:
                values["gnre_pdf_id"] = self._gnre_attach(
                    f"gnre-{self.id}.pdf", base64.b64decode(pdf), "application/pdf"
                ).id
            self.gnre_obligation_ids.write({"state": "transmitted"})
        elif situation == GUIDE_PENDING:
            values["gnre_transmission_state"] = "pending"
        else:
            values["gnre_transmission_state"] = "rejected"
        self.write(values)

    def action_gnre_download_pdf(self):
        self.ensure_one()
        if not self.gnre_pdf_id:
            raise UserError(_("O portal ainda não devolveu o PDF desta guia."))
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{self.gnre_pdf_id.id}?download=true",
            "target": "self",
        }

    def _cron_gnre_check_results(self):
        """Poll the lotes still waiting for the portal, one company at a time."""
        guides = self.search(
            [
                ("gnre_transmission_state", "in", ("sent", "pending")),
                ("gnre_receipt_number", "!=", False),
            ]
        )
        for company in guides.company_id:
            company_guides = guides.filtered(lambda g, c=company: g.company_id == c)
            company_guides.with_company(company).action_gnre_check_result()
