import sys
from SICAssembler import SIC

if len(sys.argv) < 3:
    print('Error: 3 arguments required:')
    print('       1. Source file')
    print('       2. Intermediate file')
    print('       3. Object file')
    exit()

sourceFile = sys.argv[1]
intermediateFile = sys.argv[2]
objectFile = sys.argv[3]

sic = SIC(sourceFile, intermediateFile, objectFile)
sic.pass1()
sic.pass2()

sic.printInfo()