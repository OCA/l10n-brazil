# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Cria campos pais_nac_id e pais_nascto_id para substituir o place_of_birth (que é texto)
    pais_nascto_id = fields.Many2one(
        string='País de Nascimento',
        comodel_name='sped.pais',
    )
    pais_nac_id = fields.Many2one(
        string='Nacionalidade',
        comodel_name='sped.pais',
    )

    # Dados que faltam em l10n_br_hr
    cnh_dt_exped = fields.Date(
        string='Data de Emissão',
    )
    cnh_uf = fields.Many2one(
        string='UF',
        comodel_name='res.country.state',
    )
    cnh_dt_pri_hab = fields.Date(
        string='Data da 1ª Hab.',
    )

    #  Guardar toedas as alteracoes
    sped_s2205_registro_ids = fields.Many2many(
        string='Registro S-2205 de Alterações Cadastrais',
        comodel_name='sped.transmissao',
        # column1='employee_id',
        # column2='sped_transmissao_id',
    )

    # Computar a situação da transmissao da ultima alteracao
    sped_s2205_situacao = fields.Selection(
        string='Situação',
        compute='_compute_sped_s2205_situacao',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
            ('6', 'Ainda não cadastrado no e-social'),
        ],
    )

    @api.multi
    @api.depends('sped_s2205_registro_ids')
    def _compute_sped_s2205_situacao(self):
        """
        Determinar a situacao do gerador de registro 2205
        """
        for record in self:

            if record.sped_s2205_registro_ids:

                # ultima_transmissao_id = record.sped_s2205_registro_ids.
                # sorted(key=lambda r: r.data_hora_origem)[0]

                ultima_transmissao_id = record.sped_s2205_registro_ids[0]

                # Caso a ultima alteracao do registro for maior que o ultimo
                # envio do esocial Precisa de retificacao do registro
                if ultima_transmissao_id.data_hora_origem != record.write_date:
                    record.sped_s2205_situacao = '5'
                    return

                # Caso a data seja igual mas o registro nao foi retornado pelo
                # esocial com sucesso ainda, fica pendente
                if ultima_transmissao_id.situacao == '4':
                    record.sped_s2205_situacao = '4'
                    return

                # Caso contrario assume a situacao do ultimo envio
                record.sped_s2205_situacao = ultima_transmissao_id.situacao

            elif record.contract_id.sped_s2200_registro:

                # Se a data da alteracao do registro for maior que a data de
                # envio do registro do contrato, sinalizo falta de retificacao
                if record.contract_id.sped_S2200_data_hora < record.write_date:
                    record.sped_s2205_situacao = '5'

                # se ja foi transmitido o registro S2200 do contrato,
                # marco que esta transmitido e nao foi feito alteração ainda
                # se a data de edicao do registro for igua do contrato,
                #  sinaliza apenas commo transmitida
                else:
                    record.sped_s2205_situacao = \
                        record.contract_id.sped_S2200_situacao

            # Se nao informo que nem o contrato foi transmitido ainda
            else:
                record.sped_s2205_situacao = '6'

    @api.multi
    def criar_s2205(self):
        """
        Criar registro do esocial S2205
        """
        self.ensure_one()
        values = {
            'tipo': 'esocial',
            'registro': 'S-2205',
            'ambiente': self.company_id.esocial_tpAmb or self.company_id.matriz.esocial_tpAmb,
            'company_id': self.company_id.id,
            'evento': 'evtAltCadastral',
            'origem': ('hr.employee,%s' % self.id),
        }

        sped_s2205_registro_id = self.env['sped.transmissao'].create(values)

        self.write({
            'sped_s2205_registro_ids': [(4, sped_s2205_registro_id.id)]
        })
