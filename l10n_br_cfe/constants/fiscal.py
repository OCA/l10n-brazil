AMBIENTE_CFE = (
    ('1', 'Produção'),
    ('2', 'Homologação'),
)
AMBIENTE_CFE_DICT = dict(AMBIENTE_CFE)

AMBIENTE_CFE_PRODUCAO = '1'
AMBIENTE_CFE_HOMOLOGACAO = '2'

TIPO_EMISSAO_CFE = (
    ('1', 'Normal'),
    ('2', 'Integrador Fiscal'),
    ('9', 'Contingência offline NFC-e'),
    ('10', 'Contingência online NFC-e'),
)
TIPO_EMISSAO_CFE_DICT = dict(TIPO_EMISSAO_CFE)

TIPO_EMISSAO_CFE_NORMAL = '1'
TIPO_EMISSAO_CFE_INTEGRADOR_FISCAL = '2'
TIPO_EMISSAO_CFE_CONTINGENCIA_OFFLINE_NFCE = '9'
TIPO_EMISSAO_CFE_CONTINGENCIA_ONLINE_NFCE = '10'

TIPO_CONEXAO_PROCESSADOR_CFE = (
    ('usb', 'Conectado na porta USB'),
    ('rede_local', 'Conectado em rede local/vpn'),
    ('nuvem', 'Conexão via navegador'),
)
