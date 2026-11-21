# Copyright (C) 2026 Luis Felipe Mileo - KMEE <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).


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
    uma ocorrencia. O cadastro cobre o registro 0930 da ECF. O J930 da ECD
    pede campos alem destes (COD_ASSIN, UF_CRC, NUM_SEQ_CRC, DT_CRC e
    IND_RESP_LEGAL), com a mesma tabela de qualificacao mais o 001 (e-CNPJ) e
    o 940 (auditor): quando a geracao do J930 for implementada, esses campos
    entram aqui.
    """

    _name = "l10n_br_sped.signer"
    _description = "Signatario da Escrituracao do Sped"
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
