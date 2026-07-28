# Copyright (C) 2022-Today - Engenere (<https://engenere.one>)
# @author Antônio S. Pereira Neto <neto@engenere.one>
# Copyright (C) 2024-Today - KMEE (<https://kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    ##########################
    # NF-e tag: DI (used for DUIMP too - see NT: the <DI> group covers
    # "DI, DSI, DIRE, DUImp", nfe40_nDI carries the DUIMP number)
    ##########################

    nfe40_DI = fields.One2many(
        comodel_name="nfe.40.di",
        inverse_name="nfe40_DI_prod_id",
        compute="_compute_nfe40_DI_duimp",
        store=True,
    )

    @api.model
    def _duimp_clearance_state(self, uf_code):
        """The Brazilian state whose code matches the DUIMP clearance state."""
        if not uf_code:
            return self.env["res.country.state"]
        return self.env["res.country.state"].search(
            [("code", "=", uf_code), ("country_id.code", "=", "BR")], limit=1
        )

    @api.depends("duimp_item_id", "document_id.state_edoc")
    def _compute_nfe40_DI_duimp(self):
        """Build the NF-e import-declaration group (``DI``/``adi``) from
        the linked DUIMP item. Ported from
        ``l10n_br_di.fiscal_document_line`` (KMEE 14.0), reading the
        persistent DUIMP item directly instead of going through
        ``account.move.line``.

        For a DUIMP the convention is ``nAdicao=1`` and
        ``nSeqAdic=numeroItem`` (the DUIMP has no "adição"). Confirm
        against the NT 2020.006 / current validation rules before
        production emission.
        """
        for line in self:
            if not line.document_id._need_compute_nfe_tags:
                continue

            item = line.duimp_item_id
            if not item:
                if line.nfe40_DI:
                    line.nfe40_DI = [(5, 0, 0)]
                continue

            declaracao = item.declaracao_id
            nfe40_adi_dict = {
                "nfe40_nAdicao": "1",
                # nfe40_nSeqAdic is Char in the layout; int() only drops
                # leading zeros ("01" -> "1")
                "nfe40_nSeqAdic": str(int(item.numero_item or 1)),
                "nfe40_cFabricante": item.codigo_produto,
            }
            nfe40_DI_dict = {
                "nfe40_DI_prod_id": line.id,
                "nfe40_nDI": declaracao.numero,
                "nfe40_dDI": declaracao.data_registro,
                "nfe40_xLocDesemb": declaracao.urf_despacho_nome,
                # nfe40_UFDesemb is related to state_clearance_id.code, so it
                # has to be set through the state, not written directly
                "state_clearance_id": self._duimp_clearance_state(
                    declaracao.uf_desembaraco
                ).id,
                "nfe40_dDesemb": declaracao.data_desembaraco,
                "nfe40_vAFRMM": item.amount_afrmm,
                "nfe40_tpViaTransp": (declaracao.via_transporte_codigo or "").lstrip(
                    "0"
                )
                or False,
                "nfe40_tpIntermedio": declaracao.caracterizacao_operacao_codigo,
                "nfe40_cExportador": item.codigo_produto,
                "nfe40_adi": [(0, 0, nfe40_adi_dict)],
            }
            line.nfe40_DI = [(5, 0, 0), (0, 0, nfe40_DI_dict)]
