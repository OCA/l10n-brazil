Em Configurações > Empresas > Fiscal, escolha o Provedor NFS-e "Barueri" e
informe a Inscrição Municipal da empresa.

Em cada serviço, o Código de Tributação da Cidade é o código de serviço da
Prefeitura de Barueri com 9 dígitos (por exemplo 140101220). O registro 4 do
arquivo (Ambiente de Dados Nacional) usa o NBS, o Indicador da Operação e a
Classificação Tributária do IBS/CBS do produto ou da linha.

O tomador precisa de número no endereço e de e-mail: Barueri rejeita o RPS
sem eles (erros 240 e 246).

Retenções federais: a retenção vem dos impostos retidos do l10n_br_fiscal
(IRPJ RET, PIS RET, COFINS RET, CSLL RET e INSS RET) definidos na empresa, na
linha da operação fiscal ou no perfil fiscal do parceiro. Cada valor retido
gera um registro tipo 3 (01 IRRF, 02 PIS/PASEP, 03 COFINS, 04 CSLL, 05
Contribuição Previdenciária). O leiaute não tem código para o ISS retido.

Compra governamental: no parceiro, marque Entidade Pública e informe o Tipo
de Entidade Governamental. O arquivo leva então o registro tipo 5.
