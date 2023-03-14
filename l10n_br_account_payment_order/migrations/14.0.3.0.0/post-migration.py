# Copyright (C) 2023-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def delete_payments_created_from_payment_orders(env):
    # TODO - Apagando os account.move.line, account.move e
    #  account_payment caso CNAB criados pelo modulo
    #  account_payment_order, a avaliação para a integração e uso do
    #  account_payment no caso CNAB é um roadmap do modulo
    #  https://github.com/OCA/l10n-brazil/issues/2272

    openupgrade.logged_query(
        env.cr,
        """
        DELETE FROM account_move_line WHERE move_id in
        (SELECT id FROM account_move WHERE payment_id IN
        (SELECT id FROM account_payment WHERE payment_order_id
         IS NOT NULL AND payment_method_id IN
        (SELECT id FROM account_payment_method WHERE code IN ('240', '400', '500'))));
        """,
    )

    openupgrade.logged_query(
        env.cr,
        """
        DELETE FROM account_move WHERE payment_id IN
        (SELECT id FROM account_payment WHERE payment_order_id
         IS NOT NULL AND payment_method_id IN
        (SELECT id FROM account_payment_method WHERE code IN ('240', '400', '500')));
        """,
    )

    openupgrade.logged_query(
        env.cr,
        """
        DELETE FROM account_payment WHERE payment_order_id IS NOT NULL AND payment_method_id IN
        (SELECT id FROM account_payment_method WHERE code IN ('240', '400', '500'));
        """,
    )


def create_payment_lines_in_cnab_log_events(env):
    """Associa as linhas de Pagamentos aos Logs de Eventos CNAB."""
    env.cr.execute(
        """
        SELECT id FROM l10n_br_cnab_return_event;
        """
    )
    for row in env.cr.fetchall():
        cnab_log_event = env["l10n_br_cnab.return.event"].browse(row[0])
        cnab_log_event.payment_line_ids = cnab_log_event.move_line_id.payment_line_ids


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return
    delete_payments_created_from_payment_orders(env)
    create_payment_lines_in_cnab_log_events(env)
