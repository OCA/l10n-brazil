# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase

CPF_1 = "06310999729"
CPF_1_FORMATTED = "063.109.997-29"
CPF_2 = "13177890919"
CPF_3 = "52998224725"
CPF_4 = "11144477735"
CNPJ_1 = "14500536000180"
CNPJ_1_FORMATTED = "14.500.536/0001-80"
CNPJ_2 = "71222913000109"
IE_SP = "932.446.119.086"
IE_BA = "41902653"
FOREIGN_VAT = "12-3456789"


class L10nBrBaseCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.br = cls.env.ref("base.br")
        cls.us = cls.env.ref("base.us")
        cls.state_sp = cls.env.ref("base.state_br_sp")
        cls.state_rj = cls.env.ref("base.state_br_rj")
        cls.state_ba = cls.env.ref("base.state_br_ba")
        cls.city_sp = cls.env.ref("l10n_br_base.city_3550308")
        cls.env.company.country_id = cls.br
        cls.partner_model = cls.env["res.partner"]
        cls.config = cls.env["ir.config_parameter"].sudo()
        # "off" is represented by removing the parameter
        cls.config.set_param("l10n_br_base.allow_cnpj_multi_ie", False)

    def _person(self, **vals):
        return self.partner_model.create(
            dict({"name": "Person", "country_id": self.br.id}, **vals)
        )

    def _company(self, **vals):
        return self.partner_model.create(
            dict(
                {"name": "Company", "is_company": True, "country_id": self.br.id},
                **vals,
            )
        )
