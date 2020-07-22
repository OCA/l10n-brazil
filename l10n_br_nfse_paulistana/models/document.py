# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from nfselib.paulistana.v02.TiposNFe_v01 import (
    tpEndereco,
    tpCPFCNPJ,
    tpRPS,
)


from odoo import models
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_NFSE,
)

from odoo.addons.l10n_br_nfse.models.res_company import PROCESSADOR


def fiter_processador_edoc_nfse_paulistana(record):
    if (record.processador_edoc == PROCESSADOR and
            record.document_type_id.code in [
                MODELO_FISCAL_NFSE,
            ]):
        return True
    return False


def fiter_provedor_paulistana(record):
    if record.company_id.provedor_nfse == 'paulistana':
        return True
    return False


class Document(models.Model):

    _inherit = 'l10n_br_fiscal.document'

    def _serialize(self, edocs):
        edocs = super(Document, self)._serialize(edocs)
        for record in self.filtered(
                fiter_processador_edoc_nfse_paulistana).filtered(
                    fiter_provedor_paulistana):
            edocs.append(record.serialize_nfse_paulistana())
        return edocs

    def _serialize_rps(self, dados):
        return tpRPS(
            InscricaoMunicipalTomador=dados['inscricao_municipal'],
            CPFCNPJTomador=tpCPFCNPJ(
                Cnpj=dados['cnpj'],
                Cpf=dados['cpf'],
            ),
            RazaoSocialTomador=dados['razao_social'],
            EnderecoTomador=tpEndereco(
                # TipoLogradouro='Rua', # TODO: Verificar se este campo é necessario
                Logradouro=dados['endereco'],
                NumeroEndereco=dados['numero'],
                ComplementoEndereco=dados['complemento'],
                Bairro=dados['bairro'],
                Cidade=dados['codigo_municipio'],
                UF=dados['uf'],
                CEP=dados['cep'],
            ) or None,
        )
