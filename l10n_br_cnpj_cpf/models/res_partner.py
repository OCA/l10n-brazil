# Copyright (C) 2020  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from datetime import datetime

from erpbrasil.assinatura import certificado as cert
from erpbrasil.edoc.nfe import NFe as edoc_nfe
from erpbrasil.transmissao import TransmissaoSOAP
from requests import Session

from odoo import _, fields, models
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base.misc import punctuation_rm
    from erpbrasil.base.fiscal import cnpj_cpf
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _processador(self, uf):
        if not self.env.user.company_id.certificate_nfe_id:
            raise UserError(_("Certificado não encontrado"))

        certificado = cert.Certificado(
            arquivo=self.env.user.company_id.certificate_nfe_id.file,
            senha=self.env.user.company_id.certificate_nfe_id.password,
        )
        session = Session()
        session.verify = False
        transmissao = TransmissaoSOAP(certificado, session)
        return edoc_nfe(
            transmissao,
            uf.ibge_code,
            versao="4.00",
            ambiente=self.env.user.company_id.nfe_environment,
        )

    def action_consultar_cad(self):
        if self.state_id:
            uf = self.state_id
        else:
            uf = self.env.user.company_id.state_id
        processador = self._processador(uf)
        cpf = None
        cnpj = None
        ie = None
        if self.company_type == 'person':
            if self.cnpj_cpf:
                cpf = punctuation_rm(self.cnpj_cpf)
            else:
                return
        else:
            if self.inscr_est:
                ie = punctuation_rm(self.inscr_est)
            elif self.cnpj_cpf:
                cnpj = punctuation_rm(self.cnpj_cpf)
            else:
                return
        evento = processador.consultar_cadastro(
            uf.code,
            cnpj,
            cpf,
            ie,
        )

        response_xml = evento.retorno.content.decode("utf-8")
        response = evento.resposta.infCons
        if response.cStat == "111":
            # encontrou um cadastro
            for info in response.infCad:
                cep = info.ender.CEP
                cep = f"{cep[:5]}-{cep[5:8]}"
                ibge = info.ender.cMun
                city = self.env['res.city'].search([
                    ('ibge_code', '=', ibge)])
                vals = {
                    "name": info.xNome,
                    "legal_name": info.xNome,
                    "inscr_est": info.IE,
                    "city_id": city.id,
                    "state_id": city.state_id.id,
                    "country_id": city.country_id.id,
                    "street_name": info.ender.xLgr,
                    "street_number": info.ender.nro,
                    "district": info.ender.xBairro,
                    "street2": info.ender.xCpl,
                    "zip": cep,
                }
                if not self.cnpj_cpf:
                    vals["cnpj_cpf"] = cnpj_cpf.formata(str(info.CNPJ))
                if not self.inscr_est:
                    vals["inscr_est"] = info.IE
                if info.xRegApur == "SIMPLES NACIONAL":
                    vals["ind_ie_dest"] = "1"
                    vals["tax_framework"] = "1"
                elif info.xRegApur == "NORMAL - REGIME PERIÓDICO DE APURAÇÃO":
                    vals["ind_ie_dest"] = "1"
                    vals["tax_framework"] = "3"
                self.update(vals)
        elif response.cStat != "100":
            raise UserError(_(f"Erro na busca : {response.cStat}-{response.xMotivo}/{uf.code}"))
