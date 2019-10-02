# -*- coding: utf-8 -*-
# 2019 ABGF - Hendrix Costa <hendrix.costa@abgf.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from .abstract_arquivos_governo import AbstractArquivosGoverno


class Dirf(AbstractArquivosGoverno):

    def __init__(self, *args, **kwargs):

        # 3.1 Registro de identificação da declaração (identificador Dirf)
        self.identificador_de_registro = 'Dirf'
        self.ano_referencia = 2019
        self.ano_calendario = 2019              # 2019 ou 2018
        self.indicador_de_retificadora = 'N'    # S – Retificadora N – Original
        self.numero_do_recibo = '-'
        self.identificador_de_estrutura_do_leiaute = 'T17BS45'

        # 3.2 Registro do Responsável pelo preenchimento da declaração
        # (identificador RESPO)
        self.identificador_de_registro_respo = 'RESPO'        # sempre 'RESPO'
        self.cpf_respo = ''
        self.nome_respo = ''
        self.ddd_respo = ''
        self.telefone_respo = ''
        self.ramal_respo = ''
        self.fax_respo = ''
        self.correio_eletronico = ''

        # 3.3 Registro de identificação do declarante pessoa física
        # (identificador DECPF)
        self.identificador_de_registro_decpf = 'DECPF'
        self.cpf_decpf = ''
        self.nome_decpf = ''
        self.residente_exterior = 'N'
        self.titular_serivocs_notariais = 'N'
        self.plano_privado_assistencia_saude_decpf = 'N'
        self.socio_ostensivo_decpf = 'N'
        self.situacao_especial_declaracao = 'N'
        self.data_do_evento_decpf = ''
        self.tipo_de_evento = ''
        self.declarante_falecido = ''
        self.data_do_obito = ''
        self.situacao_do_espolio = ''
        self.cpf_inventariante = ''
        self.nome_do_inventariante = ''

        # 3.4 Registro de identificação do declarante pessoa jurídica
        # (identificador DECPJ)
        self.identificador_de_registro_decpj = 'DECPJ'
        self.cnpj_decpj = ''
        self.nome_empresarial = ''
        self.natureza_do_declarante = ''
        self.cpf_responsavel = ''
        self.socio_ostensivo_decpj = ''
        self.declarante_depositario_de_credito = ''
        self.declarante_de_instituicao_administradora = ''
        self.rendimento_pago_no_exterior = 'N'
        self.plano_privado_assistencia_saude_decpj = 'N'
        self.pagamento_a_entidades_imunes = ''
        self.fundacao_publica_direito_privado = ''
        self.situacao_especial_declarante = 'N'
        self.data_do_evento_decpj = ''

        # 3.5 Registro de identificação do código de receita
        # (identificador IDREC)
        self.identificador_de_registro_idrec = 'IDREC'
        self.codigo_da_receita = ''

        # 3.6 Registro de beneficiário pessoa física do declarante
        # (identificador BPFDEC)
        self.identificador_de_registro_bpfdec = 'BPFDEC'
        self.cpf_bpfdec = ''
        self.nome_bpfdec = ''
        self.data_laudo = ''
        self.identificacao_alimentado_bpfdec = ''
        self.identificacao_previdencia_complementar = ''

        # 3.7 Registro de beneficiário pessoa jurídica do declarante
        # (identificador BPJDEC)
        self.identificador_de_registro_bpjdec = 'BPJDEC'
        self.cnpj_bpjdec = ''
        self.nome_empresarial_bpjdec =''

        # 3.8 Registro de valores pagos às entidades imunes e isentas
        # (identificador VPEIM)
        self.identificador_de_registro_vpeim = 'VPEIM'
        self.cnpj_vpeim = ''
        self.nome_empresarial_vpeim = ''

        # 3.9 Registro de identificação do fundo ou clube de investimento
        # (identificador FCI)
        self.identificador_de_registro_fci = 'FCI'
        self.cnpj_fci = ''
        self.nome_empresarial_fci = ''

        # 3.10 Registro do beneficiário pessoa física do fundo ou
        # clube de investimento (identificador BPFFCI)
        self.identificador_de_registro_bpffci = 'BPFFCI'
        self.cpf_bpffci = ''
        self.nome_bpffci = ''
        self.data_laudo_bpffci = ''

        # 3.11 Registro do beneficiário pessoa jurídica do fundo ou
        # clube de investimento (identificador BPJFCI)
        self.identificador_de_registro_bpjfci = 'BPJFCI'
        self.cnpj_bpjfci = ''
        self.nome_empresarial_bpjfci = ''

        # 3.12 Registro de processo da justiça do
        # trabalho/federal/estadual/Distrito Federal (identificador PROC)
        self.identificador_de_registro_proc = 'PROC'
        self.indicador_de_justica = ''
        self.numero_do_processo_proc = ''
        self.indicador_de_tipo_advogado_proc = ''
        self.cpf_cnpj_advogado_proc = ''
        self.nome_advogado_proc = ''
        self.valor_pag_advogado_proc = ''

        # 3.13 Registro de beneficiário pessoa física do processo da justiça
        # do trabalho/federal/estadual/Distrito Federal (identificador BPFPROC)
        self.identificador_de_registro_bpfproc = 'BPFPROC'
        self.cpf_bpfproc = ''
        self.nome_bpfproc = ''
        self.data_laudo_bpfproc = ''

        # 3.14 Registro de beneficiário pessoa jurídica do processo da justiça
        # do trabalho/federal/estadual/Distrito Federal (identificador BPJPROC)
        self.identificador_de_registro_bpjproc = 'BPJPROC'
        self.cnpj_bpjproc = ''
        self.nome_empresarial_bpjproc = ''

        # 3.15 Registro de rendimentos recebidos acumuladamente
        # (identificador RRA)
        self.identificador_de_registro_rra = 'RRA'
        self.identificador_rendimento_recebido_acumuladamente = ''
        self.numero_do_processo_rra = ''
        self.indicador_de_tipo_advogado_rra = ''
        self.cpf_cnpj_advogado_rra = ''
        self.nome_advogado_rra = ''
        self.valor_pag_advogado_rra = ''

        # 3.16 Registro de beneficiário pessoa física dos rendimentos
        # recebidos acumuladamente (identificador BPFRRA)
        self.identificador_de_registro_bpfrra = 'BPFRRA'
        self.cpf_bpfrra = ''
        self.nome_bpfrra = ''
        self.natureza_do_rra = ''
        self.data_laudo_bpfrra = ''
        self.identificacao_alimentado_bpfrra = ''

        # 3.17 Registro de identificação de Previdência Complementar
        # (identificador INFPC)
        self.identificador_de_registro_infpc = 'INFPC'
        self.cnpj_infpc = ''
        self.nome_empresarial_infpc = ''

        # 3.18 Registro de informações do beneficiário da pensão alimentícia
        # (identificador INFPA)
        self.identificador_de_registro_infpa = 'INFPA'
        self.cpf_infpa = ''
        self.data_nascimento_infpa = ''
        self.relacao_dependencia_infpa = ''

        # 3.19 Registro de valores mensais (identificadores RTRT, RTPO, RTPP,
        # RTFA, RTSP, RTEP, RTDP, RTPA, RTIRF, CJAA, CJAC, ESRT, ESPO, ESPP,
        # ESFA, ESSP, ESEP, ESDP, ESPA, ESIR, ESDJ, RIP65, RIDAC, RIIRP, RIAP,
        # RIMOG, RIVC, RIBMR, RICAP, RISCP, RIMUN, RISEN e DAJUD)
        self.identificador_de_registro_mensal = ''
        self.janeiro = ''
        self.fevereiro = ''
        self.marco = ''
        self.abril = ''
        self.maio = ''
        self.junho = ''
        self.julho = ''
        self.agosto = ''
        self.setembro = ''
        self.outubro = ''
        self.novembro = ''
        self.dezembro = ''
        self.decimo_terceiro = ''

        # 3.20 Registro de valores anuais isentos/sem retenção
        # (identificadores RIL96, RIPTS e RIRSR)
        self.identificador_de_registro_anual = ''
        self.valor_pago_ano = ''

        # 3.21 Registro de valores anuais de rendimentos isentos – outros
        # (identificador RIO)
        self.identificador_de_registro_rio = 'RIO'
        self.valor_pago_ano_rio = ''
        self.descricao_rendimentos_isentos = ''

        # 3.22 Registro de quantidade de meses (identificador QTMESES)
        self.identificacao_de_registro_qtmeses = 'QTMESES'
        self.qtd_meses_janeiro = ''
        self.qtd_meses_fevereiro = ''
        self.qtd_meses_marco = ''
        self.qtd_meses_abril = ''
        self.qtd_meses_maio = ''
        self.qtd_meses_junho = ''
        self.qtd_meses_julho = ''
        self.qtd_meses_agosto = ''
        self.qtd_meses_setembro = ''
        self.qtd_meses_outubro = ''
        self.qtd_meses_novembro = ''
        self.qtd_meses_dezembro = ''

        # 3.23 Registro de informações da Sociedade em Conta de Participação
        # (identificador SCP)
        self.identificador_de_registro_scp = 'SCP'
        self.cnpj_scp = ''
        self.nome_scp = ''

        # 3.24 Registro de beneficiário pessoa física da sociedade em conta
        # de participação (identificador BPFSCP)
        self.identificador_de_registro_bpfscp = 'BPFSCP'
        self.cpf_bpfscp = ''
        self.nome_bpfscp = ''
        self.percentual_participacao_na_scp_bpfscp = ''

        # 3.25 Registro de beneficiário pessoa jurídica da sociedade em conta
        # de participação (identificador BPJSCP)
        self.identificador_de_registro_bpjscp = 'BPJSCP'
        self.cnpj_bpjscp = ''
        self.nome_empresarial_bpjscp = ''
        self.percentual_participacao_na_scp_bpjscp = ''

        # 3.26 Registro de pagamentos a plano privado de assistência à saúde
        # – coletivo empresarial (identificador PSE)
        self.identificador_de_registro_pse = 'PSE'

        # 3.27 Registro de operadora do plano privado de assistência à saúde
        # – coletivo empresarial (identificador OPSE)
        self.identificador_de_registro_opse = 'OPSE'
        self.cnpj_opse = ''
        self.nome_empresarial_opse = ''
        self.registro_ans_opse = ''

        # 3.28 Registro de titular do plano privado de assistência à saúde
        # – coletivo empresarial (identificador TPSE)
        self.identificador_de_registro_tpse = 'TPSE'
        self.cpf_tpse = ''
        self.nome_tpse = ''
        self.valor_pago_ano_tpse = ''

        # 3.29 Registro de informação de reembolso do titular do plano de saúde
        # – coletivo empresarial (identificador RTPSE)
        self.identificador_de_registro_rtpse = 'RTPSE'
        self.cpf_rtpse = ''
        self.nome_rtpse = ''
        self.valor_reembolso_ano_calendario = ''
        self.valor_reembolso_ano_anterior = ''

        # 3.30 Registro de dependente do plano privado de assistência à saúde
        # – coletivo empresarial (identificador DTPSE)
        self.identificador_de_registro_dtpse = 'DTPSE'
        self.cpf_dependente_dtpse = ''
        self.data_nascimento_dtpse = ''
        self.nome_dtpse = ''
        self.relacao_dependencia_dtpse = ''
        self.valor_pago_ano_dtpse = ''

        # 3.31 Registro de informação de reembolso do dependente
        # (identificador RDTPSE):
        self.identificador_de_registro_rdtpse = 'RDTPSE'
        self.cpf_rdtpse = ''
        self.nome_rdtpse = ''
        self.valor_reembolso_ano_calendario_rdtpse = ''
        self.valor_reembolso_ano_anterior_rdtpse = ''

        # 3.32 Registro de rendimentos pagos a residentes ou domiciliados
        # no exterior (identificador RPDE)
        self.identificador_de_registro_rpde = 'RPDE'

        # 3.33 Registro de beneficiário dos rendimentos pagos a residentes ou
        # domiciliados no exterior (identificador BRPDE)
        self.identificador_de_registro_brpde = 'BRPDE'
        self.beneficiario_brpde = ''
        self.codigo_pais_brpde = ''
        self.nif_brpde = ''
        self.beneficiario_dispensado_nif = ''
        self.pais_dispensado_nif = ''
        self.cpf_brpde = ''
        self.nome_brpde = ''
        self.relacao_fonte_pagadora_beneficiario = ''
        self.logradouro_brpde = ''
        self.numero_brpde = ''
        self.complemento_brpde = ''
        self.bairro_brpde = ''
        self.codigo_postal = ''
        self.cidade_brpde = ''
        self.estado_brpde = ''
        self.telefone_brpde = ''

        # 3.34 Registro de valores de rendimentos pagos a residentes ou
        # domiciliados no exterior (identificador VRPDE)
        self.identificador_de_registro_vrpde = 'VRPDE'
        self.data_pagamento_vrpde = ''
        self.codigo_receita_vrpde = ''
        self.tipo_rendimento_vrpde = ''
        self.rendimento_pago_vrpde = ''
        self.imposto_retido_vrpde = ''
        self.forma_tributacao = ''

        # 3.35 Registro de informações complementares para o comprovante de
        # rendimento (identificador INF)
        self.identificador_de_registro_inf = 'INF'
        self.cpf_inf = ''
        self.informacoes_complementares = ''

        #  Registro identificador do término da declaração
        #  (identificador FIMDirf)
        self.identificador_de_registro_fimdirf = 'FIMDirf'
