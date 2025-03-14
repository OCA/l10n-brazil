Para utilizar o módulo l10n_br_mdfe em conjunto com o módulo
l10n_br_account, é necessário configurar uma linha de operação fiscal
que não adicione valor ao montante do documento, uma vez que o MDF-e
(Manifesto Eletrônico de Documentos Fiscais) não possui valor
financeiro.

**Passo a Passo:**

1.  **Criar uma Fatura:**
    - Defina o tipo de documento como **58 (MDFe)**.
2.  **Configurar o Parceiro da Fatura:**
    - Configure o parceiro para ser o mesmo da empresa emissora do
      MDF-e.
3.  **Adicionar uma Linha na Aba Produtos:**
    - Adicione uma linha de fatura com a operação fiscal previamente
      configurada.
    - **Não recomedamos que informe um produto** ou utilize um produto
      que **não possua CFOP** (Código Fiscal de Operações e Prestações),
      ou que o CFOP esteja configurado para **não gerar valor
      financeiro** e esteja atento a dados como impostos e afins.
4.  **Acesse os detalhes fiscais da fatura e informe os demais dados
    necessário para emissão do MDF-e:**
    - Preencha os campos obrigatórios para emissão do MDF-e, como UF de
      descarregamento, município de descarregamento, etc.
5.  **Valide o MDF-e, verifique os dados do XML e envie para a SEFAZ:**
    - Após preencher todos os dados necessários, valide o MDF-e e envie
      para a SEFAZ.

**Considerações Adicionais**

- **Operação Fiscal:** Certifique-se de que a operação fiscal esteja
  parametrizada corretamente para evitar a adição de valores financeiros
  ao documento.
- **CFOP:** No caso de utilização de um produto cadastrado e que
  carregue o CFOP para a linha da fatura, verifique a configuração do
  CFOP para garantir que ele não gere impacto financeiro no montante da
  fatura.

Seguindo esses passos, o módulo l10n_br_mdfe funcionará corretamente em
conjunto com o l10n_br_account, permitindo a emissão de MDF-e sem
valores financeiros associados.
