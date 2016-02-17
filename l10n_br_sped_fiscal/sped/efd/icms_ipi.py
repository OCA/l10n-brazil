from sped.efd.icms_ipi.arquivos import ArquivoDigital as SpedFiscal

efd = SpedFiscal()


registro_abertura = efd._registro_abertura

blocos = efd._blocos

escrita = efd.readfile('/home/mileo/sped.txt')

efd._blocos
