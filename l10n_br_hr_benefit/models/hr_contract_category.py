# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from openerp.exceptions import ValidationError
from openerp import api, fields, models, _

try:
    from openerp.addons.l10n_br_hr_payroll.constantes import (
        CATEGORIA_TRABALHADOR,
    )
except ImportError:
    CATEGORIA_TRABALHADOR = (
        #
        # Empregado e Trabalhador Temporário
        #
        ('101', u'101 - Empregado – Geral, inclusive o empregado público da administração direta ou indireta contratado pela CLT.'),
        ('102', u'102 - Empregado – Trabalhador Rural por Pequeno Prazo da Lei 11.718/2008'),
        ('103', u'103 - Empregado – Aprendiz'),
        ('104', u'104 - Empregado – Doméstico'),
        ('105', u'105 - Empregado – contrato a termo firmado nos termos da Lei 9601/98'),
        ('106', u'106 - Trabalhador Temporário - contrato nos termos da Lei 6.019/74'),
        # ('107', u'107 - Trabalhador não vinculado ao RGPS com direito ao FGTS'),
        ('111', u'106 - Empregado - contrato de trabalho intermitente'),

        #
        # Avulso
        #
        ('201', u'201 - Trabalhador Avulso – Portuário'),
        ('202', u'202 - Trabalhador Avulso – Não Portuário'),
        # ('203', u'203 - Trabalhador Avulso – Não Portuário '
        #         u'(Informação do Contratante)'),

        #
        # Agente público
        #
        ('301', u'301 - Servidor Público Titular de Cargo Efetivo, Magistrado, Ministro de Tribunal de Contas, Conselheiro de Tribunal de Contas e Membro do Ministério Público'),
        ('302', u'302 - Servidor Público – '
                u'Ocupante de Cargo exclusivo em comissão'),
        ('303', u'303 - Agente Político'),
        # ('304', u'304 - Servidor Público – Agente Público'),
        ('305', u'305 - Servidor Público indicado para conselho ou órgão '
                u'deliberativo, na condição de representante do governo, '
                u'órgão ou entidade da administração pública.'),
        ('306', u'401 - Servidor Público Temporário, sujeito a regime '
                u'administrativo especial definido em lei própria'),
        ('307', u'307 - Militar efetivo'),
        ('308', u'308 - Conscrito'),
        ('309', u'309 - Agente Público - Outros'),


        #
        # Cessão
        #
        ('401', u'401 - Dirigente Sindical – Em relação a Remuneração Recebida no'
                u' Sindicato'),
        ('410', u'410 - Trabalhador cedido - informação prestada pelo Cessionário'),


        #
        # Contribuinte Individua
        #
        ('701', u'701 - Contrib. Individual – Autônomo contratado por Empresas em'
                u' geral'),
        # ('702', u'702 - Contrib. Individual – Autônomo contratado por Contrib. '
        #         u'Individual, por pessoa física em geral, ou por missão '
        #         u'diplomática e repartição consular de carreira estrangeiras'),
        # ('703', u'703 - Contrib. Individual – Autônomo contratado por Entidade '
        #         u'Beneficente de Assistência Social isenta da cota patronal'),
        # ('704', u'704 - Excluído.'),
        ('711', u'711 - Contribuinte individual - Transportador autônomo de passageiros'),
        ('712', u'712 - Contribuinte individual - Transportador autônomo de carga'),
        # ('713', u'713 - Contrib. Individual – Transportador autônomo contratado'
        #         u' por Entidade Beneficente de Assistência Social isenta da cota '
        #         u'patronal'),
        ('721', u'721 - Contribuinte individual - Diretor não empregado, com FGTS'),
        ('722', u'722 - Contribuinte individual - Diretor não empregado, sem FGTS'),
        ('723', u'723 - Contribuinte individual - Empresários, sócios e membro de conselho de administração ou fiscal'),
        ('731', u'731 - Contribuinte individual - Cooperado que presta serviços por intermédio de Cooperativa de Trabalho'),
        # ('732', u'732 - Contrib. Individual – Cooperado que presta serviços a '
        #         u'Entidade Beneficente de Assistência Social isenta da cota '
        #         u'patronal ou para pessoa física'),
        # ('733', u'733 - Contrib. Individual – Cooperado eleito para direção da '
        #         u'Cooperativa'),
        ('734', u'734 - Contribuinte individual - Transportador Cooperado que presta serviços por intermédio de cooperativa de trabalho'),
        # ('735', u'735 - Contrib. Individual – Transportador Cooperado que presta'
        #         u' serviços a Entidade Beneficente de Assistência Social isenta '
        #         u'da cota patronal ou para pessoa física'),
        # ('736', u'736 - Contrib. Individual – Transportador Cooperado eleito '
        #         u'para direção da Cooperativa'),
        ('738', u'738 - Contribuinte individual - Cooperado filiado a Cooperativa de Produção'),
        ('741', u'741 - Contribuinte individual - Microempreendedor Individual'),

        ('751', u'751 - Contribuinte individual - Magistrado classista temporário da Justiça do Trabalho ou da Justiça Eleitoral que seja aposentado de qualquer regime previdenciário'),
        ('761', u'761 - Contribuinte individual - Associado eleito para direção de Cooperativa, '
                u'associação ou entidade de classe de qualquer natureza ou finalidade, bem '
                u'como o síndico ou administrador eleito para exercer atividade de direção '
                u'condominial, desde que recebam remuneração'),
        ('771', u'771 - Contribuinte individual - Membro de conselho tutelar, nos termos da Lei no 8.069, de 13 de julho de 1990'),
        ('781', u'781 - Ministro de confissão religiosa ou membro de vida consagrada, de congregação ou de ordem religiosa'),

        #
        # Bolsista
        #
        ('901', u'901 - Estagiário'),
        ('902', u'902 - Médico Residente'),
        ('903', u'903 - Bolsista, nos termos da lei 8958/1994'),
        ('904', u'904 - Participante de curso de formação, como etapa de concurso público, sem vínculo de emprego/estatutário'),
        ('905', u'905 - Atleta não profissional em formação que receba bolsa'),
    )


class HrContractCategory(models.Model):
    _name = b'hr.contract.category'
    _description = 'Categoria de Contrato'
    _order = 'name'

    name = fields.Selection(
        selection=CATEGORIA_TRABALHADOR,
        string="Categoria do Contrato",
        required=True,
        default='101',
    )

    @api.constrains('name')
    def _check_name(self):
        if self.search([('name', '=', self.name)]) - self:
            raise ValidationError(_(
                'Já existe uma categoria de contrato com o nome escolhido.'
            ))
