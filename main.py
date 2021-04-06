#!/usr/bin/env python3

class SIC:
    def __init__(self, asmFile):
        self.asmFile = asmFile
        self.intermediate = None
        self.symtab = []
        self.literals = []
        self.startAddress = hex(0)
        self.locctr = hex(0)
        self.programName = ''
        self.programSize = hex(0)
        self.optab = [
            { 'name': 'ADD' , 'format': '3', 'opcode': '18' },
            { 'name': 'COMP', 'format': '3', 'opcode': '28' },
            { 'name': 'DIV' , 'format': '3', 'opcode': '24' },
            { 'name': 'J'   , 'format': '3', 'opcode': '3C' },
            { 'name': 'JEQ' , 'format': '3', 'opcode': '30' },
            { 'name': 'JGT' , 'format': '3', 'opcode': '34' },
            { 'name': 'JLT' , 'format': '3', 'opcode': '38' },
            { 'name': 'JSUB', 'format': '3', 'opcode': '48' },
            { 'name': 'LDA' , 'format': '3', 'opcode': '00' },
            { 'name': 'LDCH', 'format': '3', 'opcode': '50' },
            { 'name': 'LDL' , 'format': '3', 'opcode': '08' },
            { 'name': 'LDX' , 'format': '3', 'opcode': '04' },
            { 'name': 'MUL' , 'format': '3', 'opcode': '20' },
            { 'name': 'OR'  , 'format': '3', 'opcode': '44' },
            { 'name': 'RD'  , 'format': '3', 'opcode': 'D8' },
            { 'name': 'RSUB', 'format': '3', 'opcode': '4C' },
            { 'name': 'STA' , 'format': '3', 'opcode': '0C' },
            { 'name': 'STCH', 'format': '3', 'opcode': '54' },
            { 'name': 'STL' , 'format': '3', 'opcode': '14' },
            { 'name': 'STSW', 'format': '3', 'opcode': 'E8' },
            { 'name': 'STX' , 'format': '3', 'opcode': '10' },
            { 'name': 'SUB' , 'format': '3', 'opcode': '1C' },
            { 'name': 'TD'  , 'format': '3', 'opcode': 'E0' },
            { 'name': 'TIX' , 'format': '3', 'opcode': '2C' },
            { 'name': 'WD'  , 'format': '3', 'opcode': 'DC' }
        ]

    def addIntToLocctr(self, num):
        self.locctr = hex(int(self.locctr, 16) + num)

    def addOperandSize(self, operand):
        start_index = operand.find('`') + 1
        size = len(operand[start_index:-1])
        if operand[start_index - 2] == "X":
            size = size//2
        self.addIntToLocctr(size)

    def writeLiterals(self):
        for literal in self.literals:
            self.intermediate.write('{:<8}'.format(self.locctr[2:]).upper())
            self.intermediate.write('{:<11}'.format('*') + literal + '\n')
            self.addOperandSize(literal)
        self.literals = []

    def writeLine(self, address, line):
        loc = ' '*8
        if address:
            loc = '{:<8}'.format(address[2:]).upper()
        self.intermediate.write(loc + line[:39].rstrip() + '\n')

    def splitLine(self, line):
        label = line[:10].strip()
        opcode = line[11:20].strip()
        operand = line[21:39].strip()
        return label, opcode, operand

    def implementPass1(self, intermediate):
        try:
            self.asmFile = open(self.asmFile, 'r')
        except(FileNotFoundError):
            exit('ERROR: asm file not found!')

        self.intermediate = open(intermediate, 'w')
        lines = self.asmFile.readlines()

        for i, line in enumerate(lines):
            try:
                # Discard comments
                if line[0] == '.':
                    self.writeLine(None, line)
                    continue

                # Split the line into: label, opcode, and operand
                label, opcode, operand = self.splitLine(line)
                # print(line)
                # print(label, opcode, operand)
                if opcode == 'START':
                    # Set the start address and program name
                    self.locctr = hex(int(operand, 16))
                    self.startAddress = hex(int(operand, 16))
                    self.programName = label
                    self.writeLine(self.locctr, line)
                    continue

                # Write address and line to intermediate file
                self.writeLine(None if opcode == 'END' else self.locctr, line)

                # Add label to SYMTAB
                if label:
                    if len([symbol for symbol in self.symtab if symbol['name'] == label]):
                        exit('ERROR: Duplicate symbol \'' + label + '\' at line ' + str(i+1))
                    self.symtab.append({'name': label, 'loc': self.locctr[2:].upper()})

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
                elif opcode == "END":
                    self.addIntToLocctr(3)
                    return
                else:
                    try:
                        opcode = [op for op in self.optab if op['name'] == opcode][0]
                    except(Exception):
                        exit('ERROR: oppcode \'' + opcode + '\' is unknown! at line ' + str(i+1))
                    self.addIntToLocctr(int(opcode['format'], 16))
            except(Exception):
                exit('ERROR: something went wrong on line ' + str(i+1))

        if len(self.literals):
            self.writeLiterals()
        self.programSize = hex((int(self.locctr, 16)) - int(self.startAddress, 16))

    def printInfo(self):
        print('Program Name:', self.programName)
        print('Starting Address:', self.startAddress)
        print('Program Size:', self.programSize)

    def printSYMTAB(self):
        print('Symbol Table:')
        for symbol in self.symtab:
            print('{:<10}'.format(symbol['name']) + ' ' + symbol['loc'])

sic = SIC('test_file-2.asm')
sic.implementPass1('intermediate.mdt')
sic.printSYMTAB()