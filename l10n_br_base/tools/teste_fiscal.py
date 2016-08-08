import sys
from fiscal import *
"""
 Testes para validacao de ie,cnpj, cpf
 
 TODO: passar testes para unittest2 

"""
def str2bool(v):
  return v.lower() in ("yes","true","t","1")

if __name__ == "__main__":
  testDataFileName=sys.argv[1]
  datafile = open(testDataFileName,"r")
  testCases = datafile.readlines()
  for case in testCases:
    [doc,uf,tipo,mensagem,esperado]=map(str.strip,case.split(";"))
    if tipo=="IE":
      print "%s >>> %s;%s;%s;%s" % ( mensagem, doc,
                         "OK" if validate_ie_param(uf,doc)==str2bool(esperado) else "FAIL",
                         "OK" if validate_ie_to(doc)==str2bool(esperado) else "FAIL",
                         "OK" if validate_ie_to_antiga(doc)==str2bool(esperado) else "FAIL")

