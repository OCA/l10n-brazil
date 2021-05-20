# Copyright 2021 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from requests import get

from odoo import api, models
from erpbrasil.edoc.nfe import NFe as edoc_nfe
from erpbrasil.assinatura import certificado as cert
from requests import Session
from erpbrasil.transmissao import TransmissaoSOAP


from erpbrasil.base.misc import punctuation_rm
from erpbrasil.base.fiscal.cnpj_cpf import validar_cnpj


class PartyMixin(models.AbstractModel):

    _inherit = 'l10n_br_base.party.mixin'

    def _processador(self):
        if not self.env.user.company_id:
            return

        certificado = cert.Certificado(
            arquivo=self.env.user.company_id.certificate_nfe_id.file,
            senha=self.env.user.company_id.certificate_nfe_id.password,
        )
        session = Session()
        session.verify = False
        transmissao = TransmissaoSOAP(certificado, session)
        return edoc_nfe(
            transmissao, self.env.user.company_id.state_id.ibge_code,
            versao=self.env.user.company_id.nfe_version,
            ambiente=self.env.user.company_id.nfe_environment
        )

    @api.onchange('state_id', 'cnpj_cpf')
    def _onchange_sintegra(self):
        if self.state_id and self.cnpj_cpf:
            cnpj_cpf = punctuation_rm(self.cnpj_cpf)

            processador = self._processador()

            if not processador:
                return

            result = processador.consultar_cadastro(
                self.state_id.code, cnpj=cnpj_cpf
            )
            if (result.resposta and result.resposta.infCons and
                    result.resposta.infCons.cStat == '111'):

                cad = result.resposta.infCons.infCad[0]
                self.inscr_est = cad.IE

"""
<nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/CadConsultaCadastro4">
  <retConsCad versao="2.00" xmlns="http://www.portalfiscal.inf.br/nfe">
    <infCons>
      <verAplic>SP_NFE_PL009_V4</verAplic>
      <cStat>111</cStat>
      <xMotivo>Consulta cadastro com uma ocorrência</xMotivo>
      <UF>SP</UF>
      <CNPJ>123213</CNPJ>
      <dhCons>2021-05-19T20:55:34-03:00</dhCons>
      <cUF>35</cUF>
      <infCad>
        <IE>123213</IE>
        <CNPJ>123123</CNPJ>
        <UF>SP</UF>
        <cSit>1</cSit>
        <indCredNFe>1</indCredNFe>
        <indCredCTe>4</indCredCTe>
        <xNome>asdasdad</xNome>
        <xRegApur>NORMAL - REGIME PERIÓDICO DE APURAÇÃO</xRegApur>
        <CNAE>1091101</CNAE>
        <dIniAtiv>2003-11-07</dIniAtiv>
        <dUltSit>2003-11-07</dUltSit>
        <ender>
          <xLgr>ESTRADA</xLgr>
          <nro>1600</nro>
          <xBairro>asdasdsad</xBairro>
          <cMun>3524402</cMun>
          <xMun>JACAREI</xMun>
          <CEP>1200000</CEP>
        </ender>
      </infCad>
    </infCons>
  </retConsCad>
</nfeResultMsg>
"""
