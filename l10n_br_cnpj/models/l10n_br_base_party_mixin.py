# Copyright 2022 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from erpbrasil.base.misc import punctuation_rm
from requests import get

from odoo import _, models
from odoo.exceptions import UserError, ValidationError


class PartyMixin(models.AbstractModel):
    _inherit = "l10n_br_base.party.mixin"

    def search_cnpj(self):
        """Search CNPJ by the chosen API """
        if not self.cnpj_cpf:
            raise UserError(_("Por favor insira o CNPJ"))

        if not self.cnpj_validation_activated():
            raise UserError(
                _(
                    "É necessário ativar a opção de validação de CNPJ para usar essa"
                    " funcionalidade."
                )
            )

        cnpj_cpf = punctuation_rm(self.cnpj_cpf)
        webservice = self.env["l10n_br_cnpj.webservice"]
        response = get(webservice.get_api_url() + cnpj_cpf)
        try:
            data = response.json()
        except ValueError:
            raise ValidationError(
                _("Não foi possível conectar ao %s." % webservice.get_provider())
            )

        if data.get("status") == "ERROR":
            raise ValidationError(_(data.get("message")))

        self.company_type = "company"
        values = webservice.import_data(data)
        self.write(values)

    def cnpj_validation_activated(self):
        cnpj_validation_disabled = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_br_base.disable_cpf_cnpj_validation")
        )
        return not cnpj_validation_disabled
