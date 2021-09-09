# Copyright (C) 2019  KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models


class NFeWorkflow(models.AbstractModel):
    _name = "l10n_br_nfe.document.workflow"
    _description = "NFe Document Workflow"
    _inherit = "l10n_br_fiscal.document.workflow"

    @api.multi
    def _document_number(self):
        # TODO: Criar campos no fiscal para codigo aleatorio e digito verificador,
        # pois outros modelos também precisam dessescampos: CT-e, MDF-e etc
        super()._document_number()
        for record in self.filtered(filter_processador_edoc_nfe):
            if record.document_key:
                chave = ChaveEdoc(record.document_key)
                record.nfe40_cNF = chave.codigo_aleatorio
                record.nfe40_cDV = chave.digito_verificador

    @api.multi
    def _document_date(self):
        super()._document_date()
        for record in self.filtered(filter_processador_edoc_nfe):
            if not record.date_in_out:
                record.date_in_out = fields.Datetime.now()