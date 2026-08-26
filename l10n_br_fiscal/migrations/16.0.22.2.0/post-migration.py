# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Saneamento das operações-base do l10n_br_fiscal.

Reaplica em bases existentes as correções de registros ``noupdate`` que o
simples ``-u`` não atinge (tax.definition, pareamento de return e a linha de
bonificação): ``operation_data.xml`` e ``l10n_br_fiscal_tax_icms_data.xml``
são carregados com ``noupdate``, então o carregamento do módulo passa por cima
das correções feitas nos arquivos.

Idempotente e defensivo: cada write só ocorre se o registro existir.
"""

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


def _ref(env, xmlid):
    return env.ref("l10n_br_fiscal." + xmlid, raise_if_not_found=False)


def _write_tax_def(env, xmlid, tax_xmlid, cst_xmlid):
    rec = _ref(env, xmlid)
    tax = _ref(env, tax_xmlid)
    cst = _ref(env, cst_xmlid)
    if rec and tax and cst:
        rec.write({"tax_id": tax.id, "cst_id": cst.id})


@openupgrade.migrate()
def migrate(env, version):
    # --- Entrega futura: PIS/COFINS CST 06 -> 49; remover IPI zerado ---
    _write_tax_def(
        env, "tax_pis_definition_entrega_futura", "tax_pis_outros", "cst_pis_49"
    )
    _write_tax_def(
        env,
        "tax_cofins_definition_entrega_futura",
        "tax_cofins_outros",
        "cst_cofins_49",
    )
    # O unlink é obrigatório, não redundante: o cleanup de xml_ids órfãos do
    # Odoo (ir.model.data._process_end) só varre registros com
    # COALESCE(noupdate, false) != True, e o arquivo de dados é noupdate. Sem
    # ele, a definição some do arquivo mas continua viva na base.
    ipi_ef = _ref(env, "tax_ipi_definition_entrega_futura")
    if ipi_ef:
        # A definição precisa estar em rascunho: o unlink do modelo recusa
        # registros aprovados (UserError). Numa base ja em uso o registro
        # costuma estar 'approved', e sem este passo a migracao inteira aborta
        # e o registry nao carrega (issue #4857).
        ipi_ef.action_draft()
        ipi_ef.unlink()  # IPI passa a destacar pelo default (remessa de produção)

    # --- Entrada de reparo: IPI 00->49; PIS/COFINS 99->98 ---
    ipi_rep = _ref(env, "tax_ipi_definition_entrada_reparo")
    cst_ipi_49 = _ref(env, "cst_ipi_49")
    if ipi_rep and cst_ipi_49:
        ipi_rep.write({"cst_id": cst_ipi_49.id})
    _write_tax_def(
        env, "tax_pis_definition_entrada_reparo", "tax_pis_outros", "cst_pis_98"
    )
    _write_tax_def(
        env,
        "tax_cofins_definition_entrada_reparo",
        "tax_cofins_outros",
        "cst_cofins_98",
    )

    # --- Entrada de industrializacao: IPI CST 55 (saida) -> 05 (entrada) ---
    ipi_ind = _ref(env, "tax_ipi_definition_entrada_industrializacao")
    cst_ipi_05 = _ref(env, "cst_ipi_05")
    if ipi_ind and cst_ipi_05:
        ipi_ind.write({"cst_id": cst_ipi_05.id})

    # --- Pareamento de return da industrializacao (core apontava errado) ---
    pairs = [
        ("fo_remessa_industrializacao", "fo_entrada_retorno_industrializacao"),
        ("fo_entrada_industrializacao", "fo_retorno_industrializacao"),
    ]
    for op_xmlid, ret_xmlid in pairs:
        op = _ref(env, op_xmlid)
        ret = _ref(env, ret_xmlid)
        if op and ret:
            op.write({"return_fiscal_operation_id": ret.id})

    # --- Bonificacao: completar a linha (classificacao fiscal) ---
    # Só tax_icms_or_issqn: em l10n_br_fiscal.operation.line esses campos são
    # critério de match (_line_domain), e vazio é curinga. Preencher
    # ind_ie_dest/product_type faria a única linha da operação deixar de casar
    # com bonificação para não contribuinte ou para produto de outro tipo.
    bonif = _ref(env, "fo_bonificacao_bonificacao")
    if bonif and not bonif.tax_icms_or_issqn:
        bonif.write({"tax_icms_or_issqn": "icms"})

    # --- Flags finance_move/stock_move do CFOP (robustez; o CSV atualiza no -u) ---
    cfop_flags = {
        "5922": (True, False),
        "6922": (True, False),
        "1922": (True, False),
        "2922": (True, False),
        "5116": (False, True),
        "6116": (False, True),
        "5117": (False, True),
        "6117": (False, True),
        "1116": (False, True),
        "2116": (False, True),
        "1117": (False, True),
        "2117": (False, True),
        "5919": (False, True),
        "6208": (False, True),
        "6209": (False, True),
    }
    for num, (fin, stk) in cfop_flags.items():
        cfop = _ref(env, "cfop_" + num)
        if cfop:
            cfop.write({"finance_move": fin, "stock_move": stk})

    _logger.info("l10n_br_fiscal: saneamento das operacoes-base aplicado.")
