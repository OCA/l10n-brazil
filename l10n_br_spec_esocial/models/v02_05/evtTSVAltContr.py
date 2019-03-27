# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:55 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models

# Sigla da UF
uf_instEnsino = [
    ("AC", "AC"),
    ("AL", "AL"),
    ("AP", "AP"),
    ("AM", "AM"),
    ("BA", "BA"),
    ("CE", "CE"),
    ("DF", "DF"),
    ("ES", "ES"),
    ("GO", "GO"),
    ("MA", "MA"),
    ("MT", "MT"),
    ("MS", "MS"),
    ("MG", "MG"),
    ("PA", "PA"),
    ("PB", "PB"),
    ("PR", "PR"),
    ("PE", "PE"),
    ("PI", "PI"),
    ("RJ", "RJ"),
    ("RN", "RN"),
    ("RS", "RS"),
    ("RO", "RO"),
    ("RR", "RR"),
    ("SC", "SC"),
    ("SP", "SP"),
    ("SE", "SE"),
    ("TO", "TO"),
]

# Sigla da UF
uf_ageIntegracao = [
    ("AC", "AC"),
    ("AL", "AL"),
    ("AP", "AP"),
    ("AM", "AM"),
    ("BA", "BA"),
    ("CE", "CE"),
    ("DF", "DF"),
    ("ES", "ES"),
    ("GO", "GO"),
    ("MA", "MA"),
    ("MT", "MT"),
    ("MS", "MS"),
    ("MG", "MG"),
    ("PA", "PA"),
    ("PB", "PB"),
    ("PR", "PR"),
    ("PE", "PE"),
    ("PI", "PI"),
    ("RJ", "RJ"),
    ("RN", "RN"),
    ("RS", "RS"),
    ("RO", "RO"),
    ("RR", "RR"),
    ("SC", "SC"),
    ("SP", "SP"),
    ("SE", "SE"),
    ("TO", "TO"),
]


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evttsvaltco.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeEveTrab(spec_models.AbstractSpecMixin):
    "Identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvaltco.tideevetrab'
    _generateds_type = 'TIdeEveTrab'
    _concrete_rec_name = 'esoc_indRetif'

    esoc02_indRetif = fields.Boolean(
        string="indRetif", xsd_required=True)
    esoc02_nrRecibo = fields.Char(
        string="nrRecibo")
    esoc02_tpAmb = fields.Boolean(
        string="tpAmb", xsd_required=True)
    esoc02_procEmi = fields.Boolean(
        string="procEmi", xsd_required=True)
    esoc02_verProc = fields.Char(
        string="verProc", xsd_required=True)


class TRemun(spec_models.AbstractSpecMixin):
    "Remuneração e periodicidade de pagamento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvaltco.tremun'
    _generateds_type = 'TRemun'
    _concrete_rec_name = 'esoc_vrSalFx'

    esoc02_vrSalFx = fields.Monetary(
        string="vrSalFx", xsd_required=True)
    esoc02_undSalFixo = fields.Boolean(
        string="undSalFixo", xsd_required=True)
    esoc02_dscSalVar = fields.Char(
        string="dscSalVar")


class AgeIntegracao(spec_models.AbstractSpecMixin):
    "Agente de Integração"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvaltco.ageintegracao'
    _generateds_type = 'ageIntegracaoType'
    _concrete_rec_name = 'esoc_cnpjAgntInteg'

    esoc02_cnpjAgntInteg = fields.Char(
        string="cnpjAgntInteg",
        xsd_required=True)
    esoc02_nmRazao = fields.Char(
        string="nmRazao", xsd_required=True)
    esoc02_dscLograd = fields.Char(
        string="dscLograd", xsd_required=True)
    esoc02_nrLograd = fields.Char(
        string="nrLograd", xsd_required=True)
    esoc02_bairro = fields.Char(
        string="bairro")
    esoc02_cep = fields.Char(
        string="cep", xsd_required=True)
    esoc02_codMunic = fields.Integer(
        string="codMunic")
    esoc02_uf = fields.Selection(
        uf_ageIntegracao,
        string="uf", xsd_required=True)


class CargoFuncao(spec_models.AbstractSpecMixin):
    "Cargo/Função ocupado pelo Trabalhador Sem Vínculo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvaltco.cargofuncao'
    _generateds_type = 'cargoFuncaoType'
    _concrete_rec_name = 'esoc_codCargo'

    esoc02_codCargo = fields.Char(
        string="codCargo", xsd_required=True)
    esoc02_codFuncao = fields.Char(
        string="codFuncao")


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evttsvaltco.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtTSVAltContr'

    esoc02_evtTSVAltContr = fields.Many2one(
        "esoc.02.evttsvaltco.evttsvaltcontr",
        string="evtTSVAltContr",
        xsd_required=True)


class EvtTSVAltContr(spec_models.AbstractSpecMixin):
    "TSVE - Alteração Contratual"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvaltco.evttsvaltcontr'
    _generateds_type = 'evtTSVAltContrType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evttsvaltco.tideevetrab",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evttsvaltco.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideTrabSemVinculo = fields.Many2one(
        "esoc.02.evttsvaltco.idetrabsemvinculo",
        string="Identificação do Trabalhador Sem Vínculo de Emprego",
        xsd_required=True)
    esoc02_infoTSVAlteracao = fields.Many2one(
        "esoc.02.evttsvaltco.infotsvalteracao",
        string="Trabalhador Sem Vínculo de Emprego",
        xsd_required=True,
        help="Trabalhador Sem Vínculo de Emprego - Alteração Contratual")


class IdeTrabSemVinculo(spec_models.AbstractSpecMixin):
    "Identificação do Trabalhador Sem Vínculo de Emprego"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvaltco.idetrabsemvinculo'
    _generateds_type = 'ideTrabSemVinculoType'
    _concrete_rec_name = 'esoc_cpfTrab'

    esoc02_cpfTrab = fields.Char(
        string="cpfTrab", xsd_required=True)
    esoc02_nisTrab = fields.Char(
        string="nisTrab")
    esoc02_codCateg = fields.Integer(
        string="codCateg", xsd_required=True)


class InfoComplementares(spec_models.AbstractSpecMixin):
    _description = 'infocomplementares'
    _name = 'esoc.02.evttsvaltco.infocomplementares'
    _generateds_type = 'infoComplementaresType'
    _concrete_rec_name = 'esoc_cargoFuncao'

    esoc02_cargoFuncao = fields.Many2one(
        "esoc.02.evttsvaltco.cargofuncao",
        string="Cargo/Função ocupado pelo Trabalhador Sem Vínculo")
    esoc02_remuneracao = fields.Many2one(
        "esoc.02.evttsvaltco.tremun",
        string="Informações da remuneração e periodicidade de pagamento")
    esoc02_infoEstagiario = fields.Many2one(
        "esoc.02.evttsvaltco.infoestagiario",
        string="informações do estagiário")


class InfoEstagiario(spec_models.AbstractSpecMixin):
    "informações do estagiário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvaltco.infoestagiario'
    _generateds_type = 'infoEstagiarioType'
    _concrete_rec_name = 'esoc_natEstagio'

    esoc02_natEstagio = fields.Char(
        string="natEstagio", xsd_required=True)
    esoc02_nivEstagio = fields.Boolean(
        string="nivEstagio", xsd_required=True)
    esoc02_areaAtuacao = fields.Char(
        string="areaAtuacao")
    esoc02_nrApol = fields.Char(
        string="nrApol")
    esoc02_vlrBolsa = fields.Monetary(
        string="vlrBolsa")
    esoc02_dtPrevTerm = fields.Date(
        string="dtPrevTerm", xsd_required=True)
    esoc02_instEnsino = fields.Many2one(
        "esoc.02.evttsvaltco.instensino",
        string="Instituição de Ensino",
        xsd_required=True)
    esoc02_ageIntegracao = fields.Many2one(
        "esoc.02.evttsvaltco.ageintegracao",
        string="Agente de Integração")
    esoc02_supervisorEstagio = fields.Many2one(
        "esoc.02.evttsvaltco.supervisorestagio",
        string="Supervisor do Estágio")


class InfoTSVAlteracao(spec_models.AbstractSpecMixin):
    "Trabalhador Sem Vínculo de Emprego - Alteração Contratual"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvaltco.infotsvalteracao'
    _generateds_type = 'infoTSVAlteracaoType'
    _concrete_rec_name = 'esoc_dtAlteracao'

    esoc02_dtAlteracao = fields.Date(
        string="dtAlteracao", xsd_required=True)
    esoc02_natAtividade = fields.Boolean(
        string="natAtividade")
    esoc02_infoComplementares = fields.Many2one(
        "esoc.02.evttsvaltco.infocomplementares",
        string="infoComplementares")


class InstEnsino(spec_models.AbstractSpecMixin):
    "Instituição de Ensino"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvaltco.instensino'
    _generateds_type = 'instEnsinoType'
    _concrete_rec_name = 'esoc_cnpjInstEnsino'

    esoc02_cnpjInstEnsino = fields.Char(
        string="cnpjInstEnsino")
    esoc02_nmRazao = fields.Char(
        string="nmRazao", xsd_required=True)
    esoc02_dscLograd = fields.Char(
        string="dscLograd")
    esoc02_nrLograd = fields.Char(
        string="nrLograd")
    esoc02_bairro = fields.Char(
        string="bairro")
    esoc02_cep = fields.Char(
        string="cep")
    esoc02_codMunic = fields.Integer(
        string="codMunic")
    esoc02_uf = fields.Selection(
        uf_instEnsino,
        string="uf")


class SupervisorEstagio(spec_models.AbstractSpecMixin):
    "Supervisor do Estágio"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvaltco.supervisorestagio'
    _generateds_type = 'supervisorEstagioType'
    _concrete_rec_name = 'esoc_cpfSupervisor'

    esoc02_cpfSupervisor = fields.Char(
        string="cpfSupervisor",
        xsd_required=True)
    esoc02_nmSuperv = fields.Char(
        string="nmSuperv", xsd_required=True)
