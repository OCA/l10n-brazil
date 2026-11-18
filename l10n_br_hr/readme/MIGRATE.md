Na atualização para a 18.0.1.8.0, o campo `cpf` do colaborador é
renomeado para `vat` (`related` ao `vat` do contato de trabalho,
seguindo a convenção do `l10n_br_base` e do núcleo do Odoo). Ajustes
em módulos privados que leem ou gravam `employee.cpf` devem passar a
usar `employee.vat`. O valor armazenado não muda de lugar: ele sempre
residiu no `vat` do `res.partner` do contato de trabalho.
