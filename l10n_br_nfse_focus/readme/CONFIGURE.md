Após a instalação do módulo, siga os seguintes passos para configurá-lo
para a empresa desejada:

1.  Definições \> Usuários & Empresas \> Empresas

2.  Selecione a empresa desejada

3.  Na visualização da empresa, clique na aba Fiscal

4.  Na subseção NFS-e, configure os seguintes campos:

    > - **Ambiente NFS-e:** Selecione a opção a ser usada no ambiente
    >   (Produção, Homologação)
    > - **Provedor NFS-e:** Selecione a opção FocusNFE
    > - **FocusNFe Token:** Informe o token de acesso da empresa. Obs.
    >   Este token é obtido através da plataforma da FocusNFE
    >   - **Token de Produção:** Token para ambiente de produção (visível quando Ambiente NFS-e = Produção)
    >   - **Token de Homologação:** Token para ambiente de homologação (visível quando Ambiente NFS-e = Homologação)
    > - **Tipo FocusNFe NFSe:** Selecione o tipo de API a ser utilizada:
    >   - **NFSe:** Para emissão de NFSe Municipal (padrão)
    >   - **NFSe Nacional:** Para emissão de NFSe Nacional
    > - **Valor Tipo de Serviço:** Se necessário configure o campo que
    >   deve preencher o valor de tipo de serviço (Service Type ou City Taxation Code)
    > - **Valor Código CNAE:** Se necessário configure o campo que deve
    >   preencher o valor do Código CNAE (CNAE Code ou City Taxation Code)
    > - **Formato Taxa:** Selecione o formato da taxa (Decimal ou Percentage)
    > - **Incluir Documentos Autorizados na Verificação de Status:** Se marcado, documentos autorizados serão incluídos na verificação de status
    > - **Forçar DANFSE Odoo:** Se marcado, o sistema sempre usará o DANFSE do Odoo ao invés do DANFSE da FocusNFE
