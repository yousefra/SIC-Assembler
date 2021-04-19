#!/usr/bin/env python3
from terminaltables import AsciiTable

class SIC:
    def __init__(self, asmFile=None, intermediateFile=None, objectFile=None, X='8000'):
        self.fileNames = {
            'asmFile': asmFile,
            'intermediateFile': intermediateFile,
            'objectFile': objectFile,
        }
        self.asmFile = None
        self.intermediateFile = None
        self.objectFile = None
        self.X = X
        
        self.symtab = {}
        self.literals = []
        self.literalsAddresses = {}
        self.errors = {}

        self.startAddress = hex(0)
        self.locctr = hex(0)
        self.programName = ''
        self.programSize = hex(0)

        self.optab = {
            'ADD' : '18',
            'AND' : '28',
            'COMP': '28',
            'DIV' : '24',
            'J'   : '3C',
            'JEQ' : '30',
            'JGT' : '34',
            'JLT' : '38',
            'JSUB': '48',
            'LDA' : '00',
            'LDCH': '50',
            'LDL' : '08',
            'LDX' : '04',
            'MUL' : '20',
            'OR'  : '44',
            'RD'  : 'D8',
            'RSUB': '4C',
            'STA' : '0C',
            'STCH': '54',
            'STL' : '14',
            'STSW': 'E8',
            'STX' : '10',
            'SUB' : '1C',
            'TD'  : 'E0',
            'TIX' : '2C',
            'WD'   :'DC',
        }

    def addIntToLocctr(self, num):
        self.locctr = hex(int(self.locctr, 16) + num)

    def addOperandSize(self, operand):
        start_index = operand.find('`')
        if start_index == -1:
            start_index = operand.find('\'')
        size = len(operand[start_index + 1:-1])
        if operand[start_index - 1] =='X':
            size = size//2
        self.addIntToLocctr(size)

    def writeLiterals(self, eof = False):
        for i, literal in enumerate(self.literals):
            loc = self.locctr[2:].upper().zfill(4)
            self.intermediateFile.write('{:<8}'.format(loc))
            self.intermediateFile.write('{:<11}'.format('*') + literal + '\n')
            self.literalsAddresses[literal] = loc
            self.addOperandSize(literal)
            self.literals = []

    def writeLineToIntermediate(self, address, line):
        loc = ' '*8
        if address:
            loc = '{:<8}'.format(address[2:].zfill(4)).upper()
        self.intermediateFile.write(loc + line[:39].rstrip() + '\n')

    def splitLine(self, line):
        label = line[:10].strip()
        opcode = line[11:20].strip()
        operand = line[21:39].strip()
        return label, opcode, operand

    def writeObjFile(self, lines):
        self.objectFile = open(self.fileNames['objectFile'], 'w')
        
        # Header record
        headerRecord = 'H^' + '{:<6}'.format(self.programName) + '^' + self.startAddress.zfill(6) + '^' + self.programSize.zfill(6)
        self.objectFile.write(headerRecord + '\n')

        # Initialize text record
        textRecord = 'T^' + self.startAddress.zfill(6)
        objCodeStr = ''
        objCodeLen = 0

        for i, line in enumerate(lines):
            objCode = line[47:].strip()

            label, opcode, operand = self.splitLine(line[8:])
            if line[8] == '.' or opcode in ['START', 'END', 'LTORG'] or objCode == '0':
                continue

            # If length of record bigger than 60 or it's null
            if not objCode or (objCodeLen + len(objCode) > 60):
                # If there is a current text record, write it and reset the new record
                if objCodeLen:
                    length = hex(objCodeLen // 2)[2:].upper().zfill(2)
                    textRecord += '^' + length + objCodeStr + '\n'
                    self.objectFile.write(textRecord)

                    textRecord = 'T^' + line[:8].strip().zfill(6)
                    objCodeStr = ''
                    objCodeLen = 0
                    
                    if objCode:
                        objCodeStr = '^' + objCode
                        objCodeLen = len(objCode)

                        if i == len(lines) - 1:
                            length = hex(objCodeLen // 2)[2:].upper().zfill(2)
                            textRecord += '^' + length + objCodeStr + '\n'
                            self.objectFile.write(textRecord)

                continue
            
            objCodeStr += '^' + objCode
            objCodeLen += len(objCode)

        # End record
        endRecord = 'E^' + self.startAddress.zfill(6)
        self.objectFile.write(endRecord)

    def pass1(self):
        try:
            self.asmFile = open(self.fileNames['asmFile'], 'r')
        except(FileNotFoundError):
            exit('ERROR: asm file not found!')

        self.intermediateFile = open(self.fileNames['intermediateFile'], 'w')
        lines = self.asmFile.readlines()

        for i, line in enumerate(lines):
            try:
                # Discard comments
                if line[0] == '.':
                    self.writeLineToIntermediate(None, line)
                    continue

                # Split the line into: label, opcode, and operand
                label, opcode, operand = self.splitLine(line)
                
                if opcode == 'START':
                    # Set the start address and program name
                    self.locctr = hex(int(operand, 16))
                    self.startAddress = operand
                    self.programName = label
                    self.writeLineToIntermediate(self.locctr, line)
                    continue

                # Write address and line to intermediate file
                self.writeLineToIntermediate(None if opcode == 'END' else self.locctr, line)

                # Add label to SYMTAB
                if label:
                    if label in self.symtab:
                        self.errors[str(i+1)] = 'Duplicate symbol \'' + label + '\''
                        continue
                    self.symtab[label] = self.locctr[2:].upper().zfill(4)

                # Check if it's a literal
                if operand and operand[0] == '=' and operand not in self.literals:
                    self.literals.append(operand)

                if opcode == 'WORD':
                    self.addIntToLocctr(3)
                elif opcode == 'BYTE':
                    self.addOperandSize(operand)
                elif opcode == 'RESW':
                    self.addIntToLocctr(int(operand)*3)
                elif opcode == 'RESB':
                    self.addIntToLocctr(int(operand))
                elif opcode == 'LTORG':
                    self.writeLiterals()
                elif opcode == 'END':
                    break
                else:
                    if opcode not in self.optab:
                        self.errors[str(i+1)] = 'Unknown oppcode \'' + opcode + '\''
                    self.addIntToLocctr(3)
            except(Exception):
                exit('ERROR: something went wrong on line ' + str(i+1))

        if len(self.literals):
            self.writeLiterals(True)

        self.programSize = hex((int(self.locctr, 16)) - int(self.startAddress, 16))[2:].upper()

    def pass2(self):
        try:
            self.intermediateFile = open(self.fileNames['intermediateFile'], 'r')
        except(FileNotFoundError):
            exit('ERROR: intermediateFile file not found!')

        lines = self.intermediateFile.readlines()
        listingFile = open('listing_file.lst', 'w')

        for i, line in enumerate(lines):
            try:
                # Split the line into: label, opcode, and operand
                label, opcode, operand = self.splitLine(line[8:])

                # Discard comments
                if line[8] == '.' or opcode == 'START':
                    lines[i] = line.rstrip()
                    listingFile.write(line)
                    continue

                # Initialize object code
                objCode = ''

                if opcode in self.optab:
                    objCode = self.optab[opcode]

                # Check if line has an error
                if str(i+1) in self.errors:
                    objCode = '0'
                # Handling a normal directive
                elif objCode:
                    address = '0000'

                    if operand:
                        # Literal is used
                        if operand[0] == '=':
                            address = self.literalsAddresses[operand]
                        else:
                            index = operand.find(',X')

                            # Indexing is used
                            if index != -1:
                                symbol = operand[:index]
                                if symbol not in self.symtab:
                                    self.errors[str(i+1)] = 'Undefined symbol \'' + symbol + '\''
                                    continue
                                address = hex(int(self.symtab[symbol], 16) + int(self.X, 16))[2:].upper()
                            # No indexing
                            else:
                                if operand not in self.symtab:
                                    self.errors[str(i+1)] = 'Undefined symbol \'' + operand + '\''
                                    continue
                                address = self.symtab[operand]
        
                    objCode += address

                # Handling 'WORD'
                elif opcode == 'WORD':
                    # get value and change it to hexadecimal
                    objCode = str(hex(int(operand))[2:]).zfill(6)

                # Handling 'BYTE' & Literals
                elif opcode == 'BYTE' or label == '*':
                    if label == '*':
                        operand = opcode
                    index = operand.find('`')
                    if index == -1:
                        index = operand.find('\'')
                    
                    # Normal string
                    if operand[index - 1] == 'C':
                        data = operand[index + 1:-1]
                        address = ''
                        # Convert string characters to ascii hexadecimal values
                        for c in data:
                            address += str(hex(ord(c))[2:]).upper()
                            
                    # Hexadecimal string
                    elif operand[index - 1] == 'X':
                        address = operand[index + 1:-1]

                    objCode = address

                # add object code to line
                line = '{:<47}'.format(line.rstrip()) + objCode
                lines[i] = line
                listingFile.write(line + '\n')
            except(Exception):
                self.errors[str(i+1)] = 'Unknown error'
        self.writeObjFile(lines)

    """
        Display information about the SIC program
    """
    def printInfo(self):
        # General info
        info_table = AsciiTable([
            ['Program Name', self.programName],
            ['Starting Address', self.startAddress],
            ['Program Size', self.programSize],
        ])
        info_table.title = 'General Info'
        info_table.inner_heading_row_border = False
        print(info_table.table + '\n')

        # Symbol Table
        data = [[symbol, loc] for symbol, loc in self.symtab.items()]
        data.insert(0, ['Symbol', 'Location'])
        symtab = AsciiTable(data)
        symtab.title = 'SYMTAB'
        print(symtab.table + '\n')

        # Error log
        if len(self.errors):
            data = [['[x] ' + error + ' at line ' + i] for i, error in self.errors.items()]
            errors = AsciiTable(data)
            errors.title = 'Errors Log'
            errors.inner_heading_row_border = False
            print(errors.table)