The registers 0000 and 0010 of the file are filled in with the data of the
company: CNPJ, name, legal name, state tax number, address, ZIP code, city
and state. Make sure they are properly filled in before generating a file.

The unit of measure of a goods is written with the abbreviation of the table
of the Ato COTEPE ICMS 61/2012 (for instance `kg` and not `quilograma`). The
abbreviation is taken from the *Code* field of the unit of measure of the
product and falls back to `99` (other units) when the code is not in the
table. The code can also be changed line by line.
