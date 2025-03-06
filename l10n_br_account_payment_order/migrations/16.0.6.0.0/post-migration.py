# Copyright (C) 2025-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def update_cnab_config_protest_code(env):
    """
    Atualiza o Código de Protesto de CHAR para Objeto/l10n_br_cnab.code
    """

    env.cr.execute(
        """
        SELECT id, boleto_protest_code FROM l10n_br_cnab_config WHERE
        boleto_protest_code IS NOT NULL;
        """
    )
    for row in env.cr.fetchall():
        cnab_config = env["l10n_br_cnab.config"].browse(row[0])
        if row[1]:
            protest_obj = env["l10n_br_cnab.code"].search(
                [
                    ("bank_ids", "in", cnab_config.bank_id.ids),
                    ("payment_method_ids", "in", cnab_config.payment_method_id.ids),
                    ("code_type", "=", "protest_code"),
                    ("code", "=", row[1]),
                ]
            )
            if protest_obj:
                cnab_config.boleto_protest_code_id = protest_obj
            else:
                code_not_found = env["l10n_br_cnab.code"].create(
                    {
                        "code": row[1],
                        "name": "CÓDIGO NÃO IDENTIFICADO, considere verificar esse"
                        " problema, ver detalhes no Comentário do Código",
                        "bank_ids": cnab_config.bank_id.ids,
                        "payment_method_ids": cnab_config.payment_method_id.ids,
                        "code_type": "protest_code",
                        "comment": "Código Não Identificado, durante a atualização"
                        "do campo de CHAR para o objeto l10n_br_cnab.code o "
                        "conjunto de Códigos CNAB do Banco não existiam dentro do "
                        " repositorio público https://github.com/OCA/l10n-brazil/"
                        "tree/16.0/l10n_br_account_payment_order/data/cnab_codes "
                        "por isso esse Código não foi incluído, para resolver esse "
                        "problema você pode alterar o campo Nome para a descrição "
                        "informada na Documentação desse CNAB específico e, se "
                        "existirem, veja de criar as outras possibilidades de "
                        "Código para que o Usuário/Empresa possam avaliar se esse "
                        "Código está de acordo com o esperado. IMPORTANTE: por "
                        "favor considere fazer um PR incluindo esse Código CNAB no "
                        "projeto, se tiver erros veja de criar um ISSUE ou se "
                        "precisar fazer alguma correção criar um PR corrigindo o "
                        "problema, assim como você e a sua Empresa foram "
                        "beneficiados e ajudados por esse trabalho o Projeto, como "
                        "qualquer Projeto de Código Aberto, também espera que você,"
                        " de acordo com as suas condições, busque contribuir com o "
                        "Projeto para beneficiar e ajudar os outros, contribuindo "
                        "para criar um circulo virtuoso de ajuda mutua que "
                        "beneficia a todos os envolvidos.",
                    }
                )
                cnab_config.boleto_protest_code_id = code_not_found


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return
    update_cnab_config_protest_code(env)
