Na empresa, aba Fiscal > NFS-e:

- **Provedor NFS-e**: GissOnline;
- **Ambiente**: produção ou homologação. A homologação do GissOnline é um
  ambiente único, compartilhado por todos os municípios, com serviços e regras
  que não são os do município: serve para conferir certificado, assinatura e
  leiaute, não a emissão em si;
- **GissOnline Host**: só para município que a biblioteca ainda não conhece
  (o prefixo de `ws-<host>.giss.com.br`).

O certificado A1 da empresa (ou de quem transmite por ela) identifica a conexão
e assina as mensagens; o GissOnline não usa login nem senha. O prestador
precisa estar cadastrado no GissOnline do município, com a emissão por RPS
liberada.
