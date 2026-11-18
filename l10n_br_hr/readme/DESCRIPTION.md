Este é o módulo base dos recursos humanos brasileiro e implementa
adaptações nos modelos básicos do cadastro de Empregados e suas
dependências:

- Campo CPF (armazenado sem máscara, como dígitos puros, no `vat` do
  contato de trabalho — convenção do `l10n_br_base`, pronto para o
  eSocial) com validação;
- CPTS com validação;
- PIS/PASEF (armazenado como dígitos puros, com máscara disponível no
  campo `pis_pasep_formatted`);
- Certificado de serviço militar;
- Naturalidade;
- Escolaridade - usar hr_skills;
- Dependentes - Usar hr_employee_relative;
- RG;
- Título de eleitor;
- Paternidade;
- Etinia;
- Tipo sanguíneo;
- Incapacidade física;
- Tipo: Funcionário / Autônomo / Terceirizado / Cedido;
