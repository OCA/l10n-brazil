# Copyright (C) 2026 Luis Felipe Mileo - KMEE <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from erpbrasil.base import misc

from odoo import api, fields, models

# Qualificacao do socio ou titular no registro Y600. Sao os codigos de uso
# corrente; a tabela completa esta no Guia Pratico da ECF.
QUALIFICACAO_SOCIO = [
    ("01", "01 - Socio ou acionista pessoa fisica residente no Brasil"),
    ("02", "02 - Socio ou acionista pessoa fisica residente no exterior"),
    ("03", "03 - Socio ou acionista pessoa juridica domiciliada no Brasil"),
    ("04", "04 - Socio ou acionista pessoa juridica domiciliada no exterior"),
    ("05", "05 - Titular de empresa individual"),
    ("06", "06 - Socio ostensivo de SCP"),
    ("07", "07 - Socio participante de SCP"),
]

# Codigo do Brasil na tabela de paises do Sped (registro Y600).
PAIS_BRASIL = "105"


class EcfShareholder(models.Model):
    """Socio ou titular da pessoa juridica, escriturado no registro Y600.

    O registro identifica quem participa do capital e o que recebeu no
    ano-calendario, informacao que o Odoo nao guarda em lugar nenhum: por isso
    e cadastro proprio.
    """

    _name = "l10n_br_ecf.shareholder"
    _description = "Socio ou Titular na ECF"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        ondelete="cascade",
        index=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Contato",
        help="Preenche nome e CPF/CNPJ a partir do contato.",
    )
    name = fields.Char(string="Nome", required=True)
    cpf_cnpj = fields.Char(string="CPF/CNPJ", required=True)
    country_id = fields.Many2one(comodel_name="res.country", string="Pais")
    qualification = fields.Selection(
        selection=QUALIFICACAO_SOCIO,
        string="Qualificacao",
        required=True,
        default="01",
    )
    date_start = fields.Date(string="Data de entrada")
    date_end = fields.Date(string="Data de saida")
    capital_share = fields.Float(
        string="% do capital total",
        digits=(5, 2),
    )
    voting_share = fields.Float(
        string="% do capital votante",
        digits=(5, 2),
    )
    work_income = fields.Monetary(string="Remuneracao do trabalho")
    dividend_income = fields.Monetary(string="Lucros e dividendos")
    interest_income = fields.Monetary(string="Juros sobre o capital proprio")
    other_income = fields.Monetary(string="Demais rendimentos")
    withheld_tax = fields.Monetary(string="Imposto de renda retido")
    currency_id = fields.Many2one(
        related="company_id.currency_id",
        string="Currency",
    )

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        for shareholder in self.filtered("partner_id"):
            partner = shareholder.partner_id
            shareholder.name = partner.name
            shareholder.cpf_cnpj = partner.vat or partner.cnpj_cpf
            shareholder.country_id = partner.country_id

    def _sped_values(self, declaration):
        """Valores do registro Y600 deste socio."""
        self.ensure_one()
        return {
            "DT_ALT_SOC": self.date_start or declaration.DT_INI,
            "DT_FIM_SOC": self.date_end or False,
            "PAIS": self.country_id.l10n_br_ibge_code or PAIS_BRASIL
            if hasattr(self.country_id, "l10n_br_ibge_code")
            else PAIS_BRASIL,
            "IND_QUALIF": self.qualification,
            "CPF_CNPJ": misc.punctuation_rm(self.cpf_cnpj or ""),
            "NOM_EMP": self.name,
            "QUALIF": self.qualification,
            "PERC_CAP_TOT": self.capital_share,
            "PERC_CAP_VOT": self.voting_share,
            "VL_REM_TRAB": self.work_income,
            "VL_LUC_DIV": self.dividend_income,
            "VL_JUR_CAP": self.interest_income,
            "VL_DEM_REND": self.other_income,
            "VL_IR_RET": self.withheld_tax,
        }
