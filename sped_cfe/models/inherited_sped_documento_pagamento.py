# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#   Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging
from odoo import api, models, fields, _
from odoo.addons.l10n_br_base.constante_tributaria import (
    MODELO_FISCAL_CFE,
    FORMA_PAGAMENTO_CARTOES,
)

_logger = logging.getLogger(__name__)

FORMA_PAGAMENTO = (
    ('01', 'Dinheiro'),
    ('02', 'Cheque'),
    ('03', 'Cartão de crédito'),
    ('04', 'Cartão de débito'),
    ('05', 'Crédito na loja'),
    ('10', 'Vale alimentação'),
    ('11', 'Vale refeição'),
    ('12', 'Vale presente'),
    ('13', 'Vale combustível'),
    ('14', 'Duplicata mercantil'),
    ('15', 'Boleto bancário'),
    # ('90', 'Sem pagamento'),
    ('99', 'Outros'),
)

try:
    from pybrasil.valor.decimal import Decimal as D
    from satcfe.entidades import MeioPagamento

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedDocumentoPagamento(models.Model):
    _inherit = 'sped.documento.pagamento'

    id_pagamento = fields.Char(
        string=u'Id Pagamento'
    )
    nsu = fields.Integer(
        string=u'NSU',
    )
    numero_aprovacao = fields.Integer(
        string=u'Nº aprovação',
    )

    serial_pos = fields.Char(
        string=u'Serial POS'
    )

    estabecimento = fields.Integer(
        string=u'Estabelecimento',
    )

    forma_pagamento = fields.Selection(
        selection=FORMA_PAGAMENTO,
        related='condicao_pagamento_id.forma_pagamento',
        string='Condição de Pagamento'
    )

    id_fila = fields.Char(
        string=u'Id Fila'
    )
    pagamento_valido = fields.Boolean(
        string=u'Pagamento Válido'
    )

    def monta_cfe(self):
        self.ensure_one()

        kwargs = {}

        if self.documento_id.modelo != MODELO_FISCAL_CFE:
            return

        if self.forma_pagamento in FORMA_PAGAMENTO_CARTOES:
            # pag.card.CNPJ.valor = limpa_formatacao(self.cnpj_cpf or '')
            # pag.card.tBand.valor = self.bandeira_cartao

            # Lembrete integracao_cartao esta com valores errados
            # das constantes
            # kwargs['cAdmC'] = '00' + self.integracao_cartao
            kwargs['cAdmC'] = self.condicao_pagamento_id.participante_id. \
                codigo_administradora_cartao

        pagamento = MeioPagamento(
            cMP=self.forma_pagamento,
            vMP=D(self.valor).quantize(D('0.01')),
            **kwargs
        )
        pagamento.validar()

        return pagamento

    def envia_pagamento(self):
        self.ensure_one()
        if self.forma_pagamento not in FORMA_PAGAMENTO_CARTOES:
            self.pagamento_valido = True
            return
        else:
            config = self.documento_id.configuracoes_pdv
            cliente = self.documento_id.processador_vfpe()

            if config.tipo_sat == 'local':
                resposta = cliente.enviar_pagamento(
                    config.chave_requisicao, self.estabecimento,
                    self.serial_pos, config.cnpjsh,
                    self.documento_id.bc_icms_proprio,
                    self.valor,
                    config.multiplos_pag,
                    config.anti_fraude,
                    'BRL',
                    int(config.numero_caixa),
                )
            elif config.tipo_sat == 'rede_interna':
                resposta = cliente.enviar_pagamento(
                    config.chave_requisicao,
                    self.estabecimento,
                    self.serial_pos,
                    config.cnpjsh,
                    self.documento_id.bc_icms_proprio,
                    self.valor,
                    config.multiplos_pag,
                    config.anti_fraude,
                    'BRL',
                    int(config.numero_caixa),
                    config.chave_acesso_validador,
                    config.path_integrador
                )
            resposta_pagamento = resposta.split('|')
            if len(resposta_pagamento[0]) >= 7:
                self.id_pagamento = resposta_pagamento[0]
                self.id_fila = resposta_pagamento[1]

                # Retorno do status do pagamento só é necessário em uma venda
                # efetuada por TEF.

                if config.tipo_sat == 'local':
                    cliente.enviar_status_pagamento(
                        config.cnpjsh, self.id_fila
                    )
                elif config.tipo_sat == 'rede_interna':
                    cliente.enviar_status_pagamento(
                        config.cnpjsh, self.id_fila,
                        int(config.numero_caixa),
                        config.chave_acesso_validador,
                        config.path_integrador
                    )

                self.pagamento_valido = True

    @api.multi
    def efetuar_pagamento(self):
        """Check the order:
        if the order is not paid: continue payment,
        if the order is paid print ticket.
        """
        self.ensure_one()
        documento = self.env['sped.documento'].browse(
            self.env.context.get('active_id', False))
        if not self.pagamento_valido:
            self.envia_pagamento()
        if documento.vr_total_residual <= 0:
            return {'type': 'ir.actions.act_window_close'}
        # data = self.read()[0]

        # if amount < 0:
        #     raise UserWarning(
        #         'Valor do pagamento deve ser maior que zero'
        #     )
        return self.launch_payment()

    def launch_payment(self):
        context = self.env.context.copy()
        if context.get('default_valor'):
            context['default_valor'] -= self.valor
        return {
            'name': _('Payment'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sped.documento.pagamento',
            'view_id': self.env.ref('sped_cfe.view_enviar_pagamento').id,
            'target': 'new',
            'views': False,
            'type': 'ir.actions.act_window',
            'context': context,
        }
