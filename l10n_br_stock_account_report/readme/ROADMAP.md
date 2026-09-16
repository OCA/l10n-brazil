A partir da v16 passou a ser necessário usar o módulo [report_wkhtmltopdf_param](https://github.com/OCA/reporting-engine/tree/16.0/report_wkhtmltopdf_param) para incluir o parâmetro **--encoding utf-8** ao chamar o comando **wkhtmltopdf**, sem isso caracteres **UTF-8** como por exemplo **é ç ã á à â ü, etc** apesar de aparecerem corretamente no **HTML** não são criados corretamente no **PDF**.
É preciso avaliar se a criação do PDF deve ser feita de alguma outra forma ou no momento da migração para as próximas versões se isso foi corrigido, porém é preciso estar ciente de que a biblioteca **Wkhtmltopdf** já foi descontinuada e a **Odoo SA** está buscando criar uma nova biblioteca, segue os links para acompanhar:

* [Issue no projeto Wkhtmltopdf sobre o status, o projeto foi alterado para Public archive em 02/01/2023](https://github.com/wkhtmltopdf/wkhtmltopdf/issues/5160#issuecomment-1010668103)
* [Status do Projeto Wkhtmltopdf no site oficial](https://wkhtmltopdf.org/status.html)
* [Issue no Odoo na v15 sobre o problema com referencia a correção](https://github.com/odoo/odoo/issues/80184)
* [Issue no Odoo na v15 sobre erro mesmo no método render_pdf_qweb em Aberto e marcadao como ORM](https://github.com/odoo/odoo/issues/84418)
* [Debate no Issue do Odoo sobre substituir o Wkhtmltopdf](https://github.com/odoo/odoo/issues/86501)
* [Biblioteca paper-muncher da Odoo para substituir o wkhtmltopdf, ainda em testes](https://github.com/odoo/paper-muncher)

Portanto isso é uma questão ainda em aberto e em andamento, onde tanto pode acabar sendo adotada a biblilioteca **paper-muncher** quanto outra, então também é importante acompanhar o que será feito na **OCA** principalmente no repósitorio [reporting-engine](https://github.com/OCA/reporting-engine). 
