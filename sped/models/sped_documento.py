# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from ..constante_tributaria import *
from pybrasil.data import parse_datetime, data_hora_horario_brasilia


class Documento(models.Model):
    _description = 'Documento Fiscal'
    _name = 'sped.documento'
    _order = 'emissao, modelo, data_emissao desc, serie, numero'
    _rec_name = 'numero'

    empresa_id = fields.Many2one('sped.empresa', 'Empresa', ondelete='restrict', default=lambda self: self.env['sped.empresa']._empresa_ativa('sped.documento'))
    empresa_cnpj_cpf = fields.Char('CNPJ/CPF', size=18, related='empresa_id.cnpj_cpf', readonly=True)
    #company_id = fields.Many2one('res.company', 'Empresa', ondelete='restrict', store=True, related='empresa_id.original_company_id')
    #company_id = fields.Many2one('res.company', 'Empresa', ondelete='restrict', default=lambda self: self.env['res.company']._company_default_get('sped.documento'))
    emissao = fields.Selection(TIPO_EMISSAO, 'Tipo de emissão', index=True)
    modelo = fields.Selection(MODELO_FISCAL, 'Modelo', index=True)

    data_hora_emissao = fields.Datetime('Data de emissão', index=True, default=fields.Datetime.now)
    data_hora_entrada_saida = fields.Datetime('Data de entrada/saída', index=True, default=fields.Datetime.now)

    @api.one
    @api.depends('data_hora_emissao', 'data_hora_entrada_saida')
    def _data_hora_separadas(self):
        data_hora_emissao = data_hora_horario_brasilia(parse_datetime(self.data_hora_emissao))
        self.data_emissao = str(data_hora_emissao)[:10]
        self.hora_emissao = str(data_hora_emissao)[11:19]

        data_hora_entrada_saida = data_hora_horario_brasilia(parse_datetime(self.data_hora_entrada_saida))
        self.data_entrada_saida = str(data_hora_entrada_saida)[:10]
        self.hora_entrada_saida = str(data_hora_entrada_saida)[11:19]

    data_emissao = fields.Date('Data de emissão', compute=_data_hora_separadas, store=True, index=True)
    hora_emissao = fields.Char('Hora de emissão', size=8, compute=_data_hora_separadas, store=True)
    data_entrada_saida = fields.Date('Data de entrada/saída', compute=_data_hora_separadas, store=True, index=True)
    hora_entrada_saida = fields.Char('Hora de entrada/saída', size=8, compute=_data_hora_separadas, store=True)

    serie = fields.Char('Série', index=True)
    numero = fields.Numero('Número', index=True)
    entrada_saida = fields.Selection(ENTRADA_SAIDA, 'Entrada/Saída', index=True, default=ENTRADA_SAIDA_SAIDA)
    situacao_fiscal = fields.Selection(SITUACAO_FISCAL, 'Situação fiscal', index=True, default=SITUACAO_FISCAL_REGULAR)

    ambiente_nfe =  fields.Selection(AMBIENTE_NFE, 'Ambiente da NF-e', index=True, default=AMBIENTE_NFE_HOMOLOGACAO)
    tipo_emissao_nfe = fields.Selection(TIPO_EMISSAO_NFE, 'Tipo de emissão da NF-e', default=TIPO_EMISSAO_NFE_NORMAL)
    ie_st = fields.Char('IE do substituto tributário', size=14)
    municipio_fato_gerador_id = fields.Many2one('sped.municipio', 'Município do fato gerador')

    operacao_id = fields.Many2one('sped.operacao', 'Operação', ondelete='restrict')
    #
    # Campos da operação
    #
    regime_tributario = fields.Selection(REGIME_TRIBUTARIO, 'Regime tributário', default=REGIME_TRIBUTARIO_SIMPLES)
    forma_pagamento = fields.Selection(FORMA_PAGAMENTO, 'Forma de pagamento', default=FORMA_PAGAMENTO_A_VISTA)
    finalidade_nfe = fields.Selection(FINALIDADE_NFE, 'Finalidade da NF-e', default=FINALIDADE_NFE_NORMAL)
    consumidor_final = fields.Selection(TIPO_CONSUMIDOR_FINAL, 'Tipo do consumidor', default=TIPO_CONSUMIDOR_FINAL_NORMAL)
    presenca_comprador = fields.Selection(INDICADOR_PRESENCA_COMPRADOR, 'Presença do comprador', default=INDICADOR_PRESENCA_COMPRADOR_NAO_SE_APLICA)
    modalidade_frete = fields.Selection(MODALIDADE_FRETE, 'Modalidade do frete', default=MODALIDADE_FRETE_DESTINATARIO)
    natureza_operacao_id = fields.Many2one('sped.natureza.operacao', 'Natureza da operação', ondelete='restrict')
    infadfisco =  fields.Text('Informações adicionais de interesse do fisco')
    infcomplementar = fields.Text('Informações complementares')
    deduz_retencao = fields.Boolean('Deduz retenção do total da NF?', default=True)
    pis_cofins_retido = fields.Boolean('PIS-COFINS retidos?')
    al_pis_retido = fields.Porcentagem('Alíquota do PIS', default=0.65)
    al_cofins_retido = fields.Porcentagem('Alíquota da COFINS', default=3)
    csll_retido = fields.Boolean('CSLL retido?')
    al_csll =  fields.Porcentagem('Alíquota da CSLL', default=1)
    limite_retencao_pis_cofins_csll = fields.Dinheiro('Obedecer limite de faturamento para retenção de', default=5000)
    irrf_retido = fields.Boolean('IR retido?')
    irrf_retido_ignora_limite = fields.Boolean('IR retido ignora limite de R$ 10,00?')
    al_irrf =  fields.Porcentagem('Alíquota do IR', default=1)
    previdencia_retido = fields.Boolean('INSS retido?')
    cnae_id = fields.Many2one('sped.cnae', 'CNAE')
    natureza_tributacao_nfse = fields.Selection(NATUREZA_TRIBUTACAO_NFSE, 'Natureza da tributação')
    servico_id = fields.Many2one('sped.servico', 'Serviço')
    cst_iss = fields.Selection(ST_ISS, 'CST ISS')

    #
    # Destinatário/Remetente
    #
    participante_id = fields.Many2one('sped.participante', 'Destinatário/Remetente', ondelete='restrict')
    participante_cnpj_cpf = fields.Char('CNPJ/CPF', size=18, related='participante_id.cnpj_cpf', readonly=True)
    participante_tipo_pessoa = fields.Char('Tipo pessoa', size=1, related='participante_id.tipo_pessoa', readonly=True)
    participante_razao_social = fields.NameChar('Razão Social', size=60, related='participante_id.razao_social', readonly=True)
    participante_fantasia = fields.NameChar('Fantasia', size=60, related='participante_id.fantasia', readonly=True)
    participante_endereco = fields.NameChar('Endereço', size=60, related='participante_id.endereco', readonly=True)
    participante_numero = fields.Char('Número', size=60, related='participante_id.numero', readonly=True)
    participante_complemento = fields.Char('Complemento', size=60, related='participante_id.complemento', readonly=True)
    participante_bairro = fields.NameChar('Bairro', size=60, related='participante_id.bairro', readonly=True)
    participante_municipio_id = fields.Many2one('sped.municipio', string='Município', related='participante_id.municipio_id', readonly=True)
    participante_cidade = fields.NameChar('Município', related='participante_id.cidade', readonly=True)
    participante_estado = fields.UpperChar('Estado', related='participante_id.estado', readonly=True)
    participante_cep = fields.Char('CEP', size=9, related='participante_id.cep', readonly=True)
    #
    # Telefone e email para a emissão da NF-e
    #
    participante_fone = fields.Char('Fone', size=18, related='participante_id.fone', readonly=True)
    participante_fone_comercial = fields.Char('Fone Comercial', size=18, related='participante_id.fone_comercial', readonly=True)
    participante_celular = fields.Char('Celular', size=18, related='participante_id.celular', readonly=True)
    participante_email = fields.Email('Email', size=60, related='participante_id.email', readonly=True)
    #
    # Inscrições e registros
    #
    participante_contribuinte = fields.Selection(IE_DESTINATARIO, string='Contribuinte', default='2', related='participante_id.contribuinte', readonly=True)
    participante_ie = fields.Char('Inscrição estadual', size=18, related='participante_id.ie', readonly=True)

    #
    # Chave e validação da chave
    #
    chave = fields.Char('Chave', size=44)

    #
    # Transporte
    #
    transportadora_id = fields.Many2one('res.partner', 'Transportadora', ondelete='restrict', domain=[('cnpj_cpf', '!=', False)])
    veiculo_id = fields.Many2one('sped.veiculo', 'Veículo', ondelete='restrict')
    reboque_1_id = fields.Many2one('sped.veiculo', 'Reboque 1', ondelete='restrict')
    reboque_2_id = fields.Many2one('sped.veiculo', 'Reboque 2', ondelete='restrict')
    reboque_3_id = fields.Many2one('sped.veiculo', 'Reboque 3', ondelete='restrict')
    reboque_4_id = fields.Many2one('sped.veiculo', 'Reboque 4', ondelete='restrict')
    reboque_5_id = fields.Many2one('sped.veiculo', 'Reboque 5', ondelete='restrict')

    #
    # Totais dos itens
    #

    # Valor total dos produtos
    vr_produtos = fields.Dinheiro('Valor dos produtos/serviços')
    vr_produtos_tributacao = fields.Dinheiro('Valor dos produtos para tributação')
    vr_frete = fields.Dinheiro('Valor do frete')
    vr_seguro = fields.Dinheiro('Valor do seguro')
    vr_desconto = fields.Dinheiro('Valor do desconto')
    vr_outras = fields.Dinheiro('Outras despesas acessórias')
    vr_operacao = fields.Dinheiro('Valor da operação')
    vr_operacao_tributacao = fields.Dinheiro('Valor da operação para tributação')

    # ICMS próprio
    bc_icms_proprio = fields.Dinheiro('Base do ICMS próprio')
    vr_icms_proprio = fields.Dinheiro('Valor do ICMS próprio')
    # ICMS SIMPLES
    vr_icms_sn = fields.Dinheiro('Valor do crédito de ICMS - SIMPLES Nacional')
    vr_simples = fields.Dinheiro('Valor do SIMPLES Nacional')
    # ICMS ST
    bc_icms_st = fields.Dinheiro('Base do ICMS ST')
    vr_icms_st = fields.Dinheiro('Valor do ICMS ST')
    # ICMS ST retido
    bc_icms_st_retido = fields.Dinheiro('Base do ICMS retido anteriormente por substituição tributária')
    vr_icms_st_retido = fields.Dinheiro('Valor do ICMS retido anteriormente por substituição tributária')

    # IPI
    bc_ipi = fields.Dinheiro('Base do IPI')
    vr_ipi = fields.Dinheiro('Valor do IPI')

    # Imposto de importação
    bc_ii = fields.Dinheiro('Base do imposto de importação')
    vr_ii = fields.Dinheiro('Valor do imposto de importação')

    # PIS e COFINS
    bc_pis_proprio = fields.Dinheiro('Base do PIS próprio')
    vr_pis_proprio = fields.Dinheiro('Valor do PIS próprio')
    bc_cofins_proprio = fields.Dinheiro('Base da COFINS própria')
    vr_cofins_proprio = fields.Dinheiro('Valor do COFINS própria')
    bc_pis_st = fields.Dinheiro('Base do PIS ST')
    vr_pis_st = fields.Dinheiro('Valor do PIS ST')
    bc_cofins_st = fields.Dinheiro('Base da COFINS ST')
    vr_cofins_st = fields.Dinheiro('Valor do COFINS ST')

    #
    # Totais dos itens (grupo ISS)
    #

    # Valor total dos serviços
    vr_servicos = fields.Dinheiro('Valor dos serviços')

    # ISS
    bc_iss = fields.Dinheiro('Base do ISS')
    vr_iss = fields.Dinheiro('Valor do ISS')

    ### PIS e COFINS
    ###'vr_pis_servico = CampoDinheiro(u'PIS sobre serviços'),
    ##'vr_pis_servico = fields.Dinheiro('PIS sobre serviços'),
    ###'vr_cofins_servico = CampoDinheiro(u'COFINS sobre serviços'),
    ##'vr_cofins_servico = fields.Dinheiro('COFINS sobre serviços'),

    ###
    ### Retenções de tributos (órgãos públicos, substitutos tributários etc.)
    ###
    ###'vr_operacao_pis_cofins_csll = CampoDinheiro(u'Base da retenção do PIS-COFINS e CSLL'),

    ### PIS e COFINS
    ##'pis_cofins_retido = fields.boolean(u'PIS-COFINS retidos?'),
    ##'al_pis_retido = CampoPorcentagem(u'Alíquota do PIS retido'),
    ##'vr_pis_retido = CampoDinheiro(u'PIS retido'),
    ##'al_cofins_retido = CampoPorcentagem(u'Alíquota da COFINS retida'),
    ##'vr_cofins_retido = CampoDinheiro(u'COFINS retida'),

    ### Contribuição social sobre lucro líquido
    ##'csll_retido = fields.boolean(u'CSLL retida?'),
    ##'al_csll = CampoPorcentagem('Alíquota da CSLL'),
    ##'vr_csll = CampoDinheiro(u'CSLL retida'),
    ##'bc_csll_propria = CampoDinheiro(u'Base da CSLL própria'),
    ##'al_csll_propria = CampoPorcentagem('Alíquota da CSLL própria'),
    ##'vr_csll_propria = CampoDinheiro(u'CSLL própria'),

    ### IRRF
    ##'irrf_retido = fields.boolean(u'IR retido?'),
    ##'bc_irrf = CampoDinheiro(u'Base do IRRF'),
    ##'al_irrf = CampoPorcentagem(u'Alíquota do IRRF'),
    ##'vr_irrf = CampoDinheiro(u'Valor do IRRF'),
    ##'bc_irpj_proprio = CampoDinheiro(u'Valor do IRPJ próprio'),
    ##'al_irpj_proprio = CampoPorcentagem(u'Alíquota do IRPJ próprio'),
    ##'vr_irpj_proprio = CampoDinheiro(u'Valor do IRPJ próprio'),

    ### Previdência social
    ##'previdencia_retido = fields.boolean(u'INSS retido?'),
    ##'bc_previdencia = fields.Dinheiro('Base do INSS'),
    ##'al_previdencia = CampoPorcentagem(u'Alíquota do INSS'),
    ##'vr_previdencia = fields.Dinheiro('Valor do INSS'),

    ### ISS
    ##'iss_retido = fields.boolean(u'ISS retido?'),
    ##'bc_iss_retido = CampoDinheiro(u'Base do ISS'),
    ##'vr_iss_retido = CampoDinheiro(u'Valor do ISS'),

    ###
    ### Total da NF e da fatura (podem ser diferentes no caso de operação triangular)
    ###
    ###'vr_nf = CampoDinheiro(u'Valor total da NF'),
    ##'vr_nf = fields.Dinheiro('Valor total da NF'),
    ###'vr_fatura = CampoDinheiro(u'valor total da fatura'),
    ##'vr_fatura = fields.Dinheiro('Valor total da fatura'),

    ##'vr_ibpt = fields.Dinheiro('Valor IBPT'),

    item_ids = fields.One2many('sped.documento.item', 'documento_id', 'Itens')


    @api.onchange('empresa_id', 'modelo', 'emissao')
    def onchange_empresa_id(self):
        res = {}
        valores = {}
        res['value'] = valores

        if not self.empresa_id:
            return res

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return res

        if self.modelo not in (MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE, MODELO_FISCAL_NFSE):
            return res

        if self.modelo == MODELO_FISCAL_NFE:
            valores['ambiente_nfe'] = self.empresa_id.ambiente_nfe
            valores['tipo_emissao_nfe'] = self.empresa_id.tipo_emissao_nfe

            if self.empresa_id.tipo_emissao_nfe == TIPO_EMISSAO_NFE_NORMAL:
                if self.empresa_id.ambiente_nfe == AMBIENTE_NFE_PRODUCAO:
                    valores['serie'] = self.empresa_id.serie_nfe_producao
                else:
                    valores['serie'] = self.empresa_id.serie_nfe_homologacao

            else:
                if self.empresa_id.ambiente_nfe == AMBIENTE_NFE_PRODUCAO:
                    valores['serie'] = self.empresa_id.serie_nfe_contingencia_producao
                else:
                    valores['serie'] = self.empresa_id.serie_nfe_contingencia_homologacao

        elif self.modelo == MODELO_FISCAL_NFCE:
            valores['ambiente_nfe'] = self.empresa_id.ambiente_nfce
            valores['tipo_emissao_nfe'] = self.empresa_id.tipo_emissao_nfce

            if self.empresa_id.tipo_emissao_nfce == TIPO_EMISSAO_NFE_NORMAL:
                if self.empresa_id.ambiente_nfce == AMBIENTE_NFE_PRODUCAO:
                    valores['serie'] = self.empresa_id.serie_nfce_producao
                else:
                    valores['serie'] = self.empresa_id.serie_nfce_homologacao

            else:
                if self.empresa_id.ambiente_nfce == AMBIENTE_NFE_PRODUCAO:
                    valores['serie'] = self.empresa_id.serie_nfce_contingencia_producao
                else:
                    valores['serie'] = self.empresa_id.serie_nfce_contingencia_homologacao

        elif self.modelo == MODELO_FISCAL_NFSE:
            valores['ambiente_nfe'] = self.empresa_id.ambiente_nfse
            valores['tipo_emissao_nfe'] = TIPO_EMISSAO_NFE_NORMAL

            if self.empresa_id.ambiente_nfse == AMBIENTE_NFE_PRODUCAO:
                valores['serie_rps'] = self.empresa_id.serie_rps_producao
            else:
                valores['serie_rps'] = self.empresa_id.serie_rps_homologacao

        return res

    @api.onchange('operacao_id', 'emissao', 'natureza_operacao_id')
    def onchange_operacao_id(self):
        res = {}
        valores = {}
        res['value'] = valores

        if not self.operacao_id:
            return res

        valores['modelo'] = self.operacao_id.modelo
        valores['emissao'] = self.operacao_id.emissao
        valores['entrada_saida'] = self.operacao_id.entrada_saida

        if self.emissao == TIPO_EMISSAO_PROPRIA:
            if self.operacao_id.natureza_operacao_id:
                valores['natureza_operacao_id'] = self.operacao_id.natureza_operacao_id.id

            if self.operacao_id.serie:
                valores['serie'] = self.operacao_id.serie

            valores['regime_tributario'] = self.operacao_id.regime_tributario
            valores['forma_pagamento'] = self.operacao_id.forma_pagamento
            valores['finalidade_nfe'] = self.operacao_id.finalidade_nfe
            valores['modalidade_frete'] = self.operacao_id.modalidade_frete
            valores['infadfisco'] = self.operacao_id.infadfisco
            valores['infcomplementar'] = self.operacao_id.infcomplementar

        valores['deduz_retencao'] = self.operacao_id.deduz_retencao
        valores['pis_cofins_retido'] = self.operacao_id.pis_cofins_retido
        valores['al_pis_retido'] = self.operacao_id.al_pis_retido
        valores['al_cofins_retido'] = self.operacao_id.al_cofins_retido
        valores['csll_retido'] = self.operacao_id.csll_retido
        valores['al_csll'] = self.operacao_id.al_csll
        valores['limite_retencao_pis_cofins_csll'] = self.operacao_id.limite_retencao_pis_cofins_csll
        valores['irrf_retido'] = self.operacao_id.irrf_retido
        valores['irrf_retido_ignora_limite'] = self.operacao_id.irrf_retido_ignora_limite
        valores['al_irrf'] = self.operacao_id.al_irrf
        valores['previdencia_retido'] = self.operacao_id.previdencia_retido
        valores['consumidor_final'] = self.operacao_id.consumidor_final
        valores['presenca_comprador'] = self.operacao_id.presenca_comprador

        if self.operacao_id.cnae_id:
            valores['cnae_id'] = self.operacao_id.cnae_id.id

        valores['natureza_tributacao_nfse'] = self.operacao_id.natureza_tributacao_nfse

        if self.operacao_id.servico_id:
            valores['servico_id'] = self.operacao_id.servico_id.id

        valores['cst_iss'] = self.operacao_id.cst_iss

        return res

    @api.onchange('empresa_id', 'modelo', 'emissao', 'serie', 'ambiente_nfe')
    def onchange_serie(self):
        res = {}
        valores = {}
        res['value'] = valores

        if not self.empresa_id:
            return res

        if self.emissao != TIPO_EMISSAO_PROPRIA:
            return res

        if self.modelo not in (MODELO_FISCAL_NFE, MODELO_FISCAL_NFCE):
            return res

        ultimo_numero = self.search([
                ('empresa_id.cnpj_cpf', '=', self.empresa_id.cnpj_cpf),
                ('ambiente_nfe', '=', self.ambiente_nfe),
                ('emissao', '=', self.emissao),
                ('modelo', '=', self.modelo),
                ('serie', '=', self.serie.strip()),
            ], limit=1, order='numero desc')

        valores['serie'] = self.serie.strip()

        if len(ultimo_numero) == 0:
            valores['numero'] = 1
        else:
            valores['numero'] = ultimo_numero[0].numero + 1

        return res

    @api.depends('consumidor_final')
    @api.onchange('participante_id')
    def onchange_participante_id(self):
        res = {}
        valores = {}
        res['value'] = valores

        #
        # Quando o tipo da nota for para consumidor normal, mas o participante não é
        # contribuinte, define que ele é consumidor final, exceto em caso de operação
        # com estrangeiros
        #
        if self.consumidor_final == TIPO_CONSUMIDOR_FINAL_NORMAL:
            if self.participante_id.estado != 'EX':
                if self.participante_id.contribuinte != INDICADOR_IE_DESTINATARIO:
                    valores['consumidor_final'] = TIPO_CONSUMIDOR_FINAL_CONSUMIDOR_FINAL

        return res
