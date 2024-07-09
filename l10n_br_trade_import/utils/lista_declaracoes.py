from dataclasses import dataclass, field
from typing import List, Optional, Union

from xsdata.models.datatype import XmlPeriod


@dataclass
class Armazem:
    class Meta:
        name = "armazem"

    nome_armazem: Optional[str] = field(
        default=None,
        metadata={
            "name": "nomeArmazem",
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class DeclaracaoEe:
    class Meta:
        name = "declaracaoEe"

    faixa_final: Optional[XmlPeriod] = field(
        default=None,
        metadata={
            "name": "faixaFinal",
            "type": "Element",
            "required": True,
        },
    )
    faixa_inicial: Optional[XmlPeriod] = field(
        default=None,
        metadata={
            "name": "faixaInicial",
            "type": "Element",
            "required": True,
        },
    )
    numero_declaracao_estrangeira: Optional[str] = field(
        default=None,
        metadata={
            "name": "numeroDeclaracaoEstrangeira",
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class Deducao:
    class Meta:
        name = "deducao"

    codigo_deducao: Optional[int] = field(
        default=None,
        metadata={
            "name": "codigoDeducao",
            "type": "Element",
            "required": True,
        },
    )
    denominacao: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    moeda_negociada_codigo: Optional[int] = field(
        default=None,
        metadata={
            "name": "moedaNegociadaCodigo",
            "type": "Element",
            "required": True,
        },
    )
    moeda_negociada_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "moedaNegociadaNome",
            "type": "Element",
            "required": True,
        },
    )
    valor_moeda_negociada: Optional[str] = field(
        default=None,
        metadata={
            "name": "valorMoedaNegociada",
            "type": "Element",
            "required": True,
        },
    )
    valor_reais: Optional[str] = field(
        default=None,
        metadata={
            "name": "valorReais",
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class DocumentoInstrucaoDespacho:
    class Meta:
        name = "documentoInstrucaoDespacho"

    codigo_tipo_documento_despacho: Optional[Union[int, str]] = field(
        default=None,
        metadata={
            "name": "codigoTipoDocumentoDespacho",
            "type": "Element",
            "required": True,
        },
    )
    nome_documento_despacho: Optional[str] = field(
        default=None,
        metadata={
            "name": "nomeDocumentoDespacho",
            "type": "Element",
            "required": True,
        },
    )
    numero_documento_despacho: Optional[str] = field(
        default=None,
        metadata={
            "name": "numeroDocumentoDespacho",
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class Embalagem:
    class Meta:
        name = "embalagem"

    codigo_tipo_embalagem: Optional[int] = field(
        default=None,
        metadata={
            "name": "codigoTipoEmbalagem",
            "type": "Element",
            "required": True,
        },
    )
    nome_embalagem: Optional[str] = field(
        default=None,
        metadata={
            "name": "nomeEmbalagem",
            "type": "Element",
            "required": True,
        },
    )
    quantidade_volume: Optional[str] = field(
        default=None,
        metadata={
            "name": "quantidadeVolume",
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class Mercadoria:
    class Meta:
        name = "mercadoria"

    descricao_mercadoria: Optional[str] = field(
        default=None,
        metadata={
            "name": "descricaoMercadoria",
            "type": "Element",
            "required": True,
        },
    )
    numero_sequencial_item: Optional[str] = field(
        default=None,
        metadata={
            "name": "numeroSequencialItem",
            "type": "Element",
            "required": True,
        },
    )
    quantidade: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    unidade_medida: Optional[str] = field(
        default=None,
        metadata={
            "name": "unidadeMedida",
            "type": "Element",
            "required": True,
        },
    )
    valor_unitario: Optional[str] = field(
        default=None,
        metadata={
            "name": "valorUnitario",
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class Pagamento:
    class Meta:
        name = "pagamento"

    agencia_pagamento: Optional[XmlPeriod] = field(
        default=None,
        metadata={
            "name": "agenciaPagamento",
            "type": "Element",
            "required": True,
        },
    )
    banco_pagamento: Optional[str] = field(
        default=None,
        metadata={
            "name": "bancoPagamento",
            "type": "Element",
            "required": True,
        },
    )
    codigo_receita: Optional[Union[int, XmlPeriod]] = field(
        default=None,
        metadata={
            "name": "codigoReceita",
            "type": "Element",
            "required": True,
        },
    )
    codigo_tipo_pagamento: Optional[int] = field(
        default=None,
        metadata={
            "name": "codigoTipoPagamento",
            "type": "Element",
            "required": True,
        },
    )
    conta_pagamento: Optional[int] = field(
        default=None,
        metadata={
            "name": "contaPagamento",
            "type": "Element",
            "required": True,
        },
    )
    data_pagamento: Optional[int] = field(
        default=None,
        metadata={
            "name": "dataPagamento",
            "type": "Element",
            "required": True,
        },
    )
    nome_tipo_pagamento: Optional[str] = field(
        default=None,
        metadata={
            "name": "nomeTipoPagamento",
            "type": "Element",
            "required": True,
        },
    )
    numero_retificacao: Optional[str] = field(
        default=None,
        metadata={
            "name": "numeroRetificacao",
            "type": "Element",
            "required": True,
        },
    )
    valor_juros_encargos: Optional[str] = field(
        default=None,
        metadata={
            "name": "valorJurosEncargos",
            "type": "Element",
            "required": True,
        },
    )
    valor_multa: Optional[str] = field(
        default=None,
        metadata={
            "name": "valorMulta",
            "type": "Element",
            "required": True,
        },
    )
    valor_receita: Optional[str] = field(
        default=None,
        metadata={
            "name": "valorReceita",
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class Adicao:
    class Meta:
        name = "adicao"

    cide_valor_aliquota_especifica: Optional[str] = field(
        default=None,
        metadata={
            "name": "cideValorAliquotaEspecifica",
            "type": "Element",
            "required": True,
        },
    )
    cide_valor_devido: Optional[str] = field(
        default=None,
        metadata={
            "name": "cideValorDevido",
            "type": "Element",
            "required": True,
        },
    )
    cide_valor_recolher: Optional[str] = field(
        default=None,
        metadata={
            "name": "cideValorRecolher",
            "type": "Element",
            "required": True,
        },
    )
    codigo_relacao_comprador_vendedor: Optional[int] = field(
        default=None,
        metadata={
            "name": "codigoRelacaoCompradorVendedor",
            "type": "Element",
            "required": True,
        },
    )
    codigo_vinculo_comprador_vendedor: Optional[int] = field(
        default=None,
        metadata={
            "name": "codigoVinculoCompradorVendedor",
            "type": "Element",
            "required": True,
        },
    )
    cofins_aliquota_ad_valorem: Optional[str] = field(
        default=None,
        metadata={
            "name": "cofinsAliquotaAdValorem",
            "type": "Element",
            "required": True,
        },
    )
    cofins_aliquota_especifica_quantidade_unidade: Optional[str] = field(
        default=None,
        metadata={
            "name": "cofinsAliquotaEspecificaQuantidadeUnidade",
            "type": "Element",
            "required": True,
        },
    )
    cofins_aliquota_especifica_valor: Optional[str] = field(
        default=None,
        metadata={
            "name": "cofinsAliquotaEspecificaValor",
            "type": "Element",
            "required": True,
        },
    )
    cofins_aliquota_reduzida: Optional[str] = field(
        default=None,
        metadata={
            "name": "cofinsAliquotaReduzida",
            "type": "Element",
            "required": True,
        },
    )
    cofins_aliquota_valor_devido: Optional[str] = field(
        default=None,
        metadata={
            "name": "cofinsAliquotaValorDevido",
            "type": "Element",
            "required": True,
        },
    )
    cofins_aliquota_valor_recolher: Optional[str] = field(
        default=None,
        metadata={
            "name": "cofinsAliquotaValorRecolher",
            "type": "Element",
            "required": True,
        },
    )
    condicao_venda_incoterm: Optional[str] = field(
        default=None,
        metadata={
            "name": "condicaoVendaIncoterm",
            "type": "Element",
            "required": True,
        },
    )
    condicao_venda_local: Optional[str] = field(
        default=None,
        metadata={
            "name": "condicaoVendaLocal",
            "type": "Element",
            "required": True,
        },
    )
    condicao_venda_metodo_valoracao_codigo: Optional[str] = field(
        default=None,
        metadata={
            "name": "condicaoVendaMetodoValoracaoCodigo",
            "type": "Element",
            "required": True,
        },
    )
    condicao_venda_metodo_valoracao_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "condicaoVendaMetodoValoracaoNome",
            "type": "Element",
            "required": True,
        },
    )
    condicao_venda_moeda_codigo: Optional[int] = field(
        default=None,
        metadata={
            "name": "condicaoVendaMoedaCodigo",
            "type": "Element",
            "required": True,
        },
    )
    condicao_venda_moeda_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "condicaoVendaMoedaNome",
            "type": "Element",
            "required": True,
        },
    )
    condicao_venda_valor_moeda: Optional[str] = field(
        default=None,
        metadata={
            "name": "condicaoVendaValorMoeda",
            "type": "Element",
            "required": True,
        },
    )
    condicao_venda_valor_reais: Optional[str] = field(
        default=None,
        metadata={
            "name": "condicaoVendaValorReais",
            "type": "Element",
            "required": True,
        },
    )
    dados_cambiais_cobertura_cambial_codigo: Optional[int] = field(
        default=None,
        metadata={
            "name": "dadosCambiaisCoberturaCambialCodigo",
            "type": "Element",
            "required": True,
        },
    )
    dados_cambiais_cobertura_cambial_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "dadosCambiaisCoberturaCambialNome",
            "type": "Element",
            "required": True,
        },
    )
    dados_cambiais_instituicao_financiadora_codigo: Optional[str] = field(
        default=None,
        metadata={
            "name": "dadosCambiaisInstituicaoFinanciadoraCodigo",
            "type": "Element",
            "required": True,
        },
    )
    dados_cambiais_instituicao_financiadora_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "dadosCambiaisInstituicaoFinanciadoraNome",
            "type": "Element",
            "required": True,
        },
    )
    dados_cambiais_motivo_sem_cobertura_codigo: Optional[str] = field(
        default=None,
        metadata={
            "name": "dadosCambiaisMotivoSemCoberturaCodigo",
            "type": "Element",
            "required": True,
        },
    )
    dados_cambiais_motivo_sem_cobertura_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "dadosCambiaisMotivoSemCoberturaNome",
            "type": "Element",
            "required": True,
        },
    )
    dados_cambiais_valor_real_cambio: Optional[str] = field(
        default=None,
        metadata={
            "name": "dadosCambiaisValorRealCambio",
            "type": "Element",
            "required": True,
        },
    )
    dados_carga_pais_procedencia_codigo: Optional[str] = field(
        default=None,
        metadata={
            "name": "dadosCargaPaisProcedenciaCodigo",
            "type": "Element",
            "required": True,
        },
    )
    dados_carga_urf_entrada_codigo: Optional[str] = field(
        default=None,
        metadata={
            "name": "dadosCargaUrfEntradaCodigo",
            "type": "Element",
            "required": True,
        },
    )
    dados_carga_via_transporte_codigo: Optional[str] = field(
        default=None,
        metadata={
            "name": "dadosCargaViaTransporteCodigo",
            "type": "Element",
            "required": True,
        },
    )
    dados_mercadoria_aplicacao: Optional[str] = field(
        default=None,
        metadata={
            "name": "dadosMercadoriaAplicacao",
            "type": "Element",
            "required": True,
        },
    )
    dados_mercadoria_codigo_naladi_ncca: Optional[str] = field(
        default=None,
        metadata={
            "name": "dadosMercadoriaCodigoNaladiNCCA",
            "type": "Element",
            "required": True,
        },
    )
    dados_mercadoria_codigo_naladi_sh: Optional[int] = field(
        default=None,
        metadata={
            "name": "dadosMercadoriaCodigoNaladiSH",
            "type": "Element",
            "required": True,
        },
    )
    dados_mercadoria_codigo_ncm: Optional[int] = field(
        default=None,
        metadata={
            "name": "dadosMercadoriaCodigoNcm",
            "type": "Element",
            "required": True,
        },
    )
    dados_mercadoria_condicao: Optional[str] = field(
        default=None,
        metadata={
            "name": "dadosMercadoriaCondicao",
            "type": "Element",
            "required": True,
        },
    )
    dados_mercadoria_medida_estatistica_quantidade: Optional[str] = field(
        default=None,
        metadata={
            "name": "dadosMercadoriaMedidaEstatisticaQuantidade",
            "type": "Element",
            "required": True,
        },
    )
    dados_mercadoria_medida_estatistica_unidade: Optional[str] = field(
        default=None,
        metadata={
            "name": "dadosMercadoriaMedidaEstatisticaUnidade",
            "type": "Element",
            "required": True,
        },
    )
    dados_mercadoria_nome_ncm: Optional[str] = field(
        default=None,
        metadata={
            "name": "dadosMercadoriaNomeNcm",
            "type": "Element",
            "required": True,
        },
    )
    dados_mercadoria_peso_liquido: Optional[str] = field(
        default=None,
        metadata={
            "name": "dadosMercadoriaPesoLiquido",
            "type": "Element",
            "required": True,
        },
    )
    dcr_coeficiente_reducao: Optional[str] = field(
        default=None,
        metadata={
            "name": "dcrCoeficienteReducao",
            "type": "Element",
            "required": True,
        },
    )
    dcr_identificacao: Optional[str] = field(
        default=None,
        metadata={
            "name": "dcrIdentificacao",
            "type": "Element",
            "required": True,
        },
    )
    dcr_valor_devido: Optional[str] = field(
        default=None,
        metadata={
            "name": "dcrValorDevido",
            "type": "Element",
            "required": True,
        },
    )
    dcr_valor_dolar: Optional[str] = field(
        default=None,
        metadata={
            "name": "dcrValorDolar",
            "type": "Element",
            "required": True,
        },
    )
    dcr_valor_real: Optional[str] = field(
        default=None,
        metadata={
            "name": "dcrValorReal",
            "type": "Element",
            "required": True,
        },
    )
    dcr_valor_recolher: Optional[str] = field(
        default=None,
        metadata={
            "name": "dcrValorRecolher",
            "type": "Element",
            "required": True,
        },
    )
    deducao: Optional[Deducao] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    fabricante_cidade: Optional[str] = field(
        default=None,
        metadata={
            "name": "fabricanteCidade",
            "type": "Element",
            "required": True,
        },
    )
    fabricante_estado: Optional[str] = field(
        default=None,
        metadata={
            "name": "fabricanteEstado",
            "type": "Element",
            "required": True,
        },
    )
    fabricante_logradouro: Optional[str] = field(
        default=None,
        metadata={
            "name": "fabricanteLogradouro",
            "type": "Element",
            "required": True,
        },
    )
    fabricante_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "fabricanteNome",
            "type": "Element",
            "required": True,
        },
    )
    fabricante_numero: Optional[int] = field(
        default=None,
        metadata={
            "name": "fabricanteNumero",
            "type": "Element",
            "required": True,
        },
    )
    fornecedor_cidade: Optional[str] = field(
        default=None,
        metadata={
            "name": "fornecedorCidade",
            "type": "Element",
            "required": True,
        },
    )
    fornecedor_complemento: Optional[str] = field(
        default=None,
        metadata={
            "name": "fornecedorComplemento",
            "type": "Element",
            "required": True,
        },
    )
    fornecedor_estado: Optional[str] = field(
        default=None,
        metadata={
            "name": "fornecedorEstado",
            "type": "Element",
            "required": True,
        },
    )
    fornecedor_logradouro: Optional[str] = field(
        default=None,
        metadata={
            "name": "fornecedorLogradouro",
            "type": "Element",
            "required": True,
        },
    )
    fornecedor_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "fornecedorNome",
            "type": "Element",
            "required": True,
        },
    )
    fornecedor_numero: Optional[int] = field(
        default=None,
        metadata={
            "name": "fornecedorNumero",
            "type": "Element",
            "required": True,
        },
    )
    frete_moeda_negociada_codigo: Optional[str] = field(
        default=None,
        metadata={
            "name": "freteMoedaNegociadaCodigo",
            "type": "Element",
            "required": True,
        },
    )
    frete_valor_moeda_negociada: Optional[str] = field(
        default=None,
        metadata={
            "name": "freteValorMoedaNegociada",
            "type": "Element",
            "required": True,
        },
    )
    frete_valor_reais: Optional[str] = field(
        default=None,
        metadata={
            "name": "freteValorReais",
            "type": "Element",
            "required": True,
        },
    )
    ii_acordo_tarifario_aladi_codigo: Optional[int] = field(
        default=None,
        metadata={
            "name": "iiAcordoTarifarioAladiCodigo",
            "type": "Element",
        },
    )
    ii_acordo_tarifario_aladi_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "iiAcordoTarifarioAladiNome",
            "type": "Element",
        },
    )
    ii_acordo_tarifario_ato_legal_ano: Optional[int] = field(
        default=None,
        metadata={
            "name": "iiAcordoTarifarioAtoLegalAno",
            "type": "Element",
        },
    )
    ii_acordo_tarifario_ato_legal_codigo: Optional[str] = field(
        default=None,
        metadata={
            "name": "iiAcordoTarifarioAtoLegalCodigo",
            "type": "Element",
        },
    )
    ii_acordo_tarifario_ato_legal_ex: Optional[str] = field(
        default=None,
        metadata={
            "name": "iiAcordoTarifarioAtoLegalEX",
            "type": "Element",
        },
    )
    ii_acordo_tarifario_ato_legal_numero: Optional[str] = field(
        default=None,
        metadata={
            "name": "iiAcordoTarifarioAtoLegalNumero",
            "type": "Element",
        },
    )
    ii_acordo_tarifario_ato_legal_orgao_emissor: Optional[str] = field(
        default=None,
        metadata={
            "name": "iiAcordoTarifarioAtoLegalOrgaoEmissor",
            "type": "Element",
        },
    )
    ii_acordo_tarifario_tipo_codigo: Optional[int] = field(
        default=None,
        metadata={
            "name": "iiAcordoTarifarioTipoCodigo",
            "type": "Element",
            "required": True,
        },
    )
    ii_acordo_tarifario_tipo_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "iiAcordoTarifarioTipoNome",
            "type": "Element",
        },
    )
    ii_aliquota_acordo: Optional[str] = field(
        default=None,
        metadata={
            "name": "iiAliquotaAcordo",
            "type": "Element",
            "required": True,
        },
    )
    ii_aliquota_ad_valorem: Optional[str] = field(
        default=None,
        metadata={
            "name": "iiAliquotaAdValorem",
            "type": "Element",
            "required": True,
        },
    )
    ii_aliquota_percentual_reducao: Optional[str] = field(
        default=None,
        metadata={
            "name": "iiAliquotaPercentualReducao",
            "type": "Element",
            "required": True,
        },
    )
    ii_aliquota_reduzida: Optional[str] = field(
        default=None,
        metadata={
            "name": "iiAliquotaReduzida",
            "type": "Element",
            "required": True,
        },
    )
    ii_aliquota_valor_calculado: Optional[str] = field(
        default=None,
        metadata={
            "name": "iiAliquotaValorCalculado",
            "type": "Element",
            "required": True,
        },
    )
    ii_aliquota_valor_devido: Optional[str] = field(
        default=None,
        metadata={
            "name": "iiAliquotaValorDevido",
            "type": "Element",
            "required": True,
        },
    )
    ii_aliquota_valor_recolher: Optional[str] = field(
        default=None,
        metadata={
            "name": "iiAliquotaValorRecolher",
            "type": "Element",
            "required": True,
        },
    )
    ii_aliquota_valor_reduzido: Optional[str] = field(
        default=None,
        metadata={
            "name": "iiAliquotaValorReduzido",
            "type": "Element",
            "required": True,
        },
    )
    ii_base_calculo: Optional[str] = field(
        default=None,
        metadata={
            "name": "iiBaseCalculo",
            "type": "Element",
            "required": True,
        },
    )
    ii_fundamento_legal_codigo: Optional[str] = field(
        default=None,
        metadata={
            "name": "iiFundamentoLegalCodigo",
            "type": "Element",
            "required": True,
        },
    )
    ii_motivo_admissao_temporaria_codigo: Optional[str] = field(
        default=None,
        metadata={
            "name": "iiMotivoAdmissaoTemporariaCodigo",
            "type": "Element",
            "required": True,
        },
    )
    ii_regime_tributacao_codigo: Optional[int] = field(
        default=None,
        metadata={
            "name": "iiRegimeTributacaoCodigo",
            "type": "Element",
            "required": True,
        },
    )
    ii_regime_tributacao_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "iiRegimeTributacaoNome",
            "type": "Element",
            "required": True,
        },
    )
    ipi_aliquota_ad_valorem: Optional[str] = field(
        default=None,
        metadata={
            "name": "ipiAliquotaAdValorem",
            "type": "Element",
            "required": True,
        },
    )
    ipi_aliquota_especifica_capacidade_recipciente: Optional[str] = field(
        default=None,
        metadata={
            "name": "ipiAliquotaEspecificaCapacidadeRecipciente",
            "type": "Element",
            "required": True,
        },
    )
    ipi_aliquota_especifica_quantidade_unidade_medida: Optional[str] = field(
        default=None,
        metadata={
            "name": "ipiAliquotaEspecificaQuantidadeUnidadeMedida",
            "type": "Element",
            "required": True,
        },
    )
    ipi_aliquota_especifica_tipo_recipiente_codigo: Optional[str] = field(
        default=None,
        metadata={
            "name": "ipiAliquotaEspecificaTipoRecipienteCodigo",
            "type": "Element",
            "required": True,
        },
    )
    ipi_aliquota_especifica_valor_unidade_medida: Optional[str] = field(
        default=None,
        metadata={
            "name": "ipiAliquotaEspecificaValorUnidadeMedida",
            "type": "Element",
            "required": True,
        },
    )
    ipi_aliquota_nota_complementar_tipi: Optional[str] = field(
        default=None,
        metadata={
            "name": "ipiAliquotaNotaComplementarTIPI",
            "type": "Element",
            "required": True,
        },
    )
    ipi_aliquota_reduzida: Optional[str] = field(
        default=None,
        metadata={
            "name": "ipiAliquotaReduzida",
            "type": "Element",
            "required": True,
        },
    )
    ipi_aliquota_valor_devido: Optional[str] = field(
        default=None,
        metadata={
            "name": "ipiAliquotaValorDevido",
            "type": "Element",
            "required": True,
        },
    )
    ipi_aliquota_valor_recolher: Optional[str] = field(
        default=None,
        metadata={
            "name": "ipiAliquotaValorRecolher",
            "type": "Element",
            "required": True,
        },
    )
    ipi_regime_tributacao_codigo: Optional[int] = field(
        default=None,
        metadata={
            "name": "ipiRegimeTributacaoCodigo",
            "type": "Element",
            "required": True,
        },
    )
    ipi_regime_tributacao_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "ipiRegimeTributacaoNome",
            "type": "Element",
            "required": True,
        },
    )
    mercadoria: List[Mercadoria] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )
    numero_adicao: Optional[str] = field(
        default=None,
        metadata={
            "name": "numeroAdicao",
            "type": "Element",
            "required": True,
        },
    )
    numero_di: Optional[int] = field(
        default=None,
        metadata={
            "name": "numeroDI",
            "type": "Element",
            "required": True,
        },
    )
    numero_li: Optional[str] = field(
        default=None,
        metadata={
            "name": "numeroLI",
            "type": "Element",
            "required": True,
        },
    )
    pais_aquisicao_mercadoria_codigo: Optional[int] = field(
        default=None,
        metadata={
            "name": "paisAquisicaoMercadoriaCodigo",
            "type": "Element",
            "required": True,
        },
    )
    pais_aquisicao_mercadoria_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "paisAquisicaoMercadoriaNome",
            "type": "Element",
            "required": True,
        },
    )
    pais_origem_mercadoria_codigo: Optional[int] = field(
        default=None,
        metadata={
            "name": "paisOrigemMercadoriaCodigo",
            "type": "Element",
            "required": True,
        },
    )
    pais_origem_mercadoria_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "paisOrigemMercadoriaNome",
            "type": "Element",
            "required": True,
        },
    )
    pis_cofins_base_calculo_aliquota_icms: Optional[str] = field(
        default=None,
        metadata={
            "name": "pisCofinsBaseCalculoAliquotaICMS",
            "type": "Element",
            "required": True,
        },
    )
    pis_cofins_base_calculo_fundamento_legal_codigo: Optional[str] = field(
        default=None,
        metadata={
            "name": "pisCofinsBaseCalculoFundamentoLegalCodigo",
            "type": "Element",
            "required": True,
        },
    )
    pis_cofins_base_calculo_percentual_reducao: Optional[str] = field(
        default=None,
        metadata={
            "name": "pisCofinsBaseCalculoPercentualReducao",
            "type": "Element",
            "required": True,
        },
    )
    pis_cofins_base_calculo_valor: Optional[str] = field(
        default=None,
        metadata={
            "name": "pisCofinsBaseCalculoValor",
            "type": "Element",
            "required": True,
        },
    )
    pis_cofins_fundamento_legal_reducao_codigo: Optional[str] = field(
        default=None,
        metadata={
            "name": "pisCofinsFundamentoLegalReducaoCodigo",
            "type": "Element",
            "required": True,
        },
    )
    pis_cofins_regime_tributacao_codigo: Optional[int] = field(
        default=None,
        metadata={
            "name": "pisCofinsRegimeTributacaoCodigo",
            "type": "Element",
            "required": True,
        },
    )
    pis_cofins_regime_tributacao_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "pisCofinsRegimeTributacaoNome",
            "type": "Element",
            "required": True,
        },
    )
    pis_pasep_aliquota_ad_valorem: Optional[str] = field(
        default=None,
        metadata={
            "name": "pisPasepAliquotaAdValorem",
            "type": "Element",
            "required": True,
        },
    )
    pis_pasep_aliquota_especifica_quantidade_unidade: Optional[str] = field(
        default=None,
        metadata={
            "name": "pisPasepAliquotaEspecificaQuantidadeUnidade",
            "type": "Element",
            "required": True,
        },
    )
    pis_pasep_aliquota_especifica_valor: Optional[str] = field(
        default=None,
        metadata={
            "name": "pisPasepAliquotaEspecificaValor",
            "type": "Element",
            "required": True,
        },
    )
    pis_pasep_aliquota_reduzida: Optional[str] = field(
        default=None,
        metadata={
            "name": "pisPasepAliquotaReduzida",
            "type": "Element",
            "required": True,
        },
    )
    pis_pasep_aliquota_valor_devido: Optional[str] = field(
        default=None,
        metadata={
            "name": "pisPasepAliquotaValorDevido",
            "type": "Element",
            "required": True,
        },
    )
    pis_pasep_aliquota_valor_recolher: Optional[str] = field(
        default=None,
        metadata={
            "name": "pisPasepAliquotaValorRecolher",
            "type": "Element",
            "required": True,
        },
    )
    relacao_comprador_vendedor: Optional[str] = field(
        default=None,
        metadata={
            "name": "relacaoCompradorVendedor",
            "type": "Element",
            "required": True,
        },
    )
    seguro_moeda_negociada_codigo: Optional[str] = field(
        default=None,
        metadata={
            "name": "seguroMoedaNegociadaCodigo",
            "type": "Element",
            "required": True,
        },
    )
    seguro_valor_moeda_negociada: Optional[str] = field(
        default=None,
        metadata={
            "name": "seguroValorMoedaNegociada",
            "type": "Element",
            "required": True,
        },
    )
    seguro_valor_reais: Optional[str] = field(
        default=None,
        metadata={
            "name": "seguroValorReais",
            "type": "Element",
            "required": True,
        },
    )
    sequencial_retificacao: Optional[str] = field(
        default=None,
        metadata={
            "name": "sequencialRetificacao",
            "type": "Element",
            "required": True,
        },
    )
    valor_multa_arecolher: Optional[str] = field(
        default=None,
        metadata={
            "name": "valorMultaARecolher",
            "type": "Element",
            "required": True,
        },
    )
    valor_multa_arecolher_ajustado: Optional[str] = field(
        default=None,
        metadata={
            "name": "valorMultaARecolherAjustado",
            "type": "Element",
            "required": True,
        },
    )
    valor_reais_frete_internacional: Optional[str] = field(
        default=None,
        metadata={
            "name": "valorReaisFreteInternacional",
            "type": "Element",
            "required": True,
        },
    )
    valor_reais_seguro_internacional: Optional[str] = field(
        default=None,
        metadata={
            "name": "valorReaisSeguroInternacional",
            "type": "Element",
            "required": True,
        },
    )
    valor_total_condicao_venda: Optional[int] = field(
        default=None,
        metadata={
            "name": "valorTotalCondicaoVenda",
            "type": "Element",
            "required": True,
        },
    )
    vinculo_comprador_vendedor: Optional[str] = field(
        default=None,
        metadata={
            "name": "vinculoCompradorVendedor",
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class DeclaracaoImportacao:
    class Meta:
        name = "declaracaoImportacao"

    adicao: List[Adicao] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )
    armazem: Optional[Armazem] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    armazenamento_recinto_aduaneiro_codigo: Optional[int] = field(
        default=None,
        metadata={
            "name": "armazenamentoRecintoAduaneiroCodigo",
            "type": "Element",
            "required": True,
        },
    )
    armazenamento_recinto_aduaneiro_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "armazenamentoRecintoAduaneiroNome",
            "type": "Element",
            "required": True,
        },
    )
    armazenamento_setor: Optional[str] = field(
        default=None,
        metadata={
            "name": "armazenamentoSetor",
            "type": "Element",
            "required": True,
        },
    )
    canal_selecao_parametrizada: Optional[str] = field(
        default=None,
        metadata={
            "name": "canalSelecaoParametrizada",
            "type": "Element",
            "required": True,
        },
    )
    caracterizacao_operacao_codigo_tipo: Optional[int] = field(
        default=None,
        metadata={
            "name": "caracterizacaoOperacaoCodigoTipo",
            "type": "Element",
            "required": True,
        },
    )
    caracterizacao_operacao_descricao_tipo: Optional[str] = field(
        default=None,
        metadata={
            "name": "caracterizacaoOperacaoDescricaoTipo",
            "type": "Element",
            "required": True,
        },
    )
    carga_data_chegada: Optional[int] = field(
        default=None,
        metadata={
            "name": "cargaDataChegada",
            "type": "Element",
            "required": True,
        },
    )
    carga_numero_agente: Optional[str] = field(
        default=None,
        metadata={
            "name": "cargaNumeroAgente",
            "type": "Element",
            "required": True,
        },
    )
    carga_pais_procedencia_codigo: Optional[int] = field(
        default=None,
        metadata={
            "name": "cargaPaisProcedenciaCodigo",
            "type": "Element",
            "required": True,
        },
    )
    carga_pais_procedencia_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "cargaPaisProcedenciaNome",
            "type": "Element",
            "required": True,
        },
    )
    carga_peso_bruto: Optional[str] = field(
        default=None,
        metadata={
            "name": "cargaPesoBruto",
            "type": "Element",
            "required": True,
        },
    )
    carga_peso_liquido: Optional[str] = field(
        default=None,
        metadata={
            "name": "cargaPesoLiquido",
            "type": "Element",
            "required": True,
        },
    )
    carga_urf_entrada_codigo: Optional[str] = field(
        default=None,
        metadata={
            "name": "cargaUrfEntradaCodigo",
            "type": "Element",
            "required": True,
        },
    )
    carga_urf_entrada_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "cargaUrfEntradaNome",
            "type": "Element",
            "required": True,
        },
    )
    conhecimento_carga_embarque_data: Optional[int] = field(
        default=None,
        metadata={
            "name": "conhecimentoCargaEmbarqueData",
            "type": "Element",
            "required": True,
        },
    )
    conhecimento_carga_embarque_local: Optional[str] = field(
        default=None,
        metadata={
            "name": "conhecimentoCargaEmbarqueLocal",
            "type": "Element",
            "required": True,
        },
    )
    conhecimento_carga_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "conhecimentoCargaId",
            "type": "Element",
            "required": True,
        },
    )
    conhecimento_carga_tipo_codigo: Optional[int] = field(
        default=None,
        metadata={
            "name": "conhecimentoCargaTipoCodigo",
            "type": "Element",
            "required": True,
        },
    )
    conhecimento_carga_tipo_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "conhecimentoCargaTipoNome",
            "type": "Element",
            "required": True,
        },
    )
    conhecimento_carga_utilizacao: Optional[int] = field(
        default=None,
        metadata={
            "name": "conhecimentoCargaUtilizacao",
            "type": "Element",
            "required": True,
        },
    )
    conhecimento_carga_utilizacao_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "conhecimentoCargaUtilizacaoNome",
            "type": "Element",
            "required": True,
        },
    )
    data_registro: Optional[int] = field(
        default=None,
        metadata={
            "name": "dataRegistro",
            "type": "Element",
            "required": True,
        },
    )
    declaracao_ee: Optional[DeclaracaoEe] = field(
        default=None,
        metadata={
            "name": "declaracaoEe",
            "type": "Element",
            "required": True,
        },
    )
    documento_chegada_carga_codigo_tipo: Optional[int] = field(
        default=None,
        metadata={
            "name": "documentoChegadaCargaCodigoTipo",
            "type": "Element",
            "required": True,
        },
    )
    documento_chegada_carga_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "documentoChegadaCargaNome",
            "type": "Element",
            "required": True,
        },
    )
    documento_chegada_carga_numero: Optional[str] = field(
        default=None,
        metadata={
            "name": "documentoChegadaCargaNumero",
            "type": "Element",
            "required": True,
        },
    )
    documento_instrucao_despacho: List[DocumentoInstrucaoDespacho] = field(
        default_factory=list,
        metadata={
            "name": "documentoInstrucaoDespacho",
            "type": "Element",
            "min_occurs": 1,
        },
    )
    embalagem: Optional[Embalagem] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        },
    )
    frete_collect: Optional[str] = field(
        default=None,
        metadata={
            "name": "freteCollect",
            "type": "Element",
            "required": True,
        },
    )
    frete_em_territorio_nacional: Optional[str] = field(
        default=None,
        metadata={
            "name": "freteEmTerritorioNacional",
            "type": "Element",
            "required": True,
        },
    )
    frete_moeda_negociada_codigo: Optional[int] = field(
        default=None,
        metadata={
            "name": "freteMoedaNegociadaCodigo",
            "type": "Element",
            "required": True,
        },
    )
    frete_moeda_negociada_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "freteMoedaNegociadaNome",
            "type": "Element",
            "required": True,
        },
    )
    frete_prepaid: Optional[str] = field(
        default=None,
        metadata={
            "name": "fretePrepaid",
            "type": "Element",
            "required": True,
        },
    )
    frete_total_dolares: Optional[str] = field(
        default=None,
        metadata={
            "name": "freteTotalDolares",
            "type": "Element",
            "required": True,
        },
    )
    frete_total_moeda: Optional[int] = field(
        default=None,
        metadata={
            "name": "freteTotalMoeda",
            "type": "Element",
            "required": True,
        },
    )
    frete_total_reais: Optional[str] = field(
        default=None,
        metadata={
            "name": "freteTotalReais",
            "type": "Element",
            "required": True,
        },
    )
    icms: Optional[object] = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    importador_codigo_tipo: Optional[int] = field(
        default=None,
        metadata={
            "name": "importadorCodigoTipo",
            "type": "Element",
            "required": True,
        },
    )
    importador_cpf_representante_legal: Optional[int] = field(
        default=None,
        metadata={
            "name": "importadorCpfRepresentanteLegal",
            "type": "Element",
            "required": True,
        },
    )
    importador_endereco_bairro: Optional[str] = field(
        default=None,
        metadata={
            "name": "importadorEnderecoBairro",
            "type": "Element",
            "required": True,
        },
    )
    importador_endereco_cep: Optional[int] = field(
        default=None,
        metadata={
            "name": "importadorEnderecoCep",
            "type": "Element",
            "required": True,
        },
    )
    importador_endereco_complemento: Optional[str] = field(
        default=None,
        metadata={
            "name": "importadorEnderecoComplemento",
            "type": "Element",
            "required": True,
        },
    )
    importador_endereco_logradouro: Optional[str] = field(
        default=None,
        metadata={
            "name": "importadorEnderecoLogradouro",
            "type": "Element",
            "required": True,
        },
    )
    importador_endereco_municipio: Optional[str] = field(
        default=None,
        metadata={
            "name": "importadorEnderecoMunicipio",
            "type": "Element",
            "required": True,
        },
    )
    importador_endereco_numero: Optional[str] = field(
        default=None,
        metadata={
            "name": "importadorEnderecoNumero",
            "type": "Element",
            "required": True,
        },
    )
    importador_endereco_uf: Optional[str] = field(
        default=None,
        metadata={
            "name": "importadorEnderecoUf",
            "type": "Element",
            "required": True,
        },
    )
    importador_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "importadorNome",
            "type": "Element",
            "required": True,
        },
    )
    importador_nome_representante_legal: Optional[str] = field(
        default=None,
        metadata={
            "name": "importadorNomeRepresentanteLegal",
            "type": "Element",
            "required": True,
        },
    )
    importador_numero: Optional[int] = field(
        default=None,
        metadata={
            "name": "importadorNumero",
            "type": "Element",
            "required": True,
        },
    )
    importador_numero_telefone: Optional[str] = field(
        default=None,
        metadata={
            "name": "importadorNumeroTelefone",
            "type": "Element",
            "required": True,
        },
    )
    informacao_complementar: Optional[str] = field(
        default=None,
        metadata={
            "name": "informacaoComplementar",
            "type": "Element",
            "required": True,
        },
    )
    local_descarga_total_dolares: Optional[str] = field(
        default=None,
        metadata={
            "name": "localDescargaTotalDolares",
            "type": "Element",
            "required": True,
        },
    )
    local_descarga_total_reais: Optional[str] = field(
        default=None,
        metadata={
            "name": "localDescargaTotalReais",
            "type": "Element",
            "required": True,
        },
    )
    local_embarque_total_dolares: Optional[str] = field(
        default=None,
        metadata={
            "name": "localEmbarqueTotalDolares",
            "type": "Element",
            "required": True,
        },
    )
    local_embarque_total_reais: Optional[str] = field(
        default=None,
        metadata={
            "name": "localEmbarqueTotalReais",
            "type": "Element",
            "required": True,
        },
    )
    modalidade_despacho_codigo: Optional[int] = field(
        default=None,
        metadata={
            "name": "modalidadeDespachoCodigo",
            "type": "Element",
            "required": True,
        },
    )
    modalidade_despacho_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "modalidadeDespachoNome",
            "type": "Element",
            "required": True,
        },
    )
    numero_di: Optional[int] = field(
        default=None,
        metadata={
            "name": "numeroDI",
            "type": "Element",
            "required": True,
        },
    )
    operacao_fundap: Optional[str] = field(
        default=None,
        metadata={
            "name": "operacaoFundap",
            "type": "Element",
            "required": True,
        },
    )
    pagamento: List[Pagamento] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )
    seguro_moeda_negociada_codigo: Optional[int] = field(
        default=None,
        metadata={
            "name": "seguroMoedaNegociadaCodigo",
            "type": "Element",
            "required": True,
        },
    )
    seguro_moeda_negociada_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "seguroMoedaNegociadaNome",
            "type": "Element",
            "required": True,
        },
    )
    seguro_total_dolares: Optional[str] = field(
        default=None,
        metadata={
            "name": "seguroTotalDolares",
            "type": "Element",
            "required": True,
        },
    )
    seguro_total_moeda_negociada: Optional[str] = field(
        default=None,
        metadata={
            "name": "seguroTotalMoedaNegociada",
            "type": "Element",
            "required": True,
        },
    )
    seguro_total_reais: Optional[str] = field(
        default=None,
        metadata={
            "name": "seguroTotalReais",
            "type": "Element",
            "required": True,
        },
    )
    sequencial_retificacao: Optional[str] = field(
        default=None,
        metadata={
            "name": "sequencialRetificacao",
            "type": "Element",
            "required": True,
        },
    )
    situacao_entrega_carga: Optional[str] = field(
        default=None,
        metadata={
            "name": "situacaoEntregaCarga",
            "type": "Element",
            "required": True,
        },
    )
    tipo_declaracao_codigo: Optional[str] = field(
        default=None,
        metadata={
            "name": "tipoDeclaracaoCodigo",
            "type": "Element",
            "required": True,
        },
    )
    tipo_declaracao_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "tipoDeclaracaoNome",
            "type": "Element",
            "required": True,
        },
    )
    total_adicoes: Optional[str] = field(
        default=None,
        metadata={
            "name": "totalAdicoes",
            "type": "Element",
            "required": True,
        },
    )
    urf_despacho_codigo: Optional[str] = field(
        default=None,
        metadata={
            "name": "urfDespachoCodigo",
            "type": "Element",
            "required": True,
        },
    )
    urf_despacho_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "urfDespachoNome",
            "type": "Element",
            "required": True,
        },
    )
    valor_total_multa_arecolher_ajustado: Optional[str] = field(
        default=None,
        metadata={
            "name": "valorTotalMultaARecolherAjustado",
            "type": "Element",
            "required": True,
        },
    )
    via_transporte_codigo: Optional[str] = field(
        default=None,
        metadata={
            "name": "viaTransporteCodigo",
            "type": "Element",
            "required": True,
        },
    )
    via_transporte_multimodal: Optional[str] = field(
        default=None,
        metadata={
            "name": "viaTransporteMultimodal",
            "type": "Element",
            "required": True,
        },
    )
    via_transporte_nome: Optional[str] = field(
        default=None,
        metadata={
            "name": "viaTransporteNome",
            "type": "Element",
            "required": True,
        },
    )
    via_transporte_nome_transportador: Optional[str] = field(
        default=None,
        metadata={
            "name": "viaTransporteNomeTransportador",
            "type": "Element",
            "required": True,
        },
    )
    via_transporte_numero_veiculo: Optional[str] = field(
        default=None,
        metadata={
            "name": "viaTransporteNumeroVeiculo",
            "type": "Element",
            "required": True,
        },
    )
    via_transporte_pais_transportador_codigo: Optional[str] = field(
        default=None,
        metadata={
            "name": "viaTransportePaisTransportadorCodigo",
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class ListaDeclaracoes:
    declaracao_importacao: Optional[DeclaracaoImportacao] = field(
        default=None,
        metadata={
            "name": "declaracaoImportacao",
            "type": "Element",
            "required": True,
        },
    )
