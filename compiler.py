# --- Imports --- #

import datetime as dt
from pprint import pprint
from stack import Stack
from ste import SymbolTableEntry

# --- Variables --- #

#tuple = frozen list (basically)
TYPES = {"int", "bool", "str", "char", "list",} #set, dict, stream
KEYWORDS = {"frozen", "not", "raise"} | TYPES #"class", "def"
SPEC_SYMBOLS = {"=", "-", "+", "<", ">", "(", ")", '[', ']'}
ERRORS = {"ArithmeticError", "AssertionError",
					"AttributeError", "BaseException",
					"BlockingIOError", "BrokenPipeError",
					"BufferError", "BytesWarning",
					"ChildProcessError", "ConnectionAbortedError",
					"ConnectionError", "ConnectionRefusedError",
					"ConnectionResetError", "DeprecationWarning",
					"EOFError", "Ellipsis", "EnvironmentError",
					"Exception", "FileExistsError", "FileNotFoundError",
					"FloatingPointError", "FutureWarning", "GeneratorExit",
					"IOError", "ImportError", "ImportWarning",
					"IndentationError", "IndexError", "InterruptedError",
					"IsADirectoryError", "KeyError", "KeyboardInterrupt",
					"LookupError", "MemoryError", "ModuleNotFoundError",
					"NameError", "NotADirectoryError", "NotImplemented",
					"NotImplementedError", "OSError", "OverflowError",
					"PendingDeprecationWarning", "PermissionError",
					"ProcessLookupError", "RecursionError", "ReferenceError",
					"ResourceWarning", "RuntimeError", "RuntimeWarning",
					"StopAsyncIteration", "StopIteration", "SyntaxError",
					"SyntaxWarning", "SystemError", "SystemExit", "TabError",
					"TimeoutError", "TypeError", "UnboundLocalError",
					"UnicodeDecodeError", "UnicodeEncodeError", "UnicodeError",
					"UnicodeTranslateError", "UnicodeWarning", "UserWarning",
					"ValueError", "Warning", "WindowsError", "ZeroDivisionError"}


# --- Compiler Class --- #

class Compiler(object):

	END_OF_FILE : chr = '0x04' #My choice

	def __init__(self, *args):
		"""Constructor for Compiler()"""

		#SymbolTable Stuff
		self.__symbolTable : dict = {}

		types = tuple((type[0].upper() for type in TYPES))
		self.__counts = dict(zip(types, (-1,)*len(types)))

		#Registers
		self.__contentsOfAReg = ""
		self.__definedStorage = False

		#Stacks
		self.__operatorStk = Stack()
		self.__operandStk = Stack()

		# Lexical Stuff
		self.__ch : chr = ''
		self.__token : str = ""
		self.__comment : str = ""

		#Error
		self.__lineNo : int = 0
		self.__errorCount : int = 0
		self.__check : bool = True

		# Other
		if len(args) == 2:
			self.__title : str = args[1]
			args = (self.__title,)*3

		try:
			self.__sourceFile = open(f"{args[0]}.cmn", "r")
			self.__listingFile = open(f"{args[1]}.ccmn", "w")
			self.__objectFile = open(f"{args[2]}.asm", "w")
		except Exception:
			print("CompilerError: Unable to open/create important files")
			exit(1)

	def isBoolean(self, s : str):
		return s == "True" or s == "False"

	def isInteger(self, s : str):
		return (s[0] == '+' or s[0] == '-' and s[1:].isdigit()) or s.isdigit()

	def isString(self, s : str):
		return s[0] == '\"' and s[-1] == '\"'

	def isChar(self, s : str):
		return s[0] == '\'' and s[-1] == '\''

	def isList(self, s : str): # NEW
		return s[0] == '[' and s[-1] == ']'

	def isSpecSymbol(self, s : str):
		return s in SPEC_SYMBOLS

	def isKeyword(self, s : str):
		return (s in KEYWORDS or self.isBoolean(s))

	def isNonKeyId(self, s : str):
		return not self.isKeyword(s) and all(True if ch.isalnum() or ch == '_' else False for ch in s)

	def isLiteral(self, s : str):
		return self.isInteger(s) or self.isBoolean(s) or s == "not True" or s == "not False" or self.isString(s) or self.isChar(s) or self.isList(s)

	def isTemp(self, s : str):
		return s[0] == "T" and s != "True"

	# def isConst(self, s : str):
		# return all((True if char.isupper() or char.isdigit() or char == '_' else False for char in s))

	def isType(self, s : str):
		return s in TYPES

	def isError(self, s : str):
		return s in ERRORS

	def processError(self, err="") -> None:
		"""Outputs error messages to .ccmn"""

		print(f"Line {self.__lineNo}: {err}")
		self.__errorCount += 1
		self.__listingFile.write(f"\nLine {self.__lineNo}: {err}\n\n")
		self.__listingFile.write("Automatically generated from compiler.py...\n") # self.__createListingFooter()
		exit(self.__errorCount)

	def createHeaders(self):
		"""Creates headers from .ccmn and .asm"""

		time = dt.datetime.now(dt.timezone.utc)

		self.__listingFile.write("{}\t{}\n\n".format(self.__title, time.strftime("%Y/%m/%D %H:%M %Z")))
		self.emitPrologue()

	def whichType(self, name : str):
		"""Determines the type of a variable"""

		datatype : str = ""

		if self.isLiteral(name):
			if self.isBoolean(name) or name == "not True" or name == "not False":
				datatype = "BOOL"#BOOLEAN"
			elif self.isInteger(name):
				datatype = "INT"#INTEGER"
			elif self.isChar(name):
				datatype = "CHAR"
			elif self.isList(name): # NEW
				datatype = "LIST" # NEW
			else:
				datatype = "STR"#STRING"
		else:
			if name in self.__symbolTable:
				datatype = self.__symbolTable[name][1]
			else:
				self.processError("ReferenceError: No type determined")

		return datatype

	def whichValue(self, name : str):
		"""Determines value of a variable"""

		value : str

		if self.isLiteral(name):
			value = name
		else:
			if name in self.__symbolTable:
				value = self.__symbolTable[name].value
			else:
				processError("ReferenceError: No type determined")

		return value

	def prog(self):
		"""Overall program 'statement'"""

		type : str = ""

		while self.__token != self.END_OF_FILE:
			if self.__token == "frozen": #Constant
				self.nextToken()
				self.assignStmt(self.typeStmts(), "CONST")
			elif self.isType(self.__token): #Variable
				self.assignStmt(self.typeStmts(), "VAR")
			elif self.isNonKeyId(self.__token): #Variable
				type = self.typeStmts()
				if self.__token == '=':
					self.assignStmt(type)
				elif self.__token == "<<":#"<-":
					self.writeStmt()
				elif self.__token == ">>":#"->":
					self.readStmt()
			elif self.__token == "raise":
				self.nextToken()
				self.raiseStmt()
			else:
				self.processError(f"SyntaxError: Keyword expected, not {self.__token}")

	def typeStmts(self):

		type : str = ""

		if self.isType(self.__token):
			type = self.__token.upper()
			# type = self.__token
			# if type == "int":
				# type = "INTEGER"
			# elif type == "bool":
				# type = "BOOLEAN"
			# elif type == "str":
				# type = "STRING"
			# elif type == "char":
				# type = "CHAR"
			self.nextToken()
			# print(f"Explicit {str1}")
		# else:
			# print(f"Implicit {str1}")

		self.__operandStk.add(self.__token)
		self.nextToken()
		return type

	def assignStmt(self, type : str, mode : str = "VAR"):

		x : str
		y : str

		if self.__token != "=":
			self.processError(f"SyntaxError: Expected \'=\', got {self.__token}")

		y = self.nextToken()

		if (self.__token == "+" or self.__token == "-"): #If positive or negative int
			self.nextToken()
			if not self.isInteger(self.__token):
				self.processError("SyntaxError: Integer expected after sign")
			y += self.__token
			if y[0] == '+':
				y = y[1:]
		elif self.__token == "not":
			self.nextToken()
			if not self.isBoolean(self.__token):
				self.processError("SyntaxError: Boolean expected after \"not\"")
			y += f" {self.__token}"

		if not (self.isBoolean(self.__token) or self.isInteger(self.__token) or self.isString(self.__token) or
		self.isChar(self.__token) or self.isList(self.__token) or self.isNonKeyId(self.__token)):
			self.processError(f"SyntaxError: Expected boolean, integer, string, char, or list, got {self.__token}")

		if (type != ""): #For explicit vars
			if (self.whichType(self.__token) != type):
				self.processError(f"TypeError: The stated type \"{type}\" was not the type given")

		x = self.__operandStk.pop()
		if x not in self.__symbolTable:
			self.insert(x, self.whichType(y), mode,  self.whichValue(y), "YES", 1)
		else:
			self.code("=", self.__token, x)
		self.nextToken()

	def raiseStmt(self):

		error : str = self.__token
		info : str = ""

		if not self.isError(self.__token):
			self.processError(f"SyntaxError: Expected an error type, got {self.__token}")

		self.nextToken()
		if self.__token == '(':
			info = self.nextToken()
			if not (self.isInteger(self.__token) or self.isString(self.__token) or self.isChar(self.__token)):
				self.processError("SyntaxError: Illegal symbol in raise statement")

		self.nextToken()
		if self.__token != ')':
			self.processError(f"SyntaxError: Expected a ')', got {self.__token}")

		# self.insert("E")
		# self.processError(f"{error}: {info}")

	def readStmt(self):

		if self.__token != ">>":
			self.processError(f"SyntaxError: Expected \">>\", got {self.__token}")

		self.nextToken()
		# operand = ids()
		self.code(">>", self.__token, self.__operandStk.pop())
		self.nextToken()

	def writeStmt(self):

		if self.__token != "<<":
			self.processError(f"SyntaxError: Expected \"<<\", got {self.__token}")

		self.nextToken()
		# operand = ids()
		self.code("<<", self.__token, self.__operandStk.pop())
		self.nextToken()

	def code(self, op : str, rhs : str = "", lhs : str = ""):
		"""Placeholder for important function"""
		if op == "=":
			self.emitAssignCode(rhs, lhs)
		elif op == "<<":
			self.emitWriteCode(rhs, lhs)
		elif op == ">>":
			self.emitReadCode(rhs, lhs)
		else:
			self.processError("CompilerError: Function code should not be called with illegal arguments")

	def nextToken(self) -> str:
		"""Determines the next token"""

		self.__comment = ""
		self.__token = ""

		while self.__token == "":
			if self.__ch == '#':
				while self.__ch != '\n' and self.__ch != self.END_OF_FILE:
					self.__comment += self.__ch
					self.nextChar()
			elif self.__ch.isspace():
				self.nextChar()

			elif self.__ch == "<":
				self.__token += self.__ch
				self.nextChar()
				if self.__ch == "<":
					self.__token += self.__ch
					self.nextChar()
			elif self.__ch == ">":
				self.__token += self.__ch
				self.nextChar()
				if self.__ch == ">":
					self.__token += self.__ch
					self.nextChar()

			elif self.__ch == '\'':
				self.__token += self.__ch
				self.__token += self.nextChar()
				if self.nextChar() != '\'':
					self.processError("SyntaxError: Unexpected letter")
				if self.__ch == self.END_OF_FILE:
					self.processError("EOFError: Unexpected EOF")
				self.__token += self.__ch
				self.nextChar()
			elif self.__ch == '\"':
				self.__token += self.__ch
				while self.nextChar() != '\"':
					if self.__ch == self.END_OF_FILE:
						self.processError("EOFError: Unexpected EOF")
					self.__token += self.__ch
				self.__token += self.__ch
				self.nextChar()
			elif self.__ch == '[': #NEW
				self.__token += self.__ch
				while self.nextChar() != ']':
					if self.__ch == self.END_OF_FILE:
						self.processError("EOFError: Unexpected EOF")
					self.__token += self.__ch
				self.__token += self.__ch
				self.nextChar()

			elif self.isSpecSymbol(self.__ch):
				self.__token = self.__ch
				self.nextChar()
			elif self.__ch.isalpha() and self.__ch != self.END_OF_FILE: #upper is implied const, lower is implied variable
				while (self.__ch.isalpha() or self.__ch.isdigit() or self.__ch == '_') and self.__ch != self.END_OF_FILE:
					self.__token += self.__ch
					self.nextChar()

				if self.__ch == self.END_OF_FILE:
					self.processError("EOFError: Unexpected EOF")
			elif self.__ch.isdigit():
				self.__token = self.__ch
				while (self.nextChar().isdigit() and self.__ch != self.END_OF_FILE):
					self.__token += self.__ch;
			elif self.__ch == self.END_OF_FILE:
				self.__token = self.__ch
			else:
				self.processError(f"SyntaxError: Invalid symbol {self.__ch} received...")

		return self.__token

	def nextChar(self) -> chr:
		"""Gets the next character from the file"""

		self.__ch = self.__sourceFile.read(1)
		if not self.__ch:
			self.__ch = self.END_OF_FILE

		if self.__ch != self.END_OF_FILE:
			if self.__check:
				self.__lineNo += 1;
				self.__listingFile.write("{:>5}| ".format(self.__lineNo))
				self.__check = False;

			self.__listingFile.write(self.__ch)
			if self.__ch == '\n':
				self.__check = True

		return self.__ch

	def genInternalName(self, value : str):
		"""Determines the internal name for the variable"""

		value = value[0].upper()

		self.__counts[value] += 1
		return f"{value}{self.__counts[value]}"
		# if value == "BOOL":
			# self.__counts[value] +=1
			# return f"B{self.__counts[value]}"
		# elif value == "INT":
			# self.__counts[value] +=1
			# return f"I{self.__counts[value]}"
		# elif value == "CHAR":
			# self.__counts[value] += 1
			# return f"C{self.__counts[value]}"
		# elif value == "STR":
			# self.__counts[value] += 1
			# return f"S{self.__counts[value]}"
		# else:
			# return ""

	def getLabel(self):
		"""Return a label name"""

		self.__labelCount += 1
		return f".L{self.__labelCount}"

	def getTemp(self):

		temp : str = ""

		self.__tempNo += 1
		temp = f"t{self.__tempNo}"
		if self.__tempNo > self.__maxTempNo:
			insert(temp, "UNKNOWN", "VARIABLE", "1", "NO", 1)
			self.__maxTempNo += 1

		return temp

	def freeTemp(self):
		"""Free temporary variable from its captivity"""

		self.__tempNo -= 1
		if self.__tempNo < 0:
			self.processError("CompilerError: tempNo should be ≥ –1")

	def insert(self, externalName : str, inType : str, inMode : str, inValue : str, inAlloc : str, inUnits : str):

		name : tuple

		if "," in externalName:
			name = tuple(externalName.split(','))
		else:
			name = (externalName,)

		for n in name:
			if self.isKeyword(n):
				self.processError("SyntaxError: Illegal use of a keyword")
			elif (len(self.__symbolTable) >= 512):
				self.processError("OverflowError: Symbol Table holds too many symbols.")
			elif n in self.__symbolTable:
				if self.__symbolTable[n].mode == "CONST":
					self.processError("RedefinitionError: You may not redefine a constant")
			# else:
			if inType == "BOOL":#"BOOLEAN":
				if inValue == "False":
					inValue = '0'
				else:
					inValue = "-1"
			elif inType == "LIST" and inValue[0] == '[' and inValue[-1] == ']':
				inValue = inValue[1:-1]

			self.__symbolTable[n] = SymbolTableEntry(self.genInternalName(inType),inType,inMode,inValue,inAlloc,inUnits)
			# print(self.__symbolTable[n])

	def emit(self, label : str = "", instruction : str = "", operands : str = "", comment : str = ""):
		"""Output assembly code"""
		self.__objectFile.write("{:8}{:8}{:24}{}\n".format(label, instruction, operands, comment))

	def emitPrologue(self):
		"""Prologue assembly code"""

		self.__objectFile.write("%INCLUDE \"Along32.inc\"\n%INCLUDE \"Macros_Along.inc\"\n\n")
		self.emit("SECTION", ".text")
		self.emit("global", "_start", "", f"; {self.__title}\n")
		self.emit("_start:")

	def emitStorage(self):
		"""Variable storage assembly code"""

		self.emit("SECTION", ".data")
		for k,v in self.__symbolTable.items():
			if v.mode == "CONST" and v.alloc == "YES":
				if v.type == "STR" or v.type == "CHAR":
					self.emit(v.internalName, "dd", f"{v.value},0", f"; {k}")
				else:
					self.emit(v.internalName, "dd", v.value, f"; {k}")

		self.__objectFile.write("\n")
		self.emit("SECTION", ".bss")
		for k,v in self.__symbolTable.items():
			if v.mode == "VAR" and v.alloc == "YES":
				if v.type == "STR" or v.type == "CHAR":
					self.emit(v.internalName, "resd", f"{v.value},0", f"; {k}")
				else:
					self.emit(v.internalName, "resd", v.value, f"; {k}")

	def emitAssignCode(self, rhs : str, lhs : str):

		if rhs not in self.__symbolTable: #if name is not in symbol table
			self.processError(f"ReferenceError: {rhs} is not in symbol table") #processError(reference to undefined symbol)

		if self.__contentsOfAReg != rhs:
			self.emit("", "mov", f"eax,[{self.__symbolTable[rhs].internalName}]")
		self.emit("", "mov", f"[{self.__symbolTable[lhs].internalName}],eax")

	def emitReadCode(self, rhs : str, lhs : str):

		name : str = rhs

		if lhs not in self.__symbolTable:
			self.processError(f"ReferenceError: {lhs} is not in symbol table")
		if name not in self.__symbolTable: #if name is not in symbol table
			self.processError(f"ReferenceError: {name} is not in symbol table") #processError(reference to undefined symbol)

		if self.whichType(name) != "INT": #"INTEGER": #if data type of name is not INTEGER
			self.processError("can't read variables of this type")# processError(can't read variables of this type)

		if self.__symbolTable[name].mode != "VARIABLE": #if storage mode of name is not VARIABLE
			self.processError("attempting to read to a read-only location") #processError(attempting to read to a read-only location)

		self.emit("", "call", "ReadInt", "; read int; value placed in eax") #emit code to call the Irvine ReadInt function
		self.emit("", "mov", f"[{self.__symbolTable[name].internalName}],eax", f"; store eax at {name}") #emit code to store the contents of the A register at name
		self.__contentsOfAReg = name # set the contentsOfAReg = name

	def emitWriteCode(self, rhs : str, lhs : str):

		name : str = rhs

		if lhs not in self.__symbolTable:
			self.processError(f"ReferenceError: {lhs} is not in symbol table")
		if name not in self.__symbolTable:
			self.processError(f"ReferenceError: {name} is not in symbol table")

		if self.__contentsOfAReg != name:
			self.emit("", "mov", f"eax,[{self.__symbolTable[name].internalName}]", f"; load {name} in eax") #emit the code to load name in the A register
			self.__contentsOfAReg = name

		if self.__symbolTable[name].type == "INT": #"INTEGER":
			self.emit("", "call", "WriteInt", "; write int in eax to standard out")
		else:
			self.emit("", "cmp", "eax,0", "; compare to 0") #emit code to compare the A register to 0

			label : str = self.getLabel() #acquire a new label Ln
			self.emit("", "je", label, "; jump if equal to print FALSE") #emit code to jump if equal to the acquired label Ln
			self.emit("", "mov", "edx,TRUELIT", "; load address of TRUE literal in edx") #emit code to load address of TRUE literal in the D register

			label2 : str = self.getLabel() #acquire a new label Ln
			self.emit("", "jmp", label2, f"; unconditionally jump to {label2}") #emit code to unconditionally jump to label L(n + 1)
			self.emit(f"{label}:") #emit code to label the next line with the first acquired label Ln
			self.emit("", "mov", "edx,FALSLIT", "; load address of FALSE literal in edx") #emit code to load address of FALSE literal in the D register
			self.emit(f"{label2}:") #emit code to label the next line with the second acquired label L(n + 1)
			self.emit("", "call", "WriteString", "; write string to standard out") #emit code to call the Irvine WriteString function

			if not self.__definedStorage: #if static variable definedStorage is false
				self.__definedStorage = True #set definedStorage to true
				self.__objectFile.write("\n") #output an endl to objectFile
				self.emit("SECTION", ".data") #emit code to begin a .data SECTION
				self.emit("TRUELIT", "db", "'TRUE',0", "; literal string TRUE") #emit code to create label TRUELIT, instruction db, operands 'TRUE',0
				self.emit("FALSLIT", "db", "'FALSE',0", "; literal string FALSE\n") #emit code to create label FALSELIT, instruction db, operands 'FALSE',0
				self.emit("SECTION", ".text") #emit code to resume .text SECTION

		self.emit("", "call", "Crlf", "; write \r\n to standard out") #emit code to call the Irvine Crlf function

	def emitEpilogue(self):
		"""Output epilogue assembly code"""

		self.emit("", "Exit", "{0}", "\n")
		self.emitStorage()

	def __main__(self):
		"""Main Function"""

		self.createHeaders()
		self.nextChar()
		self.nextToken()
		self.prog()
		self.emitEpilogue()

		pprint(self.__symbolTable)

	def __del__(self):
		"""Deconstructor for Compiler()"""

		self.__sourceFile.close()
		self.__listingFile.close()
		self.__objectFile.close()
