# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from erpbrasil.base.fiscal.edoc import ChaveEdoc

from odoo import api, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_CTE,
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_NFSE,
)


class DocumentRelated(models.Model):
    """Access key validation of the documents referenced by a fiscal document.

    Only the referenced electronic models carry a real SEFAZ access key, so
    the check belongs to the EDI module.
    """

    _inherit = "l10n_br_fiscal.document.related"

    @api.constrains("document_key")
    def _check_key(self):
        for record in self:
            if not record.document_key:
                return
            if record.document_type_id.code in (
                MODELO_FISCAL_CTE,
                MODELO_FISCAL_NFCE,
                MODELO_FISCAL_NFE,
                MODELO_FISCAL_NFSE,
            ):
                ChaveEdoc(chave=record.document_key, validar=True)
