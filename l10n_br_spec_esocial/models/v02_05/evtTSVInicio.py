# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:56 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models

# Estado da Federação emissor da CNH
ufCnh_TCnh = [
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

# UF da expedição da CTPS
ufCtps_TCtps = [
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
uf_nascimento = [
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
uf_TEnderecoBrasil = [
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


class TCessaoTrab(spec_models.AbstractSpecMixin):
    "Informações de cessão de trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.tcessaotrab'
    _generateds_type = 'TCessaoTrab'
    _concrete_rec_name = 'esoc_categOrig'

    esoc02_categOrig = fields.Integer(
        string="categOrig", xsd_required=True)
    esoc02_cnpjCednt = fields.Char(
        string="cnpjCednt", xsd_required=True)
    esoc02_matricCed = fields.Char(
        string="matricCed", xsd_required=True)
    esoc02_dtAdmCed = fields.Date(
        string="dtAdmCed", xsd_required=True)
    esoc02_tpRegTrab = fields.Boolean(
        string="tpRegTrab", xsd_required=True)
    esoc02_tpRegPrev = fields.Boolean(
        string="tpRegPrev", xsd_required=True)
    esoc02_infOnus = fields.Boolean(
        string="infOnus", xsd_required=True)


class TCnh(spec_models.AbstractSpecMixin):
    "Cartera Nacional de Habilitação"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.tcnh'
    _generateds_type = 'TCnh'
    _concrete_rec_name = 'esoc_nrRegCnh'

    esoc02_nrRegCnh = fields.Char(
        string="nrRegCnh", xsd_required=True)
    esoc02_dtExped = fields.Date(
        string="dtExped")
    esoc02_ufCnh = fields.Selection(
        ufCnh_TCnh,
        string="ufCnh", xsd_required=True)
    esoc02_dtValid = fields.Date(
        string="dtValid", xsd_required=True)
    esoc02_dtPriHab = fields.Date(
        string="dtPriHab")
    esoc02_categoriaCnh = fields.Char(
        string="categoriaCnh",
        xsd_required=True)


class TContato(spec_models.AbstractSpecMixin):
    "Informações de Contato"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.tcontato'
    _generateds_type = 'TContato'
    _concrete_rec_name = 'esoc_fonePrinc'

    esoc02_fonePrinc = fields.Char(
        string="fonePrinc")
    esoc02_foneAlternat = fields.Char(
        string="foneAlternat")
    esoc02_emailPrinc = fields.Char(
        string="emailPrinc")
    esoc02_emailAlternat = fields.Char(
        string="emailAlternat")


class TCtps(spec_models.AbstractSpecMixin):
    "Carteira de Trabalho e Previdência Social"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.tctps'
    _generateds_type = 'TCtps'
    _concrete_rec_name = 'esoc_nrCtps'

    esoc02_nrCtps = fields.Char(
        string="nrCtps", xsd_required=True)
    esoc02_serieCtps = fields.Char(
        string="serieCtps", xsd_required=True)
    esoc02_ufCtps = fields.Selection(
        ufCtps_TCtps,
        string="ufCtps", xsd_required=True)


class TDependente(spec_models.AbstractSpecMixin):
    _description = 'tdependente'
    _name = 'esoc.02.evttsvinici.tdependente'
    _generateds_type = 'TDependente'
    _concrete_rec_name = 'esoc_tpDep'

    esoc02_dependente_trabalhador_id = fields.Many2one(
        "esoc.02.evttsvinici.trabalhador")
    esoc02_tpDep = fields.Char(
        string="tpDep", xsd_required=True)
    esoc02_nmDep = fields.Char(
        string="nmDep", xsd_required=True)
    esoc02_dtNascto = fields.Date(
        string="dtNascto", xsd_required=True)
    esoc02_cpfDep = fields.Char(
        string="cpfDep")
    esoc02_depIRRF = fields.Char(
        string="depIRRF", xsd_required=True)
    esoc02_depSF = fields.Char(
        string="depSF", xsd_required=True)
    esoc02_incTrab = fields.Char(
        string="incTrab", xsd_required=True)


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evttsvinici.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TEnderecoBrasil(spec_models.AbstractSpecMixin):
    "Informações do Endereço no Brasil"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.tenderecobrasil'
    _generateds_type = 'TEnderecoBrasil'
    _concrete_rec_name = 'esoc_tpLograd'

    esoc02_tpLograd = fields.Char(
        string="tpLograd", xsd_required=True)
    esoc02_dscLograd = fields.Char(
        string="dscLograd", xsd_required=True)
    esoc02_nrLograd = fields.Char(
        string="nrLograd", xsd_required=True)
    esoc02_complemento = fields.Char(
        string="complemento")
    esoc02_bairro = fields.Char(
        string="bairro")
    esoc02_cep = fields.Char(
        string="cep", xsd_required=True)
    esoc02_codMunic = fields.Integer(
        string="codMunic", xsd_required=True)
    esoc02_uf = fields.Selection(
        uf_TEnderecoBrasil,
        string="uf", xsd_required=True)


class TEnderecoExterior(spec_models.AbstractSpecMixin):
    "Informações do Endereço no Exterior"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.tenderecoexterior'
    _generateds_type = 'TEnderecoExterior'
    _concrete_rec_name = 'esoc_paisResid'

    esoc02_paisResid = fields.Char(
        string="paisResid", xsd_required=True)
    esoc02_dscLograd = fields.Char(
        string="dscLograd", xsd_required=True)
    esoc02_nrLograd = fields.Char(
        string="nrLograd", xsd_required=True)
    esoc02_complemento = fields.Char(
        string="complemento")
    esoc02_bairro = fields.Char(
        string="bairro")
    esoc02_nmCid = fields.Char(
        string="nmCid", xsd_required=True)
    esoc02_codPostal = fields.Char(
        string="codPostal")


class TIdeEveTrab(spec_models.AbstractSpecMixin):
    "Identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.tideevetrab'
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


class TOc(spec_models.AbstractSpecMixin):
    "Órgão de Classe"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.toc'
    _generateds_type = 'TOc'
    _concrete_rec_name = 'esoc_nrOc'

    esoc02_nrOc = fields.Char(
        string="nrOc", xsd_required=True)
    esoc02_orgaoEmissor = fields.Char(
        string="orgaoEmissor",
        xsd_required=True)
    esoc02_dtExped = fields.Date(
        string="dtExped")
    esoc02_dtValid = fields.Date(
        string="dtValid")


class TRemun(spec_models.AbstractSpecMixin):
    "Remuneração e periodicidade de pagamento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.tremun'
    _generateds_type = 'TRemun'
    _concrete_rec_name = 'esoc_vrSalFx'

    esoc02_vrSalFx = fields.Monetary(
        string="vrSalFx", xsd_required=True)
    esoc02_undSalFixo = fields.Boolean(
        string="undSalFixo", xsd_required=True)
    esoc02_dscSalVar = fields.Char(
        string="dscSalVar")


class TRg(spec_models.AbstractSpecMixin):
    _description = 'trg'
    _name = 'esoc.02.evttsvinici.trg'
    _generateds_type = 'TRg'
    _concrete_rec_name = 'esoc_nrRg'

    esoc02_nrRg = fields.Char(
        string="nrRg", xsd_required=True)
    esoc02_orgaoEmissor = fields.Char(
        string="orgaoEmissor",
        xsd_required=True)
    esoc02_dtExped = fields.Date(
        string="dtExped")


class TRic(spec_models.AbstractSpecMixin):
    "Registro de Identificação Civil"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.tric'
    _generateds_type = 'TRic'
    _concrete_rec_name = 'esoc_nrRic'

    esoc02_nrRic = fields.Char(
        string="nrRic", xsd_required=True)
    esoc02_orgaoEmissor = fields.Char(
        string="orgaoEmissor",
        xsd_required=True)
    esoc02_dtExped = fields.Date(
        string="dtExped")


class TRne(spec_models.AbstractSpecMixin):
    "Registro Nacional de Estrangeiros"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.trne'
    _generateds_type = 'TRne'
    _concrete_rec_name = 'esoc_nrRne'

    esoc02_nrRne = fields.Char(
        string="nrRne", xsd_required=True)
    esoc02_orgaoEmissor = fields.Char(
        string="orgaoEmissor",
        xsd_required=True)
    esoc02_dtExped = fields.Date(
        string="dtExped")


class TTrabEstrang(spec_models.AbstractSpecMixin):
    "Informações do Trabalhador Estrangeiro"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.ttrabestrang'
    _generateds_type = 'TTrabEstrang'
    _concrete_rec_name = 'esoc_dtChegada'

    esoc02_dtChegada = fields.Date(
        string="dtChegada")
    esoc02_classTrabEstrang = fields.Boolean(
        string="classTrabEstrang",
        xsd_required=True)
    esoc02_casadoBr = fields.Char(
        string="casadoBr", xsd_required=True)
    esoc02_filhosBr = fields.Char(
        string="filhosBr", xsd_required=True)


class Afastamento(spec_models.AbstractSpecMixin):
    "Informações de afastamento do TSVE"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.afastamento'
    _generateds_type = 'afastamentoType'
    _concrete_rec_name = 'esoc_dtIniAfast'

    esoc02_dtIniAfast = fields.Date(
        string="dtIniAfast", xsd_required=True)
    esoc02_codMotAfast = fields.Char(
        string="codMotAfast", xsd_required=True)


class AgeIntegracao(spec_models.AbstractSpecMixin):
    "Agente de Integração"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.ageintegracao'
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
    _name = 'esoc.02.evttsvinici.cargofuncao'
    _generateds_type = 'cargoFuncaoType'
    _concrete_rec_name = 'esoc_codCargo'

    esoc02_codCargo = fields.Char(
        string="codCargo", xsd_required=True)
    esoc02_codFuncao = fields.Char(
        string="codFuncao")


class Documentos(spec_models.AbstractSpecMixin):
    "Informações dos documentos pessoais do trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.documentos'
    _generateds_type = 'documentosType'
    _concrete_rec_name = 'esoc_CTPS'

    esoc02_CTPS = fields.Many2one(
        "esoc.02.evttsvinici.tctps",
        string="Carteira de Trabalho e Previdência Social")
    esoc02_RIC = fields.Many2one(
        "esoc.02.evttsvinici.tric",
        string="Informações do Documento Nacional de Identidade",
        help="Informações do Documento Nacional de Identidade (DNI)")
    esoc02_RG = fields.Many2one(
        "esoc.02.evttsvinici.trg",
        string="Informações do Registro Geral (RG)")
    esoc02_RNE = fields.Many2one(
        "esoc.02.evttsvinici.trne",
        string="Informações do Registro Nacional de Estrangeiro")
    esoc02_OC = fields.Many2one(
        "esoc.02.evttsvinici.toc",
        string="Informações do número de registro em Órgão de Classe",
        help="Informações do número de registro em Órgão de Classe (OC)")
    esoc02_CNH = fields.Many2one(
        "esoc.02.evttsvinici.tcnh",
        string="Informações da Carteira Nacional de Habilitação",
        help="Informações da Carteira Nacional de Habilitação (CNH)")


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evttsvinici.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtTSVInicio'

    esoc02_evtTSVInicio = fields.Many2one(
        "esoc.02.evttsvinici.evttsvinicio",
        string="evtTSVInicio",
        xsd_required=True)


class Endereco(spec_models.AbstractSpecMixin):
    "Endereço do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.endereco'
    _generateds_type = 'enderecoType'
    _concrete_rec_name = 'esoc_brasil'

    esoc02_choice1 = fields.Selection([
        ('esoc02_brasil', 'brasil'),
        ('esoc02_exterior', 'exterior')],
        "brasil/exterior",
        default="esoc02_brasil")
    esoc02_brasil = fields.Many2one(
        "esoc.02.evttsvinici.tenderecobrasil",
        choice='1',
        string="Endereço no Brasil",
        xsd_required=True)
    esoc02_exterior = fields.Many2one(
        "esoc.02.evttsvinici.tenderecoexterior",
        choice='1',
        string="Endereço no Exterior",
        xsd_required=True)


class EvtTSVInicio(spec_models.AbstractSpecMixin):
    "TSVE - Início"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.evttsvinicio'
    _generateds_type = 'evtTSVInicioType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evttsvinici.tideevetrab",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evttsvinici.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_trabalhador = fields.Many2one(
        "esoc.02.evttsvinici.trabalhador",
        string="Grupo de Informações do Trabalhador",
        xsd_required=True)
    esoc02_infoTSVInicio = fields.Many2one(
        "esoc.02.evttsvinici.infotsvinicio",
        string="Trabalhador Sem Vínculo - Início",
        xsd_required=True)


class Fgts(spec_models.AbstractSpecMixin):
    "Informações relativas ao FGTS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.fgts'
    _generateds_type = 'fgtsType'
    _concrete_rec_name = 'esoc_opcFGTS'

    esoc02_opcFGTS = fields.Boolean(
        string="opcFGTS", xsd_required=True)
    esoc02_dtOpcFGTS = fields.Date(
        string="dtOpcFGTS")


class InfoComplementares(spec_models.AbstractSpecMixin):
    _description = 'infocomplementares'
    _name = 'esoc.02.evttsvinici.infocomplementares'
    _generateds_type = 'infoComplementaresType'
    _concrete_rec_name = 'esoc_cargoFuncao'

    esoc02_cargoFuncao = fields.Many2one(
        "esoc.02.evttsvinici.cargofuncao",
        string="Cargo/Função ocupado pelo Trabalhador Sem Vínculo")
    esoc02_remuneracao = fields.Many2one(
        "esoc.02.evttsvinici.tremun",
        string="Informações da remuneração e periodicidade de pagamento")
    esoc02_fgts = fields.Many2one(
        "esoc.02.evttsvinici.fgts",
        string="Informações relativas ao FGTS")
    esoc02_infoDirigenteSindical = fields.Many2one(
        "esoc.02.evttsvinici.infodirigentesindical",
        string="Empresa de Origem do Dirigente Sindical")
    esoc02_infoTrabCedido = fields.Many2one(
        "esoc.02.evttsvinici.tcessaotrab",
        string="Informações relativas ao trabalhador cedido",
        help="Informações relativas ao trabalhador cedido, preenchidas"
        "\nexclusivamente pelo cessionário")
    esoc02_infoEstagiario = fields.Many2one(
        "esoc.02.evttsvinici.infoestagiario",
        string="Informações relativas ao estagiário")


class InfoDeficiencia(spec_models.AbstractSpecMixin):
    "Pessoa com Deficiência"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.infodeficiencia'
    _generateds_type = 'infoDeficienciaType'
    _concrete_rec_name = 'esoc_defFisica'

    esoc02_defFisica = fields.Char(
        string="defFisica", xsd_required=True)
    esoc02_defVisual = fields.Char(
        string="defVisual", xsd_required=True)
    esoc02_defAuditiva = fields.Char(
        string="defAuditiva", xsd_required=True)
    esoc02_defMental = fields.Char(
        string="defMental", xsd_required=True)
    esoc02_defIntelectual = fields.Char(
        string="defIntelectual",
        xsd_required=True)
    esoc02_reabReadap = fields.Char(
        string="reabReadap", xsd_required=True)
    esoc02_observacao = fields.Char(
        string="observacao")


class InfoDirigenteSindical(spec_models.AbstractSpecMixin):
    "Empresa de Origem do Dirigente Sindical"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.infodirigentesindical'
    _generateds_type = 'infoDirigenteSindicalType'
    _concrete_rec_name = 'esoc_categOrig'

    esoc02_categOrig = fields.Integer(
        string="categOrig", xsd_required=True)
    esoc02_cnpjOrigem = fields.Char(
        string="cnpjOrigem")
    esoc02_dtAdmOrig = fields.Date(
        string="dtAdmOrig")
    esoc02_matricOrig = fields.Char(
        string="matricOrig")


class InfoEstagiario(spec_models.AbstractSpecMixin):
    "Informações relativas ao estagiário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.infoestagiario'
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
        "esoc.02.evttsvinici.instensino",
        string="Instituição de Ensino",
        xsd_required=True)
    esoc02_ageIntegracao = fields.Many2one(
        "esoc.02.evttsvinici.ageintegracao",
        string="Agente de Integração")
    esoc02_supervisorEstagio = fields.Many2one(
        "esoc.02.evttsvinici.supervisorestagio",
        string="Supervisor do Estágio")


class InfoTSVInicio(spec_models.AbstractSpecMixin):
    "Trabalhador Sem Vínculo - Início"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.infotsvinicio'
    _generateds_type = 'infoTSVInicioType'
    _concrete_rec_name = 'esoc_cadIni'

    esoc02_cadIni = fields.Char(
        string="cadIni", xsd_required=True)
    esoc02_codCateg = fields.Integer(
        string="codCateg", xsd_required=True)
    esoc02_dtInicio = fields.Date(
        string="dtInicio", xsd_required=True)
    esoc02_natAtividade = fields.Boolean(
        string="natAtividade")
    esoc02_infoComplementares = fields.Many2one(
        "esoc.02.evttsvinici.infocomplementares",
        string="infoComplementares")
    esoc02_mudancaCPF = fields.Many2one(
        "esoc.02.evttsvinici.mudancacpf",
        string="Informações de mudança de CPF do trabalhador")
    esoc02_afastamento = fields.Many2one(
        "esoc.02.evttsvinici.afastamento",
        string="Informações de afastamento do TSVE")
    esoc02_termino = fields.Many2one(
        "esoc.02.evttsvinici.termino",
        string="Informações de término do TSVE")


class InstEnsino(spec_models.AbstractSpecMixin):
    "Instituição de Ensino"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.instensino'
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


class MudancaCPF(spec_models.AbstractSpecMixin):
    "Informações de mudança de CPF do trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.mudancacpf'
    _generateds_type = 'mudancaCPFType'
    _concrete_rec_name = 'esoc_cpfAnt'

    esoc02_cpfAnt = fields.Char(
        string="cpfAnt", xsd_required=True)
    esoc02_dtAltCPF = fields.Date(
        string="dtAltCPF", xsd_required=True)
    esoc02_observacao = fields.Char(
        string="observacao")


class Nascimento(spec_models.AbstractSpecMixin):
    "Grupo de informações do nascimento do trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.nascimento'
    _generateds_type = 'nascimentoType'
    _concrete_rec_name = 'esoc_dtNascto'

    esoc02_dtNascto = fields.Date(
        string="dtNascto", xsd_required=True)
    esoc02_codMunic = fields.Integer(
        string="codMunic")
    esoc02_uf = fields.Selection(
        uf_nascimento,
        string="uf")
    esoc02_paisNascto = fields.Char(
        string="paisNascto", xsd_required=True)
    esoc02_paisNac = fields.Char(
        string="paisNac", xsd_required=True)
    esoc02_nmMae = fields.Char(
        string="nmMae")
    esoc02_nmPai = fields.Char(
        string="nmPai")


class SupervisorEstagio(spec_models.AbstractSpecMixin):
    "Supervisor do Estágio"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.supervisorestagio'
    _generateds_type = 'supervisorEstagioType'
    _concrete_rec_name = 'esoc_cpfSupervisor'

    esoc02_cpfSupervisor = fields.Char(
        string="cpfSupervisor",
        xsd_required=True)
    esoc02_nmSuperv = fields.Char(
        string="nmSuperv", xsd_required=True)


class Termino(spec_models.AbstractSpecMixin):
    "Informações de término do TSVE"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.termino'
    _generateds_type = 'terminoType'
    _concrete_rec_name = 'esoc_dtTerm'

    esoc02_dtTerm = fields.Date(
        string="dtTerm", xsd_required=True)


class Trabalhador(spec_models.AbstractSpecMixin):
    "Grupo de Informações do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttsvinici.trabalhador'
    _generateds_type = 'trabalhadorType'
    _concrete_rec_name = 'esoc_cpfTrab'

    esoc02_cpfTrab = fields.Char(
        string="cpfTrab", xsd_required=True)
    esoc02_nisTrab = fields.Char(
        string="nisTrab")
    esoc02_nmTrab = fields.Char(
        string="nmTrab", xsd_required=True)
    esoc02_sexo = fields.Char(
        string="sexo", xsd_required=True)
    esoc02_racaCor = fields.Boolean(
        string="racaCor", xsd_required=True)
    esoc02_estCiv = fields.Boolean(
        string="estCiv")
    esoc02_grauInstr = fields.Char(
        string="grauInstr", xsd_required=True)
    esoc02_nmSoc = fields.Char(
        string="nmSoc")
    esoc02_nascimento = fields.Many2one(
        "esoc.02.evttsvinici.nascimento",
        string="Grupo de informações do nascimento do trabalhador",
        xsd_required=True)
    esoc02_documentos = fields.Many2one(
        "esoc.02.evttsvinici.documentos",
        string="Informações dos documentos pessoais do trabalhador")
    esoc02_endereco = fields.Many2one(
        "esoc.02.evttsvinici.endereco",
        string="Endereço do Trabalhador",
        xsd_required=True)
    esoc02_trabEstrangeiro = fields.Many2one(
        "esoc.02.evttsvinici.ttrabestrang",
        string="Informações do Trabalhador Estrangeiro")
    esoc02_infoDeficiencia = fields.Many2one(
        "esoc.02.evttsvinici.infodeficiencia",
        string="Pessoa com Deficiência")
    esoc02_dependente = fields.One2many(
        "esoc.02.evttsvinici.tdependente",
        "esoc02_dependente_trabalhador_id",
        string="Informações dos dependentes"
    )
    esoc02_contato = fields.Many2one(
        "esoc.02.evttsvinici.tcontato",
        string="Informações de Contato")
