# Copyright 2024 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""
Hooks para limpeza de dados duplicados durante a instalação.
"""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """Limpa dados duplicados que podem causar violações de constraint."""
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Limpar dados PIX duplicados
    _cleanup_duplicate_pix_data(env)

    # Limpar dados state_tax_numbers duplicados
    _cleanup_duplicate_state_tax_numbers(env)


def _cleanup_duplicate_pix_data(env):
    """Limpa dados PIX duplicados que podem causar violação de constraint."""
    _logger.info("Limpeza de dados PIX duplicados...")

    # Buscar registros PIX duplicados
    env.cr.execute(
        """
        SELECT key_type, key, partner_id, COUNT(*) as count
        FROM res_partner_pix
        GROUP BY key_type, key, partner_id
        HAVING COUNT(*) > 1
    """
    )

    duplicates = env.cr.fetchall()

    for key_type, key, partner_id, count in duplicates:
        _logger.warning(
            f"Encontrados {count} registros PIX duplicados para "
            f"partner_id={partner_id}, key_type={key_type}, key={key}"
        )

        # Manter apenas o primeiro registro, remover os demais
        env.cr.execute(
            """
            DELETE FROM res_partner_pix
            WHERE key_type = %s AND key = %s AND partner_id = %s
            AND id NOT IN (
                SELECT id FROM res_partner_pix
                WHERE key_type = %s AND key = %s AND partner_id = %s
                ORDER BY id
                LIMIT 1
            )
        """,
            (key_type, key, partner_id, key_type, key, partner_id),
        )


def _cleanup_duplicate_state_tax_numbers(env):
    """Limpa dados state_tax_numbers duplicados que podem causar violação
    de constraint."""
    _logger.info("Limpeza de dados state_tax_numbers duplicados...")

    # Buscar registros state_tax_numbers duplicados
    env.cr.execute(
        """
        SELECT state_id, partner_id, COUNT(*) as count
        FROM state_tax_numbers
        GROUP BY state_id, partner_id
        HAVING COUNT(*) > 1
    """
    )

    duplicates = env.cr.fetchall()

    for state_id, partner_id, count in duplicates:
        _logger.warning(
            f"Encontrados {count} registros state_tax_numbers duplicados "
            f"para partner_id={partner_id}, state_id={state_id}"
        )

        # Manter apenas o primeiro registro, remover os demais
        env.cr.execute(
            """
            DELETE FROM state_tax_numbers
            WHERE state_id = %s AND partner_id = %s
            AND id NOT IN (
                SELECT id FROM state_tax_numbers
                WHERE state_id = %s AND partner_id = %s
                ORDER BY id
                LIMIT 1
            )
        """,
            (state_id, partner_id, state_id, partner_id),
        )
