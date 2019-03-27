# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:21 2019 by generateDS.py(Akretion's branch).
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


class TCnh(spec_models.AbstractSpecMixin):
    "Cartera Nacional de Habilitação"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcadas.tcnh'
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
    _name = 'esoc.02.evtaltcadas.tcontato'
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
    _name = 'esoc.02.evtaltcadas.tctps'
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
    _name = 'esoc.02.evtaltcadas.tdependente'
    _generateds_type = 'TDependente'
    _concrete_rec_name = 'esoc_tpDep'

    esoc02_dependente_dadosTrabalhador_id = fields.Many2one(
        "esoc.02.evtaltcadas.dadostrabalhador")
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
    _name = 'esoc.02.evtaltcadas.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TEnderecoBrasil(spec_models.AbstractSpecMixin):
    "Informações do Endereço no Brasil"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcadas.tenderecobrasil'
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
    _name = 'esoc.02.evtaltcadas.tenderecoexterior'
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
    _name = 'esoc.02.evtaltcadas.tideevetrab'
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
    _name = 'esoc.02.evtaltcadas.toc'
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


class TRg(spec_models.AbstractSpecMixin):
    _description = 'trg'
    _name = 'esoc.02.evtaltcadas.trg'
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
    _name = 'esoc.02.evtaltcadas.tric'
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
    _name = 'esoc.02.evtaltcadas.trne'
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
    _name = 'esoc.02.evtaltcadas.ttrabestrang'
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


class Alteracao(spec_models.AbstractSpecMixin):
    "Alteração de Dados Cadastrais do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcadas.alteracao'
    _generateds_type = 'alteracaoType'
    _concrete_rec_name = 'esoc_dtAlteracao'

    esoc02_dtAlteracao = fields.Date(
        string="dtAlteracao", xsd_required=True)
    esoc02_dadosTrabalhador = fields.Many2one(
        "esoc.02.evtaltcadas.dadostrabalhador",
        string="Informações Pessoais do Trabalhador",
        xsd_required=True)


class Aposentadoria(spec_models.AbstractSpecMixin):
    "Informação de aposentadoria do trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcadas.aposentadoria'
    _generateds_type = 'aposentadoriaType'
    _concrete_rec_name = 'esoc_trabAposent'

    esoc02_trabAposent = fields.Char(
        string="trabAposent", xsd_required=True)


class DadosTrabalhador(spec_models.AbstractSpecMixin):
    "Informações Pessoais do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcadas.dadostrabalhador'
    _generateds_type = 'dadosTrabalhadorType'
    _concrete_rec_name = 'esoc_nisTrab'

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
        "esoc.02.evtaltcadas.nascimento",
        string="Grupo de informações do nascimento do trabalhador",
        xsd_required=True)
    esoc02_documentos = fields.Many2one(
        "esoc.02.evtaltcadas.documentos",
        string="Informações dos documentos pessoais do trabalhador")
    esoc02_endereco = fields.Many2one(
        "esoc.02.evtaltcadas.endereco",
        string="Endereço do Trabalhador",
        xsd_required=True)
    esoc02_trabEstrangeiro = fields.Many2one(
        "esoc.02.evtaltcadas.ttrabestrang",
        string="Informações do Trabalhador Estrangeiro")
    esoc02_infoDeficiencia = fields.Many2one(
        "esoc.02.evtaltcadas.infodeficiencia",
        string="Pessoa com Deficiência")
    esoc02_dependente = fields.One2many(
        "esoc.02.evtaltcadas.tdependente",
        "esoc02_dependente_dadosTrabalhador_id",
        string="Informações dos dependentes"
    )
    esoc02_aposentadoria = fields.Many2one(
        "esoc.02.evtaltcadas.aposentadoria",
        string="Informação de aposentadoria do trabalhador")
    esoc02_contato = fields.Many2one(
        "esoc.02.evtaltcadas.tcontato",
        string="Informações de Contato")


class Documentos(spec_models.AbstractSpecMixin):
    "Informações dos documentos pessoais do trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcadas.documentos'
    _generateds_type = 'documentosType'
    _concrete_rec_name = 'esoc_CTPS'

    esoc02_CTPS = fields.Many2one(
        "esoc.02.evtaltcadas.tctps",
        string="Carteira de Trabalho e Previdência Social")
    esoc02_RIC = fields.Many2one(
        "esoc.02.evtaltcadas.tric",
        string="Informações do Documento Nacional de Identidade",
        help="Informações do Documento Nacional de Identidade (DNI)")
    esoc02_RG = fields.Many2one(
        "esoc.02.evtaltcadas.trg",
        string="Informações do Registro Geral (RG)")
    esoc02_RNE = fields.Many2one(
        "esoc.02.evtaltcadas.trne",
        string="Informações do Registro Nacional de Estrangeiro")
    esoc02_OC = fields.Many2one(
        "esoc.02.evtaltcadas.toc",
        string="Informações do número de registro em Órgão de Classe",
        help="Informações do número de registro em Órgão de Classe (OC)")
    esoc02_CNH = fields.Many2one(
        "esoc.02.evtaltcadas.tcnh",
        string="Informações da Carteira Nacional de Habilitação",
        help="Informações da Carteira Nacional de Habilitação (CNH)")


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtaltcadas.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtAltCadastral'

    esoc02_evtAltCadastral = fields.Many2one(
        "esoc.02.evtaltcadas.evtaltcadastral",
        string="evtAltCadastral",
        xsd_required=True)


class Endereco(spec_models.AbstractSpecMixin):
    "Endereço do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcadas.endereco'
    _generateds_type = 'enderecoType'
    _concrete_rec_name = 'esoc_brasil'

    esoc02_choice1 = fields.Selection([
        ('esoc02_brasil', 'brasil'),
        ('esoc02_exterior', 'exterior')],
        "brasil/exterior",
        default="esoc02_brasil")
    esoc02_brasil = fields.Many2one(
        "esoc.02.evtaltcadas.tenderecobrasil",
        choice='1',
        string="Endereço no Brasil",
        xsd_required=True)
    esoc02_exterior = fields.Many2one(
        "esoc.02.evtaltcadas.tenderecoexterior",
        choice='1',
        string="Endereço no Exterior",
        xsd_required=True)


class EvtAltCadastral(spec_models.AbstractSpecMixin):
    "Evento Alteração Cadastral do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcadas.evtaltcadastral'
    _generateds_type = 'evtAltCadastralType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtaltcadas.tideevetrab",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtaltcadas.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideTrabalhador = fields.Many2one(
        "esoc.02.evtaltcadas.idetrabalhador",
        string="Identificação do Trabalhador",
        xsd_required=True)
    esoc02_alteracao = fields.Many2one(
        "esoc.02.evtaltcadas.alteracao",
        string="Alteração de Dados Cadastrais do Trabalhador",
        xsd_required=True)


class IdeTrabalhador(spec_models.AbstractSpecMixin):
    "Identificação do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcadas.idetrabalhador'
    _generateds_type = 'ideTrabalhadorType'
    _concrete_rec_name = 'esoc_cpfTrab'

    esoc02_cpfTrab = fields.Char(
        string="cpfTrab", xsd_required=True)


class InfoDeficiencia(spec_models.AbstractSpecMixin):
    "Pessoa com Deficiência"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcadas.infodeficiencia'
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
    esoc02_infoCota = fields.Char(
        string="infoCota")
    esoc02_observacao = fields.Char(
        string="observacao")


class Nascimento(spec_models.AbstractSpecMixin):
    "Grupo de informações do nascimento do trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcadas.nascimento'
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
