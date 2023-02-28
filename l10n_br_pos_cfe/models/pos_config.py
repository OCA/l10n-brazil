# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = "pos.config"

    def _demo_configure_pos_config_sat_tanca(self):
        for record in self:
            record.write(
                {
                    "cnpj_homologation": "08.723.218/0001-86",
                    "ie_homologation": "149.626.224.113",
                    "cnpj_software_house": "16.716.114/0001-72",
                    "sat_path": "/opt/sat/libsat_v3_0_0_3_x64.so",
                    "cashier_number": "1",
                    "activation_code": "12345678",
                    "signature_sat": "SGR-SAT SISTEMA DE GESTAO E RETAGUARDA DO SAT",
                }
            )
            record.company_id.environment_sat = "homologation"

    def _demo_configure_pos_config_sat_sweda(self):
        for record in self:
            record.write(
                {
                    "cnpj_homologation": "53.485.215/0001-06",
                    "ie_homologation": "111.072.115.110",
                    "cnpj_software_house": "10.615.281/0001-40",
                    "sat_path": "/opt/sat/sweda/libSATDLL_Dual_armv7.so",
                    "cashier_number": "1",
                    "activation_code": "12345678",
                    "signature_sat": "SGR-SAT SISTEMA DE GESTAO E RETAGUARDA DO SAT",
                }
            )
            record.company_id.environment_sat = "homologation"
