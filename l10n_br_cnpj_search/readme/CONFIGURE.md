Esta busca de informações a partir do cnpj é realizada com base no
provedor configurado na aba de configurações, vale ressaltar que o
provedor receitaws permite a realização de três consultas por minuto,
enquanto que o SERPRO é pago e permite consultas ilimitadas em seus
planos.

O provedor cpfcnpj.com.br é comercial, com dados em tempo real (D+0),
sem o limite de três consultas por minuto do receitaws. Os dados vêm
diretamente da Receita Federal no momento da consulta. Para utilizá-lo,
selecione "CPF.CNPJ" no campo provedor e informe o token de acesso
e o pacote desejado. O pacote 5 (CNPJ B) é a opção mais leve (cadastro e
endereço, sem sócios e sem PDF), enquanto o pacote 6 (CNPJ D) é o
cadastro completo (porte, situação cadastral, Simples Nacional, Quadro
de Sócios e Administradores e Cartão CNPJ em PDF). O token é gravado em
`ir.config_parameter` e nunca fica no código. Com o pacote 6, o módulo
também preenche o regime tributário (`tax_framework`) do partner.

Ao selecionar o provedor CPF.CNPJ, ficam visíveis em Configurações >
Contatos as opções a seguir:

- "CPF.CNPJ: do not import partners (QSA)" (padrão desligado): por padrão
  cada sócio do Quadro de Sócios e Administradores vira um contato filho,
  com nome, qualificação e CPF/CNPJ. Marque esta opção para pular esse
  passo.
- "CPF.CNPJ: do not attach the CNPJ card PDF" (padrão desligado): por
  padrão o Cartão CNPJ em PDF emitido pela Receita Federal, retornado pela
  API no mesmo request, é anexado ao parceiro. Marque esta opção para não
  anexar.
- "CPF.CNPJ: fetch state registration (package 16)" (padrão desligado):
  faz uma segunda consulta ao pacote 16 (CNPJ H) para preencher a
  Inscrição Estadual da UF do endereço. O pacote 16 tem custo próprio por
  consulta, por isso a opção vem desligada.

O provedor é auditado sob as normas ISO/IEC 27001, ISO/IEC 27701 e ISO
37301. Consulte a documentação da API, os pacotes disponíveis e as
credenciais em https://www.cpfcnpj.com.br/dev/.
