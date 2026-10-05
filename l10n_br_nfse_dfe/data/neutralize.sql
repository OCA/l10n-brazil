-- force the national NFS-e distribution environment to restricted production
UPDATE res_company
   SET nfse_dfe_environment = 'producao_restrita';
