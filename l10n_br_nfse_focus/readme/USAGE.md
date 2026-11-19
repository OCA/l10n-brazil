Para usar este módulo:

1.  Configure a empresa conforme descrito na seção de Configuração.

2.  Crie uma fatura com o tipo de documento fiscal 'SE'.

3.  Preencha os detalhes necessários:
    - Para **NFSe Municipal:** Preencha o código tributário municipal, impostos e informações correlatas
    - Para **NFSe Nacional:** Preencha o código tributário nacional (NBS), código tributário municipal (se aplicável), impostos e informações correlatas

4.  Valide o documento fiscal.

5.  Envie o Documento Fiscal através do botão "Enviar Documento Fiscal".

6.  Acompanhe o status de processamento do documento. O sistema verificará automaticamente o status através de um cron job, ou você pode verificar manualmente através do botão "Verificar Status".

7.  Após a autorização, o DANFSE (Documento Auxiliar da Nota Fiscal de Serviço Eletrônica) será gerado automaticamente, a menos que a opção "Forçar DANFSE Odoo" esteja marcada na configuração da empresa.
