# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

PROVEDOR_NFSE_NACIONAL = "nacional"

DANFSE_NACIONAL_TEMPLATE = "main_template_danfse_nacional"

ADN_BASE_URL = {
    "1": "https://sefin.nfse.gov.br/SefinNacional",
    "2": "https://sefin.producaorestrita.nfse.gov.br/SefinNacional",
}

PRESTADOR_SELF_EMITTED_EXCLUDED = (
    "nfse10_xNome",
    "nfse10_end",
    "nfse10_fone",
    "nfse10_email",
)

NFSE_NACIONAL_CANCEL_EVENT = "101101"
NFSE_NACIONAL_CANCEL_OFICIO_EVENT = "305101"
NFSE_NACIONAL_CANCEL_MOTIVES = [
    ("1", "Erro na emissão"),
    ("2", "Serviço não prestado"),
    ("9", "Outros"),
]

# cMotivo of the subst group of the DPS (TSCodJustSubst)
NFSE_NACIONAL_REPLACE_MOTIVES = [
    ("01", "Desenquadramento de NFS-e do Simples Nacional"),
    ("02", "Enquadramento de NFS-e no Simples Nacional"),
    ("03", "Inclusão retroativa de imunidade/isenção para NFS-e"),
    ("04", "Exclusão retroativa de imunidade/isenção para NFS-e"),
    (
        "05",
        "Rejeição de NFS-e pelo tomador ou pelo intermediário se responsável "
        "pelo recolhimento do tributo",
    ),
    ("99", "Outros"),
]
