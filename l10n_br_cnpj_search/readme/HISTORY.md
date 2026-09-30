## 18.0.1.3.0

- Adiciona o provedor de consulta cpfcnpj.com.br (dados em tempo real, D+0),
  com token e pacote (5 ou 6) configuráveis.
- Preenche o regime tributário (`tax_framework`) do partner a partir do
  Simples Nacional, SIMEI e porte retornados no pacote 6.
- Amplia o pacote 6 (CNPJ D): preenche porte da empresa, situação
  cadastral (com data e motivo), data de abertura, matriz ou filial, data
  de opção pelo Simples Nacional e responsável perante a Receita (nome e
  qualificação).
- Cada sócio do Quadro de Sócios e Administradores vira um contato filho,
  com nome, qualificação e CPF/CNPJ. A opção "CPF.CNPJ: do not import
  partners (QSA)" desliga esse passo.
- O Cartão CNPJ em PDF emitido pela Receita Federal é anexado ao parceiro.
  A opção "CPF.CNPJ: do not attach the CNPJ card PDF" desliga esse passo.
- Nova opção "CPF.CNPJ: fetch state registration (package 16)" (padrão
  desligado): consulta o pacote 16 (CNPJ H) para preencher a Inscrição
  Estadual da UF do endereço. O pacote 16 tem custo próprio por consulta.
