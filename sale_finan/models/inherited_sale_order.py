# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ultrapassa_limite_credito = fields.Boolean(
        string='Venda ultrapassa o limite de crédito?',
        compute='_compute_ultrapassa_limite_credito',
    )

    @api.depends('vr_nf')
    def _compute_ultrapassa_limite_credito(self):
        for sale in self:
            if sale.participante_id.limite_credito:
                sale.ultrapassa_limite_credito = sale.vr_nf > \
                    sale.participante_id.limite_credito_disponivel
            else:
                sale.ultrapassa_limite_credito = False

    carteira_id = fields.Many2one(
        string='Carteira',
        comodel_name='finan.carteira',
        # domain=lambda self: self.domain_carteira_id,
        compute='compute_carteira_id',
        inverse='inverse_carteira_id',
        help='Essa é a carteira padrão configurada na aba comercial do '
             'cadastro da empresa.',
        store=True,
    )

    permissao = fields.Boolean(
        string='permissao para alterar a carteira?',
        compute="compute_permissao",
        default=False,
    )

    @api.multi
    @api.depends('condicao_pagamento_id')
    def compute_permissao(self):
        """
        Permissao é um boolean que indica se o usuario tem ou nao permissao 
        para editar o campo e se podera visualizar esse campo (readonly)
        O usuario tem permissao quando:
         1. Pertencer ao grupo de gerente do financeiro
         2. E Se a forma de pagamento for boleto
        """
        for record in self:
            forma_pgto_id = record.condicao_pagamento_id.forma_pagamento_id
            boleto = forma_pgto_id.forma_pagamento == '15'
            if record.condicao_pagamento_id and \
                    boleto and \
                    record.user_id.has_group('finan.GRUPO_CADASTRO_GERENTE'):
                record.permissao = True
            else:
                record.permissao = False

    @api.multi
    @api.depends('condicao_pagamento_id')
    def compute_carteira_id(self):
        for record in self:
            forma_pgto_id = record.condicao_pagamento_id.forma_pagamento_id
            boleto = forma_pgto_id.forma_pagamento == '15'
            # Se existir uma forma de pagamento e essa forma for Boleto
            if record.condicao_pagamento_id and boleto:
                # setar a carteira padrão da empresa na venda
                if record.env.user.company_id.sped_empresa_id.carteira_id:
                    record.carteira_id = \
                        record.env.user.company_id.sped_empresa_id.carteira_id
                # Emitir aviso que nenhuma carteira foi configurada
                # else:
                #     raise UserError(
                #         "Nenhuma carteira padrão foi configurada no "
                #         "cadastro da empresa.\n Para emitir boleto juntamento "
                #         "com a nota fiscal, configurar a carteira padrão na "
                #         "aba \"Comercial\" do cadastro da empresa.")

    # @api.multi
    # def domain_carteira_id(self):
    #     ids = []
    #     for carteira in self.env.user.sped_empresa_id.carteira_ids:
    #         ids.append(carteira.id)
    #     ids.append(self.participante_id.sped_empresa_id.carteira_id.id)
    #     return [('id', 'in', ids)]

    def inverse_carteira_id(self):
        """
        Definido a função inverse apenas para ser possível editar o campo calcu
        """
        for record in self:
            pass

    def prepara_dados_documento(self):
        """
        Adicionar informação da carteira ne preparação dos dados para criação
         do sped.documento. 
        """
        self.ensure_one()
        res = super(SaleOrder, self).prepara_dados_documento()
        res.update({'carteira_id': self.carteira_id.id})
        return res
