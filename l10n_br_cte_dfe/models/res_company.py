# Copyright 2026 Engenere.
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import base64
from datetime import datetime, timezone

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal_dfe.tools import utils

from ..constants.cte_dfe import CTE_EVENT_CANCELAMENTO, CTE_PROC_SCHEMAS

try:
    from nfelib.cte.client.v4_0.dfe import DfeClient
except ImportError:
    DfeClient = None


class ResCompany(models.Model):
    """CT-e implementation of the generic DF-e distribution engine.

    The CTeDistribuicaoDFe service (NT 2015.002) differs from the NF-e
    one in three ways that shape this module:

    - there is no summary payload nor recipient manifestation: the
      complete XML is distributed right away;
    - there is no query by access key, only by NSU;
    - besides the CT-e (procCTe) it distributes the CT-e OS, the GTV-e
      and the CT-e Simplificado, which share the ``infCte`` layout.
    """

    _inherit = "res.company"

    # ── CT-e DF-e configuration (typed fields convention) ──────────────

    cte_last_nsu = fields.Char(string="CT-e Last NSU", size=25, default="0")

    cte_max_nsu = fields.Char(string="CT-e Max NSU", readonly=True)

    cte_dfe_last_query = fields.Datetime(string="CT-e DF-e Last Query")

    cte_dfe_last_status = fields.Char(string="CT-e DF-e Last Status", readonly=True)

    cte_dfe_last_status_code = fields.Char(
        string="CT-e DF-e Last Status Code", readonly=True
    )

    cte_dfe_next_query = fields.Datetime(
        string="CT-e Next Scheduled Query",
        help="CT-e DF-e distribution will not be queried before this time.",
    )

    cte_auto_fetch = fields.Boolean(
        default=False,
        string="Auto-fetch CT-e DF-e",
        help="Periodically queries DF-e distribution for new CT-e documents",
    )

    # ── Generic engine hooks ────────────────────────────────────────────

    def _dfe_get_processor(self, fiscal_type):
        if fiscal_type != "cte":
            return super()._dfe_get_processor(fiscal_type)
        self.ensure_one()
        cert = base64.b64decode(self.certificate.file)
        return DfeClient(
            ambiente=self.cte_environment,
            uf=self.state_id.ibge_code,
            pkcs12_data=cert,
            pkcs12_password=self.certificate.password,
            wrap_response=True,
        )

    def _dfe_consultar_distribuicao(self, fiscal_type, **kwargs):
        if fiscal_type == "cte":
            # CTeDistribuicaoDFe has no consChCTe: the client does not even
            # accept the ``chave`` argument the generic engine passes.
            if kwargs.pop("chave", None):
                raise UserError(
                    _("The CT-e distribution service has no query by access key.")
                )
        return super()._dfe_consultar_distribuicao(fiscal_type, **kwargs)

    def _dfe_extract_access_key(self, root, schema_type):
        if schema_type in CTE_PROC_SCHEMAS:
            return str(root.protCTe.infProt.chCTe)
        if schema_type == "procEventoCTe":
            return str(root.eventoCTe.infEvento.chCTe)
        return super()._dfe_extract_access_key(root, schema_type)

    def _dfe_cron_xmlid(self, fiscal_type):
        if fiscal_type == "cte":
            return "l10n_br_cte_dfe.ir_cron_search_cte_dfe_documents"
        return super()._dfe_cron_xmlid(fiscal_type)

    def _dfe_document_action_xmlid(self, fiscal_type):
        if fiscal_type == "cte":
            return "l10n_br_cte_dfe.action_cte_dfe_document"
        return super()._dfe_document_action_xmlid(fiscal_type)

    # ── CT-e specific actions ───────────────────────────────────────────

    def cte_dfe_search_documents(self):
        for record in self:
            record._dfe_document_distribution("cte")

    @api.model
    def _cron_cte_dfe_search_documents(self):
        return self._cron_dfe_search_documents("cte")

    @api.model
    def action_banner_search_all_cte(self):
        """Called from the CT-e banner button — delegates to current company."""
        company = self.env.company
        result = company.action_document_distribution("cte")
        return result or {"type": "ir.actions.client", "tag": "reload"}

    @api.model
    def action_banner_specific_search_cte(self):
        """Called from the CT-e banner button — delegates to current company."""
        return self.env.company.action_search_specific("cte")

    # ── Schema processors (NT 2015.002) ─────────────────────────────────

    @staticmethod
    def _cte_dfe_text(node, name, default=""):
        """Raw text of a child element, or ``default`` when absent.

        objectify coerces numeric text (CNPJ, nCT...) into numbers; the
        raw text keeps leading zeros.
        """
        child = getattr(node, name, None)
        if child is None:
            return default
        return (child.text or "").strip() or default

    def _cte_dfe_proc_vals(self, infcte):
        """Document metadata shared by CT-e, CT-e OS, GTV-e and CT-e Simp."""
        ide = infcte.ide
        emit = infcte.emit
        cnpj = self._cte_dfe_text(emit, "CNPJ")
        if cnpj:
            vat = utils.mask_cnpj(cnpj.zfill(14))
        else:
            vat = self._cte_dfe_text(emit, "CPF").zfill(11)
        # CT-e and CT-e OS carry the amount in vPrest; CT-e Simp in total;
        # the GTV-e has no service amount.
        amount = 0.0
        for group in ("vPrest", "total"):
            node = getattr(infcte, group, None)
            if node is not None and getattr(node, "vTPrest", None) is not None:
                amount = float(node.vTPrest)
                break
        return {
            "emitter": self._cte_dfe_text(emit, "xNome"),
            "vat": vat,
            "serie": self._cte_dfe_text(ide, "serie"),
            "document_number": str(int(ide.nCT)),
            "document_amount": amount,
            "document_emission_date": datetime.fromisoformat(
                self._cte_dfe_text(ide, "dhEmi")
            )
            .astimezone(timezone.utc)
            .replace(tzinfo=None),
            "document_state": "1",
        }

    def _cte_dfe_create_from_proc(self, root, nsu, schema_type):
        access_key = str(root.protCTe.infProt.chCTe)
        dfe_document = self._dfe_get_or_create_document(access_key, "cte")
        infcte = getattr(root, CTE_PROC_SCHEMAS[schema_type]).infCte

        dfe_record = (
            self.env["l10n_br_fiscal_dfe.dfe"]
            .sudo()
            .create(
                {
                    "access_key": access_key,
                    "nsu": nsu,
                    "company_id": self.id,
                    "fiscal_type": "cte",
                    "document_type_dfe": "complete",
                }
            )
        )
        dfe_document.sudo().dfe_ids = [(4, dfe_record.id)]
        dfe_document._update_metadata(self._cte_dfe_proc_vals(infcte), is_complete=True)
        return dfe_record

    def _dfe_create_from_procCTe(self, root, nsu, fiscal_type="cte"):
        return self._cte_dfe_create_from_proc(root, nsu, "procCTe")

    def _dfe_create_from_procCTeOS(self, root, nsu, fiscal_type="cte"):
        return self._cte_dfe_create_from_proc(root, nsu, "procCTeOS")

    def _dfe_create_from_procGTVe(self, root, nsu, fiscal_type="cte"):
        return self._cte_dfe_create_from_proc(root, nsu, "procGTVe")

    def _dfe_create_from_procCTeSimp(self, root, nsu, fiscal_type="cte"):
        return self._cte_dfe_create_from_proc(root, nsu, "procCTeSimp")

    def _dfe_create_from_procEventoCTe(self, root, nsu, fiscal_type="cte"):
        inf_evento = root.eventoCTe.infEvento
        access_key = str(inf_evento.chCTe)
        event_type = self._cte_dfe_text(inf_evento, "tpEvento")
        dfe_document = self._dfe_get_or_create_document(access_key, "cte")

        dfe_record = (
            self.env["l10n_br_fiscal_dfe.dfe"]
            .sudo()
            .create(
                {
                    "access_key": access_key,
                    "nsu": nsu,
                    "company_id": self.id,
                    "fiscal_type": "cte",
                    "document_type_dfe": "event",
                    "event_type_dfe": event_type,
                }
            )
        )
        dfe_document.sudo().dfe_ids = [(4, dfe_record.id)]
        if event_type == CTE_EVENT_CANCELAMENTO:
            # No summary payload tells the situation: the cancellation
            # event is the only way to learn the CT-e was cancelled.
            dfe_document._update_metadata({"document_state": "3"}, is_complete=True)
        return dfe_record
