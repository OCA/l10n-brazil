# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:49 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models

# Identificação da UF da Seção Judiciária
ufVara_dadosProcJud = [
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


class TDadosProc(spec_models.AbstractSpecMixin):
    "Dados do processo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabproce.tdadosproc'
    _generateds_type = 'TDadosProc'
    _concrete_rec_name = 'esoc_indAutoria'

    esoc02_indAutoria = fields.Boolean(
        string="indAutoria")
    esoc02_indMatProc = fields.Boolean(
        string="indMatProc", xsd_required=True)
    esoc02_observacao = fields.Char(
        string="observacao")
    esoc02_dadosProcJud = fields.Many2one(
        "esoc.02.evttabproce.dadosprocjud",
        string="Informações Complementares do Processo Judicial")
    esoc02_infoSusp = fields.One2many(
        "esoc.02.evttabproce.infosusp",
        "esoc02_infoSusp_TDadosProc_id",
        string="Informações de suspensão de exigibilidade de tributos"
    )


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evttabproce.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeCadastro(spec_models.AbstractSpecMixin):
    "Identificação de evento de cadastro/tabelas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabproce.tidecadastro'
    _generateds_type = 'TIdeCadastro'
    _concrete_rec_name = 'esoc_tpAmb'

    esoc02_tpAmb = fields.Boolean(
        string="tpAmb", xsd_required=True)
    esoc02_procEmi = fields.Boolean(
        string="procEmi", xsd_required=True)
    esoc02_verProc = fields.Char(
        string="verProc", xsd_required=True)


class TIdeProcesso(spec_models.AbstractSpecMixin):
    "Informações de Identificação do Processo e Validade das Informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabproce.tideprocesso'
    _generateds_type = 'TIdeProcesso'
    _concrete_rec_name = 'esoc_tpProc'

    esoc02_tpProc = fields.Boolean(
        string="tpProc", xsd_required=True)
    esoc02_nrProc = fields.Char(
        string="nrProc", xsd_required=True)
    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class TPeriodoValidade(spec_models.AbstractSpecMixin):
    "Período de validade das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabproce.tperiodovalidade'
    _generateds_type = 'TPeriodoValidade'
    _concrete_rec_name = 'esoc_iniValid'

    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class Alteracao(spec_models.AbstractSpecMixin):
    "Alteração das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabproce.alteracao'
    _generateds_type = 'alteracaoType'
    _concrete_rec_name = 'esoc_ideProcesso'

    esoc02_ideProcesso = fields.Many2one(
        "esoc.02.evttabproce.tideprocesso",
        string="Informações de identificação do Processo",
        xsd_required=True)
    esoc02_dadosProc = fields.Many2one(
        "esoc.02.evttabproce.tdadosproc",
        string="Dados do processo",
        xsd_required=True)
    esoc02_novaValidade = fields.Many2one(
        "esoc.02.evttabproce.tperiodovalidade",
        string="Novo período de validade das informações")


class DadosProcJud(spec_models.AbstractSpecMixin):
    "Informações Complementares do Processo Judicial"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabproce.dadosprocjud'
    _generateds_type = 'dadosProcJudType'
    _concrete_rec_name = 'esoc_ufVara'

    esoc02_ufVara = fields.Selection(
        ufVara_dadosProcJud,
        string="ufVara", xsd_required=True)
    esoc02_codMunic = fields.Integer(
        string="codMunic", xsd_required=True)
    esoc02_idVara = fields.Integer(
        string="idVara", xsd_required=True)


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evttabproce.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtTabProcesso'

    esoc02_evtTabProcesso = fields.Many2one(
        "esoc.02.evttabproce.evttabprocesso",
        string="evtTabProcesso",
        xsd_required=True)


class EvtTabProcesso(spec_models.AbstractSpecMixin):
    "Evento Tabela de Processos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabproce.evttabprocesso'
    _generateds_type = 'evtTabProcessoType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evttabproce.tidecadastro",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evttabproce.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_infoProcesso = fields.Many2one(
        "esoc.02.evttabproce.infoprocesso",
        string="Informações do Processo",
        xsd_required=True)


class Exclusao(spec_models.AbstractSpecMixin):
    "Exclusão das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabproce.exclusao'
    _generateds_type = 'exclusaoType'
    _concrete_rec_name = 'esoc_ideProcesso'

    esoc02_ideProcesso = fields.Many2one(
        "esoc.02.evttabproce.tideprocesso",
        string="Identificação do Processo que será excluído",
        xsd_required=True)


class Inclusao(spec_models.AbstractSpecMixin):
    "Inclusão de novas informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabproce.inclusao'
    _generateds_type = 'inclusaoType'
    _concrete_rec_name = 'esoc_ideProcesso'

    esoc02_ideProcesso = fields.Many2one(
        "esoc.02.evttabproce.tideprocesso",
        string="Identificação do Processo",
        xsd_required=True)
    esoc02_dadosProc = fields.Many2one(
        "esoc.02.evttabproce.tdadosproc",
        string="Dados do processo",
        xsd_required=True)


class InfoProcesso(spec_models.AbstractSpecMixin):
    "Informações do Processo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabproce.infoprocesso'
    _generateds_type = 'infoProcessoType'
    _concrete_rec_name = 'esoc_inclusao'

    esoc02_choice1 = fields.Selection([
        ('esoc02_inclusao', 'inclusao'),
        ('esoc02_alteracao', 'alteracao'),
        ('esoc02_exclusao', 'exclusao')],
        "inclusao/alteracao/exclusao",
        default="esoc02_inclusao")
    esoc02_inclusao = fields.Many2one(
        "esoc.02.evttabproce.inclusao",
        choice='1',
        string="Inclusão de novas informações",
        xsd_required=True)
    esoc02_alteracao = fields.Many2one(
        "esoc.02.evttabproce.alteracao",
        choice='1',
        string="Alteração das informações",
        xsd_required=True)
    esoc02_exclusao = fields.Many2one(
        "esoc.02.evttabproce.exclusao",
        choice='1',
        string="Exclusão das informações",
        xsd_required=True)


class InfoSusp(spec_models.AbstractSpecMixin):
    "Informações de suspensão de exigibilidade de tributos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabproce.infosusp'
    _generateds_type = 'infoSuspType'
    _concrete_rec_name = 'esoc_codSusp'

    esoc02_infoSusp_TDadosProc_id = fields.Many2one(
        "esoc.02.evttabproce.tdadosproc")
    esoc02_codSusp = fields.Integer(
        string="codSusp", xsd_required=True)
    esoc02_indSusp = fields.Char(
        string="indSusp", xsd_required=True)
    esoc02_dtDecisao = fields.Date(
        string="dtDecisao", xsd_required=True)
    esoc02_indDeposito = fields.Char(
        string="indDeposito", xsd_required=True)
