# Copyright 2023 KMEE - Breno Oliveira Dias
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import xml.etree.ElementTree as ET

from erpbrasil.base.misc import punctuation_rm

from odoo import _, api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


# pylint: disable=consider-merging-classes-inherited
class SefazWebservice(models.AbstractModel):
    _inherit = "l10n_br_cnpj_search.webservice.abstract"

    @api.model
    def sefaz_validate(self, response):
        if not response.ok:
            raise ValidationError(_(response.reason))
        return response

    @api.model
    def _sefaz_import_data(self, data):
        tree = ET.ElementTree(ET.fromstring(data.text))
        IE = ""
        for el in tree.findall(".//"):
            if "IE" in el.tag:
                IE = el.text
        res = {
            "inscr_est": IE,
        }
        return res

    def sefaz_search(self, uf, cnpj, processador):
        response = processador.consultar_cadastro(uf, int(punctuation_rm(cnpj)))
        return response.retorno
