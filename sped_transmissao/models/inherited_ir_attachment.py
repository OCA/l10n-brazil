# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from lxml import etree

from openerp import api, fields, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    name = fields.Char(index=True)
    datas_fname = fields.Char(index=True)
    res_name = fields.Char(index=True)
    res_model = fields.Char(index=True)
    res_field = fields.Char(index=True)
    res_id = fields.Integer(index=True)
    public = fields.Boolean(index=True)
    store_fname = fields.Char(index=True)

    @property
    def conteudo_binario(self):
        self.ensure_one()

        binario = self.with_context(bin_size=False).datas
        binario = base64.b64decode(binario)

        return binario

    @property
    def conteudo_texto(self):
        self.ensure_one()

        texto = self.conteudo_binario
        texto = texto.decode('utf-8')

        return texto

    @property
    def conteudo_xml(self):
        self.ensure_one()

        xml = self.conteudo_texto
        root = etree.fromstring(xml.encode('utf-8'))
        xml = '<?xml version="1.0" encoding="utf-8"?>\n' + etree.tounicode(root, pretty_print=True)

        return xml
