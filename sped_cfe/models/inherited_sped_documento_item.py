# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#   Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import models
from odoo.addons.l10n_br_base.constante_tributaria import *

_logger = logging.getLogger(__name__)

try:
    from satcfe.entidades import *
    from pybrasil.valor.decimal import Decimal as D
    from pybrasil.template import TemplateBrasil

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedDocumentoItem(models.Model):
    _inherit = 'sped.documento.item'

    def monta_cfe(self):
        """
        FIXME: Impostos
        :return:
        """
        self.ensure_one()

        kwargs = {}

        if self.documento_id.modelo != MODELO_FISCAL_CFE:
            return

        if self.produto_descricao:
            descricao = self.produto_descricao
        else:
            descricao = self.produto_id.nome

        descricao = descricao.replace('—', '-').replace('–', '-')
        descricao = descricao.replace('”', '"').replace('“', '"')
        descricao = descricao.replace('’', u"'").replace('‘', u"'")
        descricao = descricao.replace('—', '-').replace('–', '-')

        if self.produto_id.ncm_id:
            ncm = self.produto_id.ncm_id.codigo
            ncm_extipi = self.produto_id.ncm_id.ex
        else:
            ncm = ''

        imposto = Imposto(
            vItem12741=D(self.vr_ibpt).quantize(D('0.01')),
            icms=ICMSSN102(
                Orig=self.org_icms,
                CSOSN='500'),
            pis=PISSN(CST='49'),
            cofins=COFINSSN(CST='49')
        )
        imposto.validar()

        detalhe = Detalhamento(
            produto=ProdutoServico(
                cProd=self.produto_id.codigo or str(self.produto_id.id),
                xProd=descricao.strip(),
                CFOP=self.cfop_id.codigo,
                uCom=self.unidade_id.codigo,
                qCom=D(self.quantidade).quantize(D('0.0001')),
                vUnCom=D(self.vr_unitario).quantize(D(10 * 10 ** -3)),
                indRegra='A',
                NCM=ncm,
                **kwargs
            ),
            imposto=imposto
        )
        detalhe.validar()

        return detalhe
