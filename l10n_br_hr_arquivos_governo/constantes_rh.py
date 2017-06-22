# -*- encoding: utf-8 -*-

# TIPO_DE_FERIAS = (
#     ('1', 'Normal'),
#     ('2', 'Coletiva'),
#     ('3', 'antecipada'),
# )
#
# TIPO_ADMISSAO = (
#     ('1', u'Admissão'),
#     ('2', u'Transferência de empresa no mesmo grupo econômico'),
#     ('3', u'Admissão por sucessão, incorporação ou fusão'),
#     ('4', u'Trabalhador cedido'),
# )
#
# INDICATIVO_ADMISSAO = (
#     ('1', u'Normal'),
#     ('2', u'Decorrente de ação fiscal'),
#     ('3', u'Decorrente de decisão judicial'),
# )
#
# REGIME_TRABALHISTA = (
#     ('1', u'CLT - Consolidação das Leis de Trabalho'),
#     ('2', u'RJU - Regime Jurídico Único'),
#     ('3', u'RJP - Regime Jurídico Próprio'),
# )
#
# REGIME_PREVIDENCIARIO = (
#     ('1', u'RGPS - Regime Geral da Previdência Social'),
#     ('2', u'RPPS - Regime Próprio de Previdência Social'),
#     ('3', u'RPPE - Regime Próprio de Previdência Social no Exterior'),
# )
#
# NATUREZA_ATIVIDADE = (
#     ('1', u'Trabalhador urbano'),
#     ('2', u'Trabalhador rural'),
# )
#
# UNIDADE_SALARIO = (
#     ('1', u'Por hora'),
#     #('2', u'Por dia'),
#     #('3', u'Por semana'),
#     ('4', u'Por mês'),
#     #('5', u'Por tarefa'),
# )
#
# TIPO_CONTRATO = (
#     ('1', u'Prazo indeterminado'),
#     ('2', u'Prazo determinado'),
# )

CATEGORIA_TRABALHADOR = (
    ('101', u'101 - Empregado – Geral'),
    ('102', u'102 - Empregado – Trabalhador Rural por Pequeno Prazo da Lei 11.718/2008'),
    ('103', u'103 - Empregado – Aprendiz'),
    ('104', u'104 - Empregado – Doméstico'),
    ('105', u'105 - Empregado – contrato a termo firmado nos termos da Lei 9601/98'),
    ('106', u'106 - Empregado – contrato por prazo determinado nos termos da Lei 6019/74'),
    ('107', u'107 - Trabalhador não vinculado ao RGPS com direito ao FGTS'),
    ('201', u'201 - Trabalhador Avulso – Portuário'),
    ('202', u'202 - Trabalhador Avulso – Não Portuário (Informação do Sindicato)'),
    ('203', u'203 - Trabalhador Avulso – Não Portuário (Informação do Contratante)'),
    ('301', u'301 - Servidor Público – Titular de Cargo Efetivo'),
    ('302', u'302 - Servidor Público – Ocupante de Cargo exclusivo em comissão'),
    ('303', u'303 - Servidor Público – Exercente de Mandato Eletivo'),
    ('304', u'304 - Servidor Público – Agente Público'),
    ('305', u'305 - Servidor Público vinculado a RPPS indicado para conselho ou órgão representativo, na condição de representante do governo, órgão ou entidade da administração pública'),
    ('401', u'401 - Dirigente Sindical – Em relação a Remuneração Recebida no Sindicato'),
    ('701', u'701 - Contrib. Individual – Autônomo contratado por Empresas em geral'),
    ('702', u'702 - Contrib. Individual – Autônomo contratado por Contrib. Individual, por pessoa física em geral, ou por missão diplomática e repartição consular de carreira estrangeiras'),
    ('703', u'703 - Contrib. Individual – Autônomo contratado por Entidade Beneficente de Assistência Social isenta da cota patronal'),
    ('704', u'704 - Excluído.'),
    ('711', u'711 - Contrib. Individual – Transportador autônomo contratado por Empresas em geral'),
    ('712', u'712 - Contrib. Individual – Transportador autônomo contratado por Contrib. Individual, por pessoa física em geral, ou por missão diplomática e repartição consular de carreira estrangeiras'),
    ('713', u'713 - Contrib. Individual – Transportador autônomo contratado por Entidade Beneficente de Assistência Social isenta da cota patronal'),
    ('721', u'721 - Contrib. Individual – Diretor não empregado com FGTS'),
    ('722', u'722 - Contrib. Individual – Diretor não empregado sem FGTS'),
    ('731', u'731 - Contrib. Individual – Cooperado que presta serviços a empresa por intermédio de cooperativa de trabalho'),
    ('732', u'732 - Contrib. Individual – Cooperado que presta serviços a Entidade Beneficente de Assistência Social isenta da cota patronal ou para pessoa física'),
    ('733', u'733 - Contrib. Individual – Cooperado eleito para direção da Cooperativa'),
    ('734', u'734 - Contrib. Individual – Transportador Cooperado que presta serviços a empresa por intermédio de cooperativa de trabalho'),
    ('735', u'735 - Contrib. Individual – Transportador Cooperado que presta serviços a Entidade Beneficente de Assistência Social isenta da cota patronal ou para pessoa física'),
    ('736', u'736 - Contrib. Individual – Transportador Cooperado eleito para direção da Cooperativa'),
    ('741', u'741 - Contrib. Individual – Cooperado filiado a cooperativa de produção'),
    ('751', u'751 - Contrib. Individual – Micro Empreendedor Individual, quando contratado por PJ'),
    ('901', u'901 - Estagiário'),
)
CATEGORIA_TRABALHADOR_DIC = dict(CATEGORIA_TRABALHADOR)

# TIPO_ESCALA = (
#     ('1', u'12 × 36'),
#     ('2', u'24 × 72'),
#     ('3', u'6 × 18'),
# )
#
# TIPO_JORNADA = (
#     ('1', u'Padrão'),
#     #('2', u'Turno fixo'),
#     #
#     # Turno flexível removido devido a dificuldade de determinar
#     # quantas vezer o funcionário trabalha no turno no mês
#     #
#     #('3', u'Turno flexível'),
#     ('4', u'Especial/escala'),
# )
#
#
# SEXO = (
#     ('M', 'Masculino'),
#     ('F', 'Feminino')
# )
#
# RACA_COR = (
#     ('1', u'Indígena'),
#     ('2', 'Branca'),
#     ('4', 'Negra'),
#     ('6', 'Amarela'),
#     ('8', 'Parda'),
#     ('9', u'Não informada')
# )
#
# ESTADO_CIVIL = (
#     ('1', 'Solteiro(a)'),
#     ('2', 'Casado(a)'),
#     ('3', 'Divorciado(a)'),
#     ('4', u'Viúvo(a)'),
#     ('5', u'Em união estável'),
#     ('6', 'Outros'),
# )
#
# GRAU_INSTRUCAO = (
#     ('01', 'Analfabeto'),
#     ('02', u'Até o 5º ano incompleto do Ensino Fundamental (4ª série, 1º grau ou primário) ou alfabetizado sem ter frequentado escola regular'),
#     ('03', u'5º ano completo do Ensino Fundamental (4ª série, 1º grau ou primário)'),
#     ('04', u'Do 6º ao 9º ano incompletos do Ensino Fundamental (5ª a 8ª série, 1º grau ou ginásio)'),
#     ('05', u'Ensino Fundamental completo (1ª a 8ª série, 1º grau ou primário e ginásio)'),
#     ('06', u'Ensino Médio incompleto (2º grau, secundário ou colegial)'),
#     ('07', u'Ensino Médio completo (2º grau, secundário ou colegial)'),
#     ('08', u'Educação Superior incompleta'),
#     ('09', u'Educação Superior completa'),
#     ('10', u'Pós-graduação'),
#     ('11', u'Mestrado'),
#     ('12', u'Doutorado'),
# )
#
# ESTADO = (
#     ('AC', u'Acre'),
#     ('AL', u'Alagoas'),
#     ('AP', u'Amapá'),
#     ('AM', u'Amazonas'),
#     ('BA', u'Bahia'),
#     ('CE', u'Ceará'),
#     ('DF', u'Distrito Federal'),
#     ('ES', u'Espírito Santo'),
#     ('GO', u'Goiás'),
#     ('MA', u'Maranhão'),
#     ('MT', u'Mato Grosso'),
#     ('MS', u'Mato Grosso do Sul'),
#     ('MG', u'Minas Gerais'),
#     ('PA', u'Pará'),
#     ('PB', u'Paraíba'),
#     ('PR', u'Paraná'),
#     ('PE', u'Pernambuco'),
#     ('PI', u'Piauí'),
#     ('RJ', u'Rio de Janeiro'),
#     ('RN', u'Rio Grande do Norte'),
#     ('RS', u'Rio Grande do Sul'),
#     ('RO', u'Rondônia'),
#     ('RR', u'Roraima'),
#     ('SC', u'Santa Catarina'),
#     ('SP', u'São Paulo'),
#     ('SE', u'Sergipe'),
#     ('TO', u'Tocantins'),
# )
#
# TIPO_DEPENDENTE = (
#     ('01', u'Cônjuge ou companheiro(a) com o(a) qual tenha filho(s) ou viva há mais de 5 anos'),
#     ('02', u'Filho(a) ou enteado(a) até 21 anos'),
#     ('03', u'Filho(a) ou enteado(a) universatário(a) ou cursando escola técnica de 2º grau, até 24 anos'),
#     ('04', u'Filho(a) ou enteado(a) universatário(a) ou cursando escola técnica de 2º grau, até 24 anos'),
# )
#
# TIPO_SANGUINEO = (
#     ('A+', 'A+'),
#     ('A-', 'A-'),
#     ('B+', 'B+'),
#     ('B-', 'B-'),
#     ('AB+', 'AB+'),
#     ('AB-', 'AB-'),
#     ('O+', 'O+'),
#     ('O-', 'O-'),
# )
#
# TIPO_AFASTAMENTO = (
#     ('H', u'H - Rescisão, com justa causa, por iniciativa do empregador.'),
#     ('I1', u'I1 - Rescisão, sem justa causa, por iniciativa do empregador.'),
#     ('I2', u'I2 - Rescisão por culpa recíproca ou força maior.'),
#     ('I3', u'I3 - Rescisão por término do contrato a termo.'),
#     ('I4', u'I4 - Rescisão, sem justa causa, do contrato de trabalho do empregado doméstico, por iniciativa do empregador .'),
#     ('J',  u'J - Rescisão do contrato de trabalho por iniciativa do empregado.'),
#     ('K', u'K - Rescisão a pedido do empregado ou por iniciativa do empregador, com justa causa, no caso de empregado não optante, com menos de um ano de serviço.'),
#     ('L', u'L - Outros motivos de rescisão do contrato de trabalho.'),
#     ('M', u'M - Mudança de regime estatutário.'),
#     ('N1', u'N1 - Transferência do empregado para outro estabelecimento da mesma empresa.'),
#     ('N2', u'N2 - Transferência do empregado para outra empresa que tenha assumido os encargos trabalhistas, sem que tenha havido rescisão de contrato de trabalho.'),
#     ('N3', u'N3 - Empregado proveniente de transferência de outro estabelecimento da mesma empresa ou de outra empresa, sem rescisão do contrato de trabalho.'),
#     ('O1', u'O1 - Afastamento temporário por motivo de acidente do trabalho, por período superior a 15 dias.'),
#     ('O2', u'O2 - Novo afastamento temporário em decorrência do mesmo acidente do trabalho.'),
#     ('O3', u'O3 - Afastamento temporário por motivo de acidente do trabalho, por período igual ou inferior a 15 dias.'),
#     ('P1', u'P1 - Afastamento temporário por motivo de doença, por período superior a 15 dias.'),
#     ('P2', u'P2 - Novo afastamento temporário em decorrência da mesma doença, dentro de 60 dias contados da cessação do afastamento anterior.'),
#     ('P3', u'P3 - Afastamento temporário por motivo de doença, por período igual ou inferior a 15 dias.'),
#     ('Q1', u'Q1 - Afastamento temporário por motivo de licença-maternidade (120 dias).'),
#     ('Q2', u'Q2 - Prorrogação do afastamento temporário por motivo de licença-maternidade.'),
#     ('Q3', u'Q3 - Afastamento temporário por motivo de aborto não criminoso.'),
#     ('Q4', u'Q4 - Afastamento temporário por motivo de licença-maternidade decorrente de adoção ou guarda judicial de criança até (um) ano de idade (120 dias).'),
#     ('Q5', u'Q5 - Afastamento temporário por motivo de licença-maternidade decorrente de adoção ou guarda judicial de criança a partir de 1(um) ano até 4(quatro) anos de idade (60 dias).'),
#     ('Q6', u'Q6 - Afastamento temporário por motivo de licença-maternidade decorrente de adoção ou guarda judicial de criança de 4 (quatro) até 8 (oito) anos de idade (30 dias).'),
#     ('R', u'R - Afastamento temporário para prestar serviço militar.'),
#     ('S2', u'S2 - Falecimento.'),
#     ('S3', u'S3 - Falecimento motivado por acidente do trabalho.'),
#     ('U1', u'U1 - Aposentadoria.'),
#     ('U3', u'U3 - Aposentadoria por invalidez.'),
#     ('V3', u'V3 - Remuneração de comissão e/ou percentagens devidas após a extinção de contrato de trabalho.'),
#     ('W', u'W - Afastamento temporário para exercício de mandato sindical.'),
#     ('X', u'X - Licença sem vencimentos.'),
#     ('Y', u'Y - Outros motivos de afastamento temporário.'),
#     ('Z1', u'Z1 - Retorno de afastamento temporário por motivo de licença-maternidade'),
#     ('Z2', u'Z2 - Retorno de afastamento temporário por motivo de acidente do trabalho'),
#     ('Z3', u'Z3 - Retorno de novo afastamento temporário em decorrência do mesmo acidente do trabalho.'),
#     ('Z4', u'Z4 - Retorno de afastamento temporário por motivo de prestação de serviço militar.'),
#     ('Z5', u'Z5 - Outros retornos de afastamento temporário e/ou licença.'),
#     ('Z6', u'Z6 - Retorno de afastamento temporário por motivo de acidente do trabalho, por período igual ou inferior a 15 dias.'),
# )
#
# TIPO_AFASTAMENTO_DIC = dict(TIPO_AFASTAMENTO)
#
# TIPO_AFASTAMENTO_CAGED = {
#     'H': '32',
#     'I1': '31',
#     'I2': '31',
#     'I3': '45',
#     'I4': '45',
#     'J':  '40',
#     'K': '32',
#     'L': '31',
#     'M': '31',
#     'N1': '80',
#     'N2': '80',
#     'S2': '60',
#     'S3': '60',
#     'U1': '50',
#     'U3': '50',
# }
#
# TIPO_RETORNO = {
#     'Q1': 'Z1',
#     'Q2': 'Z1',
#     'Q3': 'Z1',
#     'Q4': 'Z1',
#     'Q5': 'Z1',
#     'Q6': 'Z1',
#     'O1': 'Z2',
#     'O2': 'Z3',
#     'O3': 'Z6',
#     'R': 'Z4',
#     'P1': 'Z5',
#     'P2': 'Z5',
#     'P3': 'Z5',
#     'U3': 'Z5',
#     'W': 'Z5',
#     'X': 'Z5',
#     'Y': 'Z5',
# }
#
# CODIGO_RECOLHIMENTO_SEFIP = (
#     ('115', u'115 - Recolhimento ao FGTS e informações à Previdência Social'),
#     ('130', u'130 - Recolhimento ao FGTS e informações à Previdência Social relativas ao trabalhador avulso portuário'),
#     ('135', u'135 - Recolhimento e/ou declaração ao FGTS e informações à Previdência Social relativas ao trabalhador avulso não portuário'),
#     ('145', u'145 - Recolhimento ao FGTS de diferenças apuradas pela CAIXA'),
#     ('150', u'150 - Recolhimento ao FGTS e informações à Previdência Social de empresa prestadora de serviços com cessão de mão-de-obra e empresa de trabalho temporário Lei nº 6.019/74, em relação aos empregados cedidos, ou de obra de construção civil – empreitada parcial'),
#     ('155', u'155 - Recolhimento ao FGTS e informações à Previdência Social de obra de construção civil – empreitada total ou obra própria'),
#     ('211', u'211 - Declaração para a Previdência Social de Cooperativa de Trabalho relativa aos contribuintes individuais cooperados que prestam serviços a tomadores'),
#     ('307', u'307 - Recolhimento de Parcelamento de débito com o FGTS'),
#     ('317', u'317 - Recolhimento de Parcelamento de débito com o FGTS de empresa com tomador de serviços'),
#     ('327', u'327 - Recolhimento de Parcelamento de débito com o FGTS priorizando os valores devidos aos trabalhadores'),
#     ('337', u'337 - Recolhimento de Parcelamento de débito com o FGTS de empresas com tomador de serviços, priorizando os valores devidos aos trabalhadores'),
#     ('345', u'345 - Recolhimento de parcelamento de débito com o FGTS relativo a diferença de recolhimento, priorizando os valores devidos aos trabalhadores'),
#     ('418', u'418 - Recolhimento recursal para o FGTS'),
#     ('604', u'604 - Recolhimento ao FGTS de entidades com fins filantrópicos – Decreto-Lei nº 194, de 24/02/1967 (competências anteriores a 10/1989)'),
#     ('608', u'608 - Recolhimento ao FGTS e informações à Previdência Social relativo a dirigente sindical'),
#     ('640', u'640 - Recolhimento ao FGTS para empregado não optante (competência anterior a 10/1988)'),
#     ('650', u'650 - Recolhimento ao FGTS e Informações à Previdência Social relativo a Anistiados, Reclamatória Trabalhista, Reclamatória Trabalhista com reconhecimento de vínculo, Acordo ou Dissídio ou Convenção Coletiva, Comissão Conciliação Prévia ou Núcleo Intersindical Conciliação Trabalhista'),
#     ('660', u'660 - Recolhimento exclusivo ao FGTS relativo a Anistiados, Conversão Licença Saúde em Acidente Trabalho, Reclamatória Trabalhista, Acordo ou Dissídio ou Convenção Coletiva, Comissão Conciliação Prévia ou Núcleo Intersindical Conciliação Trabalhista.'),
# )
#
# TIPO_SAQUE = (
#     ('01', u'01 - Sem justa causa (incl. indireta)'),
#     ('02', u'02 - Por culpa recíproca ou força maior'),
#     ('03', u'03 - Extinção total da empresa'),
#     ('04', u'04 - Extinção do contrato por prazo determinado'),
#     ('  ', u'Código mov. H, J e M'),
#     ('23', u'23 - Por falecimento'),
# )
#
# TIPO_DESLIGAMENTO_RAIS = (
#     ('10', u'10 - Rescisão de contrato de trabalho por justa causa e iniciativa do empregador ou demissão de servidor'),
#     ('11', u'11 - Rescisão de contrato de trabalho sem justa causa por iniciativa do empregador ou exoneração de oficio de servidor de cargo efetivo ou exoneração de cargo em comissão'),
#     ('12', u'12 - Término do contrato de trabalho'),
#     ('20', u'20 - Rescisão com justa causa por iniciativa do empregado (rescisão indireta)'),
#     ('21', u'21 - Rescisão sem justa causa por iniciativa do empregado ou exoneração de cargo efetivo a pedido do servidor'),
#     ('22', u'22 - Posse em outro cargo inacumulável (específico para servidor público)'),
#     ('30', u'30 - Transferência de empregado entre estabelecimentos da mesma empresa ou para outra empresa, com ônus para a cedente'),
#     ('31', u'31 - Transferência de empregado entre estabelecimentos da mesma empresa ou para outra empresa, sem ônus para a cedente'),
#     ('32', u'32 - Readaptação (específico para servidor público)'),
#     ('33', u'33 - Cessão'),
#     ('34', u'34 - Redistribuição (específico para servidor público)'),
#     ('40', u'40 - Mudança de regime trabalhista'),
#     ('50', u'50 - Reforma de militar para a reserva remunerada'),
#     ('60', u'60 - Falecimento'),
#     ('62', u'62 - Falecimento decorrente de acidente do trabalho típico (que ocorre no exercício de atividades profissionais a serviço da empresa)'),
#     ('63', u'63 - Falecimento decorrente de acidente do trabalho de trajeto (ocorrido no trajeto residência–trabalho–residência)'),
#     ('64', u'64 - Falecimento decorrente de doença profissional'),
#     ('70', u'70 - Aposentadoria por tempo de contribuição, com rescisão contratual'),
#     ('71', u'71 - Aposentadoria por tempo de contribuição, sem rescisão contratual'),
#     ('72', u'72 - Aposentadoria por idade, com rescisão contratual'),
#     ('73', u'73 - Aposentadoria por invalidez, decorrente de acidente do trabalho'),
#     ('74', u'74 - Aposentadoria por invalidez, decorrente de doença profissional'),
#     ('75', u'75 - Aposentadoria compulsória'),
#     ('76', u'76 - Aposentadoria por invalidez, exceto a decorrente de doença profissional ou acidente do trabalho'),
#     ('78', u'78 - Aposentadoria por idade, sem rescisão contratual'),
#     ('79', u'79 - Aposentadoria especial, com rescisão contratual'),
#     ('80', u'80 - Aposentadoria especial, sem rescisão contratual'),
# )
