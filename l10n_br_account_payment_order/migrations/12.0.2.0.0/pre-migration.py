# @ 2020 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openupgradelib import openupgrade

_column_renames = {
    "account.payment.mode": [
        ("instrucoes", "instructions"),
        ("condicao_da_papeleta", "condition_issuing_paper"),
        ("comunicacao_2", "communication_2"),
        ("tipo_servico", "service_type"),
        ("forma_lancamento", "release_form"),
        ("codigo_convenio", "code_convetion"),
        ("codigo_finalidade_doc", "doc_finality_code"),
        ("codigo_finalidade_ted", "ted_finality_code"),
        ("codigo_finalidade_complementar", "complementary_finality_code"),
        ("aviso_ao_favorecido", "favored_warning"),
        ("boleto_carteira", "boleto_wallet"),
        ("boleto_modalidade", "boleto_modality"),
        ("boleto_convenio", "boleto_convetion"),
        ("boleto_variacao", "boleto_variation"),
        ("boleto_aceite", "boleto_accept"),
        ("boleto_especie", "boleto_species"),
        ("boleto_cod_protesto", "boleto_protest_code"),
        ("boleto_dias_protesto", "boleto_days_protest"),
        ("gera_nosso_numero", "generate_own_number"),
        ("boleto_posto", "boleto_post"),
        ("boleto_cod_mora", "boleto_interest_code"),
        ("boleto_perc_mora", "boleto_interest_perc"),
        ("boleto_cod_multa", "boleto_fee_code"),
        ("boleto_perc_multa", "boleto_fee_perc"),
        ("tax_account_id", "product_tax_account_id"),
    ],
    "account.payment.line": [
        ("linha_digitavel", "digitable_line"),
        ("nosso_numero", "own_number"),
        ("numero_documento", "document_number"),
        ("identificacao_titulo_empresa", "company_title_identification"),
        ("codigo_finalidade_doc", "doc_finality_code"),
        ("codigo_finalidade_ted", "ted_finality_code"),
        ("codigo_finalidade_complementar", "complementary_finality_code"),
        ("aviso_ao_favorecido", "favored_warning"),
        ("abatimento", "rebate_value"),
        ("desconto", "discount_value"),
        ("mora", "interest_value"),
        ("multa", "fee_value"),
    ],
    "account.payment.order": [
        ("tipo_servico", "service_type"),
        ("forma_lancamento", "release_form"),
        ("codigo_convenio", "code_convetion"),
        ("indicativo_forma_pagamento", "indicative_form_payment"),
        ("tipo_movimento", "movement_type"),
        ("codigo_instrucao_movimento", "movement_instruction_code"),
    ],
    "bank.payment.line": [
        ("codigo_finalidade_doc", "doc_finality_code"),
        ("codigo_finalidade_ted", "ted_finality_code"),
        ("codigo_finalidade_complementar", "complementary_finality_code"),
        ("aviso_ao_favorecido", "favored_warning"),
        ("abatimento", "rebate_value"),
        ("desconto", "discount_value"),
        ("mora", "interest_value"),
        ("multa", "fee_value"),
        ("evento_id", "event_id"),
        ("nosso_numero", "own_number"),
        ("numero_documento", "document_number"),
        ("identificacao_titulo_empresa", "company_title_identification"),
        ("is_erro_exportacao", "is_export_error"),
        ("mensagem_erro_exportacao", "export_error_message"),
        ("ultimo_estado_cnab", "last_cnab_state"),
    ],
    "l10n_br.cnab.evento": [
        ("data_real_pagamento", "real_payment_date"),
        ("data_ocorrencia", "occurrence_date"),
        ("data_vencimento", "due_date"),
        ("favorecido_conta_bancaria_id", "favored_bank_account_id"),
        ("favorecido_id", "favored_id"),
        ("identificacao_titulo_empresa", "company_title_identification"),
        ("juros_mora_multa", "interest_fee_value"),
        ("nosso_numero", "own_number"),
        ("ocorrencias", "occurrences"),
        ("outros_creditos", "other_credits"),
        ("segmento", "segment"),
        ("numero_documento", "document_number"),
        ("seu_numero", "your_number"),
        ("tipo_moeda", "currency_type"),
        ("tarifa_cobranca", "tariff_charge"),
        ("valor", "title_value"),
        ("valor_abatimento", "rebate_value"),
        ("valor_desconto", "discount_value"),
        ("valor_iof", "iof_value"),
        ("valor_pagamento", "payment_value"),
        ("lote_id", "lot_id"),
    ],
    "l10n_br.cnab.lote": [
        ("empresa_inscricao_numero", "company_registration_number"),
        ("empresa_inscricao_tipo", "company_registration_type"),
        ("mensagem", "message"),
        ("qtd_registros", "register_qty"),
        ("servico_operacao", "operation_service"),
        ("tipo_servico", "service_type"),
        ("total_valores", "total_value"),
    ],
    # TODO - Separação dos dados de importação para um objeto especifico
    #  l10n_br_cnab.return.log armazenando o LOG do Arquivo de Retorno CNAB
    #  de forma separada e permitindo a integração com a alteração feita no
    #  modulo do BRCobranca onde se esta utilizando o modulo
    #  account_base_move_import para fazer essa tarefa de wizard de importação,
    #  o objeto l10n_br_cnab esta comentado para permitir, caso seja necessário,
    #  a implementação de outra forma de importação pois tem os metodos que eram
    #  usados pela KMEE e o historico git do arquivo
    "l10n_br.cnab": [
        ("arquivo_retorno", "return_file"),
        ("data", "cnab_date"),
        ("data_arquivo", "date_file"),
        ("sequencial_arquivo", "sequential_file"),
        ("motivo_erro", "reason_error"),
        ("lote_id", "lot_id"),
        ("num_eventos", "number_events"),
        ("num_lotes", "number_lots"),
    ],
    "account.move.line": [
        ("state_cnab", "cnab_state"),
        ("nosso_numero", "own_number"),
        ("numero_documento", "document_number"),
        ("identificacao_titulo_empresa", "company_title_identification"),
        ("situacao_pagamento", "payment_situation"),
        ("instrucoes", "instructions"),
    ],
    "account.invoice": [
        ("instrucoes", "instructions"),
        ("eval_payment_mode_instrucoes", "eval_payment_mode_instructions"),
    ],
}
# TODO - verificar na migração da 8/10 para 12, em uma base de dados nova não
#  existe os campos e objetos o que causa erro
_column_renames = {}


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    openupgrade.rename_columns(env.cr, _column_renames)
