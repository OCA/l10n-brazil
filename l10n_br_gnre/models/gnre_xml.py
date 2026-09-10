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

    def _append_emitter(self, guia, company):
        """contribuinteEmitente, o contribuinte que recolhe."""
        partner = company.partner_id
        emitente = self._element(guia, "contribuinteEmitente")
        identificacao = self._element(emitente, "identificacao")
        self._element(identificacao, "CNPJ", self._digits(partner.cnpj_cpf))
        # A IE vai sem mascara: o XSD exige o pattern [0-9]{2,16}.
        if partner.inscr_est:
            self._element(identificacao, "IE", self._digits(partner.inscr_est))
        if partner.legal_name or partner.name:
            self._element(
                emitente, "razaoSocial", (partner.legal_name or partner.name)[:60]
            )

    def _append_value(self, item, value_type, amount):
        if not amount:
            return
        self._element(item, "valor", f"{amount:.2f}", tipo=value_type)

    def _append_item(self, itens, obligation):
        """Um item da guia, montado a partir de uma obrigação.

        A ordem segue o xs:sequence do XSD: receita, detalhamentoReceita,
        documentoOrigem, produto, referencia, dataVencimento, valor, convenio,
        contribuinteDestinatario, camposExtras, numeroControle.
        """
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
                tipo=DOCUMENT_ORIGIN_NFE,
            )
        if obligation.period_ref:
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
        self._append_value(item, VALUE_TYPE_FCP, obligation.amount_fcp)
        if obligation.config_id.convenio:
            self._element(item, "convenio", obligation.config_id.convenio)
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
        self._append_emitter(guia, guide.company_id)
        itens = self._element(guia, "itensGNRE")
        for obligation in obligations:
            self._append_item(itens, obligation)
        total = sum(obligations.mapped("amount_total"))
        self._element(guia, "valorGNRE", f"{total:.2f}")
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
