# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError

GNRE_NAMESPACE = "http://www.gnre.pe.gov.br"
GNRE_VERSION = "2.00"

# Códigos do elemento itensGNRE/item/valor, conforme o layout 2.00.
VALUE_TYPE_ICMS = "11"
VALUE_TYPE_FCP = "12"

# Tipos de documento de origem da tabela do convênio.
DOCUMENT_ORIGIN_NFE = "10"


class GnreXml(models.AbstractModel):
    """Serialização do lote GNRE conforme o XSD 2.00.

    A serialização é feita com lxml em vez do `spec_driven_model`, e isso é
    provisório: os bindings da GNRE ainda não estão publicados na nfelib (ver
    akretion/nfelib#157). Quando estiverem, este modelo deve dar lugar ao
    `StackedModel` sobre os mixins `gnre20_`, que é o padrão da localização.

    A ordem dos elementos importa, porque o XSD usa `xs:sequence`. Por isso os
    métodos abaixo escrevem na ordem exata do schema, e o teste valida o
    resultado contra o XSD oficial em vez de contra uma string esperada.
    """

    _name = "l10n_br_gnre.xml"
    _description = "GNRE XML Serializer"

    def _digits(self, value):
        """Strip the mask: the XSD wants digits only in CNPJ, CPF and IE."""
        return "".join(c for c in (value or "") if c.isdigit())

    def _element(self, parent, tag, text=None, **attrs):
        from lxml import etree

        node = etree.SubElement(parent, f"{{{GNRE_NAMESPACE}}}{tag}", **attrs)
        if text is not None:
            node.text = str(text)
        return node

    def _text(self, value, size):
        """Trim to the XSD size: TString refuses leading or trailing spaces."""
        return " ".join((value or "").split())[:size].strip()

    def _state_ie(self, partner, state):
        """State tax number of the partner in the favoured state, if any.

        The GNRE IE is the registration in the favoured state (rejection 202
        of the manual), not the one of the state where the partner lives.
        """
        if partner.state_id == state and partner.l10n_br_ie_code:
            return partner.l10n_br_ie_code
        number = partner.state_tax_number_ids.filtered(lambda n: n.state_id == state)[
            :1
        ]
        return number.l10n_br_ie_code if number else False

    def _append_identification(self, parent, partner, state):
        identificacao = self._element(parent, "identificacao")
        document = self._digits(partner.vat)
        tag = "CPF" if len(document) == 11 else "CNPJ"
        self._element(identificacao, tag, document)
        # A IE vai sem mascara: o XSD exige o pattern [0-9]{2,16}.
        ie = self._digits(self._state_ie(partner, state))
        if ie:
            self._element(identificacao, "IE", ie)
        return bool(ie)

    def _municipality(self, partner):
        """TCodMunIBGE has the 5 digits of the city, without the state."""
        return self._digits(partner.city_id.ibge_code)[-5:] or False

    def _append_emitter(self, guia, company, state):
        """contribuinteEmitente, o contribuinte que recolhe.

        Who is registered in the favoured state sends only the identification.
        Who is not sends the address too (rejections 209 to 211 of the manual).
        """
        partner = company.partner_id
        emitente = self._element(guia, "contribuinteEmitente")
        registered = self._append_identification(emitente, partner, state)
        if partner.legal_name or partner.name:
            self._element(
                emitente,
                "razaoSocial",
                self._text(partner.legal_name or partner.name, 60),
            )
        if registered:
            return emitente
        address = ", ".join(p for p in (partner.street, partner.district) if p)
        if address:
            self._element(emitente, "endereco", self._text(address, 60))
        municipio = self._municipality(partner)
        if municipio:
            self._element(emitente, "municipio", municipio)
        if partner.state_id:
            self._element(emitente, "uf", partner.state_id.code)
        cep = self._digits(partner.zip)
        if len(cep) == 8:
            self._element(emitente, "cep", cep)
        phone = self._digits(partner.phone)[-11:]
        if len(phone) >= 6:
            self._element(emitente, "telefone", phone)
        return emitente

    def _append_recipient(self, item, obligation):
        """contribuinteDestinatario, required by some states for the DIFAL."""
        partner = obligation.document_id.partner_id
        if not obligation.config_id.recipient_required or not partner:
            return
        destinatario = self._element(item, "contribuinteDestinatario")
        self._append_identification(destinatario, partner, obligation.fiscal_state_id)
        if partner.legal_name or partner.name:
            self._element(
                destinatario,
                "razaoSocial",
                self._text(partner.legal_name or partner.name, 60),
            )
        municipio = self._municipality(partner)
        if municipio:
            self._element(destinatario, "municipio", municipio)

    def _append_value(self, item, value_type, amount, required=False):
        if not amount and not required:
            return
        self._element(item, "valor", f"{amount or 0.0:.2f}", tipo=value_type)

    def _append_extra_fields(self, item, obligation):
        """camposExtras that the state requires for the revenue."""
        extras = [
            (extra.code, extra._value_for(obligation))
            for extra in obligation.config_id.extra_field_ids
        ]
        extras = [(code, value) for code, value in extras if value]
        if not extras:
            return
        campos = self._element(item, "camposExtras")
        for code, value in extras:
            campo = self._element(campos, "campoExtra")
            self._element(campo, "codigo", code)
            self._element(campo, "valor", self._text(value, 100))

    def _append_item(self, itens, obligation):
        """Um item da guia, montado a partir de uma obrigação.

        A ordem segue o xs:sequence do XSD: receita, detalhamentoReceita,
        documentoOrigem, produto, referencia, dataVencimento, valor, convenio,
        contribuinteDestinatario, camposExtras, numeroControle.
        """
        config = obligation.config_id
        item = self._element(itens, "item")
        self._element(item, "receita", obligation.revenue_code)
        if obligation.detail_revenue_code:
            self._element(item, "detalhamentoReceita", obligation.detail_revenue_code)
        document = obligation.document_id
        if document and document.document_key:
            self._element(
                item,
                "documentoOrigem",
                document.document_key,
                tipo=config.origin_document_type or DOCUMENT_ORIGIN_NFE,
            )
        if obligation.period_ref and config.period_reference:
            referencia = self._element(item, "referencia")
            self._element(referencia, "periodo", obligation.config_id.period or "0")
            self._element(referencia, "mes", obligation.period_ref[:2])
            self._element(referencia, "ano", obligation.period_ref[2:])
        if obligation.date_due:
            self._element(
                item, "dataVencimento", obligation.date_due.strftime("%Y-%m-%d")
            )
        # ICMS e FCP são dois valores do MESMO item, não itens separados.
        self._append_value(item, VALUE_TYPE_ICMS, obligation.amount_principal)
        self._append_value(
            item, VALUE_TYPE_FCP, obligation.amount_fcp, required=config.fcp_required
        )
        if config.convenio:
            self._element(item, "convenio", self._text(config.convenio, 30))
        self._append_recipient(item, obligation)
        self._append_extra_fields(item, obligation)
        return item

    def _append_guide(self, guias, guide):
        from lxml import etree

        obligations = guide.gnre_obligation_ids
        if not obligations:
            raise UserError(
                _("A guia %(name)s não tem obrigações.", name=guide.display_name)
            )

        guia = etree.SubElement(
            guias, f"{{{GNRE_NAMESPACE}}}TDadosGNRE", versao=GNRE_VERSION
        )
        self._element(guia, "ufFavorecida", guide.gnre_fiscal_state_id.code)
        self._element(guia, "tipoGnre", guide.gnre_type)
        self._append_emitter(guia, guide.company_id, guide.gnre_fiscal_state_id)
        itens = self._element(guia, "itensGNRE")
        for obligation in obligations:
            self._append_item(itens, obligation)
        total = sum(obligations.mapped("amount_total"))
        self._element(guia, "valorGNRE", f"{total:.2f}")
        due_dates = [d for d in obligations.mapped("date_due") if d]
        if due_dates and any(obligations.mapped("config_id.payment_date_required")):
            self._element(guia, "dataPagamento", min(due_dates).strftime("%Y-%m-%d"))
        return guia

    def build_lote(self, guides):
        """Return the `TLote_GNRE` element carrying the given guides."""
        from lxml import etree

        if not guides:
            raise UserError(_("Nenhuma guia para montar o lote."))

        lote = etree.Element(
            f"{{{GNRE_NAMESPACE}}}TLote_GNRE",
            versao=GNRE_VERSION,
            nsmap={None: GNRE_NAMESPACE},
        )
        guias = self._element(lote, "guias")
        for guide in guides:
            self._append_guide(guias, guide)
        return lote

    def render_lote(self, guides):
        """Return the `TLote_GNRE` XML as text, ready to be signed or sent."""
        from lxml import etree

        return etree.tostring(
            self.build_lote(guides), encoding="unicode", pretty_print=True
        )
