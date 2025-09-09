# Copyright 2024 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""
Mixin para limpeza de dados de teste que podem causar violações de constraint.
"""


class TestCleanupMixin:
    """
    Mixin para limpeza de dados de teste que podem causar violações de constraint.
    """

    def setUp(self):
        super().setUp()
        self._cleanup_duplicate_data()

    def _cleanup_duplicate_data(self):
        """
        Limpa dados que podem causar violações de constraint de chave única.
        """
        # Limpar dados PIX duplicados
        self._cleanup_pix_data()

        # Limpar dados de state_tax_numbers duplicados
        self._cleanup_state_tax_numbers_data()

    def _cleanup_pix_data(self):
        """
        Limpa dados PIX que podem causar violação de constraint.
        """
        # Limpar PIX com chaves conhecidas que causam problemas
        problematic_pix_keys = [
            ("phone", "+50372424737"),
            ("phone", "+5511999999999"),
        ]

        for key_type, key in problematic_pix_keys:
            self.env["res.partner.pix"].search(
                [
                    ("key_type", "=", key_type),
                    ("key", "=", key),
                ]
            ).unlink()

    def _cleanup_state_tax_numbers_data(self):
        """
        Limpa dados de state_tax_numbers que podem causar violação de constraint.
        """
        # Limpar state_tax_numbers com combinações conhecidas que causam problemas
        problematic_combinations = [
            (75, 83),  # state_id=75, partner_id=83
        ]

        for state_id, partner_id in problematic_combinations:
            self.env["state.tax.numbers"].search(
                [
                    ("state_id", "=", state_id),
                    ("partner_id", "=", partner_id),
                ]
            ).unlink()

    def cleanup_partner_pix(self, partner_id, key_type, key):
        """
        Limpa PIX específico de um parceiro antes de criar um novo.
        """
        self.env["res.partner.pix"].search(
            [
                ("partner_id", "=", partner_id),
                ("key_type", "=", key_type),
                ("key", "=", key),
            ]
        ).unlink()

    def cleanup_state_tax_number(self, state_id, partner_id):
        """
        Limpa state_tax_number específico antes de criar um novo.
        """
        self.env["state.tax.numbers"].search(
            [
                ("state_id", "=", state_id),
                ("partner_id", "=", partner_id),
            ]
        ).unlink()
