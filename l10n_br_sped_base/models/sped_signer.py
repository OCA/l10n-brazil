# Copyright (C) 2026 Luis Felipe Mileo - KMEE <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).


from erpbrasil.base import misc

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# Tabela de qualificacao do assinante do Sped, a mesma que os programas da ECD
# (SPEDCONTABIL_QUALIF_ASSINANTE) e da ECF (SPEDECF_QUALIF_ASSINANTE) conferem.
QUALIFICACAO_SIGNATARIO = [
    ("203", "203 - Diretor"),
    ("204", "204 - Conselheiro de Administracao"),
    ("205", "205 - Administrador"),
    ("206", "206 - Administrador do Grupo"),
    ("207", "207 - Administrador de Sociedade Filiada"),
    ("220", "220 - Administrador Judicial - Pessoa Fisica"),
    (
        "222",
        "222 - Administrador Judicial - Pessoa Juridica - Profissional Responsavel",
    ),
    ("223", "223 - Administrador Judicial/Gestor"),
    ("226", "226 - Gestor Judicial"),
    ("309", "309 - Procurador"),
    ("312", "312 - Inventariante"),
    ("313", "313 - Liquidante"),
    ("315", "315 - Interventor"),
    ("401", "401 - Titular Pessoa Fisica - EIRELI"),
    ("801", "801 - Empresario"),
    ("900", "900 - Contador/Contabilista"),
    ("999", "999 - Outros"),
]

# Qualificacoes que exigem o numero de inscricao no CRC.
QUALIFICACAO_COM_CRC = ("900",)


class SpedSigner(models.Model):
    """Signatario de uma escrituracao do Sped.

    A escrituracao e assinada por, no minimo, o responsavel legal da pessoa
    juridica e o contabilista; por isso o registro e obrigatorio e tem mais de
    uma ocorrencia. O cadastro cobre o registro 0930 da ECF e o J930 da ECD,
    que pede tambem a UF do CRC, a certidao de regularidade profissional do
    contador e qual signatario e o responsavel legal.
    """

    _name = "l10n_br_sped.signer"
    _description = "Signatario da Escrituracao do Sped"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        ondelete="cascade",
        index=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Contato",
        help="Preenche nome, CPF/CNPJ, e-mail e telefone a partir do contato.",
    )
    name = fields.Char(string="Nome", required=True)
    cpf_cnpj = fields.Char(string="CPF/CNPJ", required=True)
    qualification = fields.Selection(
        selection=QUALIFICACAO_SIGNATARIO,
        string="Qualificacao",
        required=True,
    )
    crc = fields.Char(
        string="CRC",
        help="Numero de inscricao no Conselho Regional de Contabilidade, "
        "obrigatorio para o contador.",
    )
    crc_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="UF do CRC",
    )
    crp_number = fields.Char(
        string="Numero da CRP",
        help="Numero da Certidao de Regularidade Profissional do contador "
        "(registro J930 da ECD).",
    )
    crp_validity = fields.Date(
        string="Validade da CRP",
    )
    legal_responsible = fields.Boolean(
        string="Responsavel legal",
        help="Signatario que responde legalmente pela escrituracao "
        "(IND_RESP_LEGAL do registro J930 da ECD).",
    )
    email = fields.Char()
    phone = fields.Char(string="Telefone")

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        for signer in self.filtered("partner_id"):
            partner = signer.partner_id
            signer.name = partner.name
            signer.cpf_cnpj = partner.vat or partner.cnpj_cpf
            signer.email = partner.email
            signer.phone = partner.phone or partner.mobile
            signer.crc = partner.crc_code or signer.crc
            signer.crc_state_id = partner.crc_state_id or signer.crc_state_id

    @api.constrains("qualification", "crc")
    def _check_crc(self):
        for signer in self:
            if signer.qualification in QUALIFICACAO_COM_CRC and not signer.crc:
                raise ValidationError(
                    _(
                        "O signatario %(nome)s e contabilista e precisa do "
                        "numero de inscricao no CRC para assinar a ECF."
                    )
                    % {"nome": signer.name}
                )

    @staticmethod
    def _so_digitos(valor):
        """So os digitos: o Sped nao aceita separador nem espaco.

        O ``punctuation_rm`` do erpbrasil tira a pontuacao mas preserva o
        espaco, e o telefone brasileiro costuma ter um depois do DDD.
        """
        return "".join(c for c in str(valor or "") if c.isdigit())

    def _sped_values(self):
        """Valores do registro 0930 deste signatario."""
        self.ensure_one()
        return {
            "IDENT_NOM": self.name,
            "IDENT_CPF_CNPJ": self._so_digitos(self.cpf_cnpj),
            "IDENT_QUALIF": self.qualification,
            "IND_CRC": self.crc or "",
            "EMAIL": self.email or "",
            "FONE": self._so_digitos(self.phone),
        }


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_br_sped_signer_ids = fields.One2many(
        comodel_name="l10n_br_sped.signer",
        inverse_name="company_id",
        string="Signatarios da escrituracao",
        help="A escrituracao e assinada, no minimo, pelo responsavel legal da "
        "pessoa juridica e pelo contabilista: registro 0930 da ECF e J930 da "
        "ECD.",
    )
    # registro na junta comercial, que o termo de abertura da ECD (I030) e o
    # indicador de NIRE do 0000 informam
    l10n_br_nire = fields.Char(
        string="NIRE",
        size=11,
        help="Numero de Identificacao do Registro de Empresas, dado pela junta "
        "comercial. Vazio para a sociedade registrada em cartorio.",
    )
    l10n_br_articles_filing_date = fields.Date(
        string="Data de arquivamento dos atos constitutivos",
    )
    l10n_br_conversion_filing_date = fields.Date(
        string="Data de arquivamento do ato de conversao",
        help="Data de arquivamento do ato de conversao de sociedade simples em "
        "sociedade empresaria, quando houve.",
    )

    @api.constrains("l10n_br_nire")
    def _check_l10n_br_nire(self):
        # regras REGRA_VALIDA_NIRE e REGRA_NIRE_UF do PVA da ECD
        for company in self.filtered("l10n_br_nire"):
            nire = misc.punctuation_rm(company.l10n_br_nire)
            if not _nire_check_digit_ok(nire):
                raise ValidationError(
                    _("Invalid NIRE %s: 11 digits with a valid check digit.") % nire
                )
            uf_code = company.state_id.ibge_code
            if uf_code == "50":
                uf_code = "54"
            if uf_code and not nire.startswith(uf_code):
                raise ValidationError(
                    _("The NIRE %(nire)s does not belong to the state %(state)s.")
                    % {"nire": nire, "state": company.state_id.code}
                )


def _nire_check_digit_ok(nire):
    if len(nire) != 11 or not nire.isdigit():
        return False
    weights = [2, 10, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(d) * w for d, w in zip(nire[:10], weights, strict=True))
    digit = 11 - total % 11
    digit = {10: 0, 11: 1}.get(digit, digit)
    return digit == int(nire[10])
