# Copyright (C) 2023 KMEE Informatica LTDA
# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _dfe_log(self, message, log_type="info", result=None):
        """Generic SOAP Log"""
        vals = {"company_id": self.id, "log_type": log_type, "message": message}
        if result is not None:
            if getattr(result, "envio_xml", False):
                vals["request_xml"] = (
                    result.envio_xml.decode("utf-8", errors="replace")
                    if isinstance(result.envio_xml, bytes)
                    else str(result.envio_xml)
                )
            retorno = getattr(result, "retorno", None)
            content = getattr(retorno, "content", None) or getattr(
                retorno, "_content", None
            )
            if content:
                vals["response_xml"] = (
                    content.decode("utf-8", errors="replace")
                    if isinstance(content, bytes)
                    else str(content)
                )
        self.env["l10n_br_fiscal_dfe.distribution_log"].sudo().create(vals)

    def _dfe_validate_distribution_response(self, result, raise_message=False):
        """Validates Sefaz Response generically"""
        resp = result.resposta
        if resp.cStat == "138":
            return True

        if resp.cStat == "137":
            self._dfe_log(
                f"No documents found: {resp.cStat} - {resp.xMotivo}",
                log_type="info",
                result=result,
            )
        else:
            msg = f"Error validating distribution: {resp.cStat} - {resp.xMotivo}"
            self._dfe_log(msg, log_type="warning", result=result)
            if raise_message:
                from odoo.exceptions import ValidationError

                raise ValidationError(msg)
        return False
