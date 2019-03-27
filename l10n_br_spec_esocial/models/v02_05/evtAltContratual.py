# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:22 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models

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


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtaltcontr.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TEnderecoBrasil(spec_models.AbstractSpecMixin):
    "Informações do Endereço no Brasil"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.tenderecobrasil'
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


class THorario(spec_models.AbstractSpecMixin):
    "Informações de Horário Contratual"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.thorario'
    _generateds_type = 'THorario'
    _concrete_rec_name = 'esoc_dia'

    esoc02_horario_horContratual_id = fields.Many2one(
        "esoc.02.evtaltcontr.horcontratual")
    esoc02_dia = fields.Boolean(
        string="dia", xsd_required=True)
    esoc02_codHorContrat = fields.Char(
        string="codHorContrat",
        xsd_required=True)


class TIdeEveTrab(spec_models.AbstractSpecMixin):
    "Identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.tideevetrab'
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


class TIdeVinculoNisObrig(spec_models.AbstractSpecMixin):
    "Informações do Vínculo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.tidevinculonisobrig'
    _generateds_type = 'TIdeVinculoNisObrig'
    _concrete_rec_name = 'esoc_cpfTrab'

    esoc02_cpfTrab = fields.Char(
        string="cpfTrab", xsd_required=True)
    esoc02_nisTrab = fields.Char(
        string="nisTrab", xsd_required=True)
    esoc02_matricula = fields.Char(
        string="matricula", xsd_required=True)


class TLocalTrab(spec_models.AbstractSpecMixin):
    "Informações do Local de Trabalho"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.tlocaltrab'
    _generateds_type = 'TLocalTrab'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)
    esoc02_descComp = fields.Char(
        string="descComp")


class TRemun(spec_models.AbstractSpecMixin):
    "Remuneração e periodicidade de pagamento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.tremun'
    _generateds_type = 'TRemun'
    _concrete_rec_name = 'esoc_vrSalFx'

    esoc02_vrSalFx = fields.Monetary(
        string="vrSalFx", xsd_required=True)
    esoc02_undSalFixo = fields.Boolean(
        string="undSalFixo", xsd_required=True)
    esoc02_dscSalVar = fields.Char(
        string="dscSalVar")


class AltContratual(spec_models.AbstractSpecMixin):
    "Informações do Contrato de Trabalho"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.altcontratual'
    _generateds_type = 'altContratualType'
    _concrete_rec_name = 'esoc_dtAlteracao'

    esoc02_dtAlteracao = fields.Date(
        string="dtAlteracao", xsd_required=True)
    esoc02_dtEf = fields.Date(
        string="dtEf")
    esoc02_dscAlt = fields.Char(
        string="dscAlt")
    esoc02_vinculo = fields.Many2one(
        "esoc.02.evtaltcontr.vinculo",
        string="Informações do vinculo",
        xsd_required=True)
    esoc02_infoRegimeTrab = fields.Many2one(
        "esoc.02.evtaltcontr.inforegimetrab",
        string="Informações do regime trabalhista",
        xsd_required=True)
    esoc02_infoContrato = fields.Many2one(
        "esoc.02.evtaltcontr.infocontrato",
        string="Informações do Contrato de Trabalho",
        xsd_required=True)


class AlvaraJudicial(spec_models.AbstractSpecMixin):
    "Dados do Alvará Judicial"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.alvarajudicial'
    _generateds_type = 'alvaraJudicialType'
    _concrete_rec_name = 'esoc_nrProcJud'

    esoc02_nrProcJud = fields.Char(
        string="nrProcJud", xsd_required=True)


class Aprend(spec_models.AbstractSpecMixin):
    "Informações relacionadas ao aprendiz"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.aprend'
    _generateds_type = 'aprendType'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class Duracao(spec_models.AbstractSpecMixin):
    "Duração do Contrato de Trabalho"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.duracao'
    _generateds_type = 'duracaoType'
    _concrete_rec_name = 'esoc_tpContr'

    esoc02_tpContr = fields.Boolean(
        string="tpContr", xsd_required=True)
    esoc02_dtTerm = fields.Date(
        string="dtTerm")
    esoc02_objDet = fields.Char(
        string="objDet")


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtaltcontr.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtAltContratual'

    esoc02_evtAltContratual = fields.Many2one(
        "esoc.02.evtaltcontr.evtaltcontratual",
        string="evtAltContratual",
        xsd_required=True)


class EvtAltContratual(spec_models.AbstractSpecMixin):
    "Evento Alteração Contratual"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.evtaltcontratual'
    _generateds_type = 'evtAltContratualType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtaltcontr.tideevetrab",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtaltcontr.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideVinculo = fields.Many2one(
        "esoc.02.evtaltcontr.tidevinculonisobrig",
        string="Informações de Identificação do Trabalhador e do Vínculo",
        xsd_required=True)
    esoc02_altContratual = fields.Many2one(
        "esoc.02.evtaltcontr.altcontratual",
        string="Informações do Contrato de Trabalho",
        xsd_required=True)


class FiliacaoSindical(spec_models.AbstractSpecMixin):
    "Filiação Sindical do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.filiacaosindical'
    _generateds_type = 'filiacaoSindicalType'
    _concrete_rec_name = 'esoc_cnpjSindTrab'

    esoc02_filiacaoSindical_infoContrato_id = fields.Many2one(
        "esoc.02.evtaltcontr.infocontrato")
    esoc02_cnpjSindTrab = fields.Char(
        string="cnpjSindTrab",
        xsd_required=True)


class HorContratual(spec_models.AbstractSpecMixin):
    "Informações do Horário Contratual do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.horcontratual'
    _generateds_type = 'horContratualType'
    _concrete_rec_name = 'esoc_qtdHrsSem'

    esoc02_qtdHrsSem = fields.Monetary(
        string="qtdHrsSem")
    esoc02_tpJornada = fields.Boolean(
        string="tpJornada", xsd_required=True)
    esoc02_dscTpJorn = fields.Char(
        string="dscTpJorn")
    esoc02_tmpParc = fields.Boolean(
        string="tmpParc", xsd_required=True)
    esoc02_horario = fields.One2many(
        "esoc.02.evtaltcontr.thorario",
        "esoc02_horario_horContratual_id",
        string="Informações diárias do horário contratual"
    )


class InfoCeletista(spec_models.AbstractSpecMixin):
    "Informações de Trabalhador Celetista"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.infoceletista'
    _generateds_type = 'infoCeletistaType'
    _concrete_rec_name = 'esoc_tpRegJor'

    esoc02_tpRegJor = fields.Boolean(
        string="tpRegJor", xsd_required=True)
    esoc02_natAtividade = fields.Boolean(
        string="natAtividade",
        xsd_required=True)
    esoc02_dtBase = fields.Boolean(
        string="dtBase")
    esoc02_cnpjSindCategProf = fields.Char(
        string="cnpjSindCategProf",
        xsd_required=True)
    esoc02_trabTemp = fields.Many2one(
        "esoc.02.evtaltcontr.trabtemp",
        string="Dados sobre trabalho temporário")
    esoc02_aprend = fields.Many2one(
        "esoc.02.evtaltcontr.aprend",
        string="Informações relacionadas ao aprendiz")


class InfoContrato(spec_models.AbstractSpecMixin):
    "Informações do Contrato de Trabalho"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.infocontrato'
    _generateds_type = 'infoContratoType'
    _concrete_rec_name = 'esoc_codCargo'

    esoc02_codCargo = fields.Char(
        string="codCargo")
    esoc02_codFuncao = fields.Char(
        string="codFuncao")
    esoc02_codCateg = fields.Integer(
        string="codCateg", xsd_required=True)
    esoc02_codCarreira = fields.Char(
        string="codCarreira")
    esoc02_dtIngrCarr = fields.Date(
        string="dtIngrCarr")
    esoc02_remuneracao = fields.Many2one(
        "esoc.02.evtaltcontr.tremun",
        string="Informações da remuneração e periodicidade de pagamento",
        xsd_required=True)
    esoc02_duracao = fields.Many2one(
        "esoc.02.evtaltcontr.duracao",
        string="Duração do Contrato de Trabalho",
        xsd_required=True)
    esoc02_localTrabalho = fields.Many2one(
        "esoc.02.evtaltcontr.localtrabalho",
        string="Informações do local de trabalho",
        xsd_required=True)
    esoc02_horContratual = fields.Many2one(
        "esoc.02.evtaltcontr.horcontratual",
        string="Informações do Horário Contratual do Trabalhador")
    esoc02_filiacaoSindical = fields.One2many(
        "esoc.02.evtaltcontr.filiacaosindical",
        "esoc02_filiacaoSindical_infoContrato_id",
        string="Filiação Sindical do Trabalhador"
    )
    esoc02_alvaraJudicial = fields.Many2one(
        "esoc.02.evtaltcontr.alvarajudicial",
        string="Dados do Alvará Judicial")
    esoc02_observacoes = fields.One2many(
        "esoc.02.evtaltcontr.observacoes",
        "esoc02_observacoes_infoContrato_id",
        string="Observações do contrato de trabalho"
    )
    esoc02_servPubl = fields.Many2one(
        "esoc.02.evtaltcontr.servpubl",
        string="Alterações inerentes ao servidor público")


class InfoEstatutario(spec_models.AbstractSpecMixin):
    "Informações de Trabalhador Estatutário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.infoestatutario'
    _generateds_type = 'infoEstatutarioType'
    _concrete_rec_name = 'esoc_tpPlanRP'

    esoc02_tpPlanRP = fields.Boolean(
        string="tpPlanRP", xsd_required=True)


class InfoRegimeTrab(spec_models.AbstractSpecMixin):
    "Informações do regime trabalhista"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.inforegimetrab'
    _generateds_type = 'infoRegimeTrabType'
    _concrete_rec_name = 'esoc_infoCeletista'

    esoc02_infoCeletista = fields.Many2one(
        "esoc.02.evtaltcontr.infoceletista",
        string="Informações de Trabalhador Celetista")
    esoc02_infoEstatutario = fields.Many2one(
        "esoc.02.evtaltcontr.infoestatutario",
        string="Informações de Trabalhador Estatutário")


class LocalTrabalho(spec_models.AbstractSpecMixin):
    "Informações do local de trabalho"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.localtrabalho'
    _generateds_type = 'localTrabalhoType'
    _concrete_rec_name = 'esoc_localTrabGeral'

    esoc02_localTrabGeral = fields.Many2one(
        "esoc.02.evtaltcontr.tlocaltrab",
        string="localTrabGeral",
        help="Estabelecimento onde o trabalhador exercerá suas atividades")
    esoc02_localTrabDom = fields.Many2one(
        "esoc.02.evtaltcontr.tenderecobrasil",
        string="localTrabDom",
        help="Endereço de trabalho do trabalhador doméstico e trabalhador"
        "\ntemporário")


class Observacoes(spec_models.AbstractSpecMixin):
    "Observações do contrato de trabalho"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.observacoes'
    _generateds_type = 'observacoesType'
    _concrete_rec_name = 'esoc_observacao'

    esoc02_observacoes_infoContrato_id = fields.Many2one(
        "esoc.02.evtaltcontr.infocontrato")
    esoc02_observacao = fields.Char(
        string="observacao", xsd_required=True)


class ServPubl(spec_models.AbstractSpecMixin):
    "Alterações inerentes ao servidor público"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.servpubl'
    _generateds_type = 'servPublType'
    _concrete_rec_name = 'esoc_mtvAlter'

    esoc02_mtvAlter = fields.Boolean(
        string="mtvAlter", xsd_required=True)


class TrabTemp(spec_models.AbstractSpecMixin):
    "Dados sobre trabalho temporário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.trabtemp'
    _generateds_type = 'trabTempType'
    _concrete_rec_name = 'esoc_justProrr'

    esoc02_justProrr = fields.Char(
        string="justProrr", xsd_required=True)


class Vinculo(spec_models.AbstractSpecMixin):
    "Informações do vinculo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaltcontr.vinculo'
    _generateds_type = 'vinculoType'
    _concrete_rec_name = 'esoc_tpRegPrev'

    esoc02_tpRegPrev = fields.Boolean(
        string="tpRegPrev", xsd_required=True)
