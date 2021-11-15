# --- Imports --- #

import datetime as dt
from ste import SymbolTableEntry

# --- Variables --- #

KEYWORDS = ("not",)
SPEC_SYMBOLS = (':', '=')


# --- Compiler Class --- #

class Compiler(object):
	
	END_OF_FILE : chr = '0x04' #My choice
	
	def __init__(self, *args):
		"""Constructor for Compiler()"""
		
		#SymbolTable Stuff
		self.__symbolTable : dict = {}
		self.__boolCount = -1
		self.__intCount = -1
		
		# Lexical Stuff
		self.__ch : chr = ''
		self.__token : str = ""
		self.__comment : str = ""
		
		#Error
		self.__lineNo : int = 0
		self.__errorCount : int = 0
		
		# Other
		if len(args) == 2:
			self.__title = args[1]
			args = (self.__title,)*3
		
		try:
			self.__sourceFile = open(f"{args[0]}.cmn", "r")
			self.__listingFile = open(f"{args[1]}.ccmn", "w")
			self.__objectFile = open(f"{args[2]}.asm", "w")
		except Exception:
			print("CompilerError: Unable to open/create important files")
			exit(1)
			
	def __del__(self):
		"""Deconstructor for Compiler()"""
		
		self.__sourceFile.close()
		self.__listingFile.close()
		self.__objectFile.close()
		
	def processError(self, err="") -> None:
		"""Outputs error messages to .ccmn"""
		
		self.__listingFile.write(f"\nLine {self.__lineNo}: {err}\n\n")
		self.__listingFile.write("Automatically generated from compiler.py...\n") # self.__createListingFooter()
		exit(self.__errorCount)
		
	def createHeaders(self):
		"""Creates headers from .ccmn and .asm"""
		
		time = dt.datetime.now(dt.timezone.utc)
		time_str = time.strftime("%Y/%m/%D %H:%M %Z")
		self.__listingFile.write(f"{self.__title}\t{time_str}\n")
		
		self.emitPrologue()
		
	def nextToken(self) -> str:
		"""Determines the next token"""
		
		self.__comment = ""
		self.__token = ""
		
		while self.__token == "":
			if self.__ch == '#':
				while self.__ch != '\n' and self.__ch != self.END_OF_FILE:
					if self.__ch == self.END_OF_FILE:
						self.processError("EOFError: Comment unterminated")
					else:
						self.__comment += self.__ch
						self.nextChar()
						
				self.__comment += self.nextChar()
			elif self.__ch.isspace():
				self.nextChar()
			elif self.__ch.isalpha() and self.__ch != self.END_OF_FILE:
				while (self.__ch.isalpha() or self.__ch.isdigit() or self.__ch == '_') and self.__ch != self.END_OF_FILE:
					self.__token += self.__ch
					self.nextChar()
				
				if self.__ch == self.END_OF_FILE:
					self.processError("EOFError: Unexpected EOF")
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
			
		return self.__ch
		
	def isKeyword(self, s : str):
		return (s in KEYWORDS or isBoolean(s))
		
	def isBoolean(self, s : str):
		return s == "true" or s == "false"
		
	def isSpecSymbol(self, s : str):
		return s in SPEC_SYMBOLS
		
	def isNonKeyId(self, s : str):
		return not isKeyword(s) and all(True if ch.isdigit() or ch.isalpha() or ch == '_' else False for ch in s)
		
	def isInteger(self, s : str):
		return ((s[0] == '+' or s[0] == '-') and s[1:].isdigit()) or s[1:].isdigit()
		
	def isLiteral(self, s : str):
		return isInteger(s) or isBoolean(s) or s == "not true" or s == "not false"
		
	def genInternalName(self, value : str):
		"""Determines the internal name for the variable"""
		
		if value == "BOOLEAN":
			self.__boolCount +=1
			return f"B{self.__boolCount}"
		elif value == "INTEGER":
			self.__intCount +=1
			return f"I{self.__intCount}"
		else:
			return ""
			
	def insert(self, externalName : str, inType : str, inMode : str, inValue : str, inAlloc : str, inUnits : str):
		
		name : list
		
		if "," in externalName:
			name = externalName.split(',')
		else:
			name = (externalName,)
			
		for n in name:
			if isKeyword(n):
				self.processError("SyntaxError: Illegal use of a keyword")
			else:
				if inType == "BOOLEAN" and inMode == "CONSTANT":
					if inValue == "false":
						inValue = 0
					else:
						inValue = -1
				else:
					inValue = 1
					
				symbolTable[name] = SymbolTableEntry(genInternalName(inType),inType,inMode,inValue,inAlloc,inUnits)
				
	def emit(self, label : str = "", instruction : str = "", operands : str = "", comment : str = ""):
		"""Output assembly code"""
		self.__objectFile.write("{:8}{:8}{:24}{}\n".format(label, instruction, operands, comment))
		
	def emitPrologue(self):
		"""Prologue assembly code"""
		
		self.__objectFile.write("%INCLUDE \"Along32.inc\"\n%INCLUDE \"Macros_Along.inc\"\n\n")
		self.emit("SECTION", ".text")
		self.emit("global", "_start", "", f"; {self.__title}")
		self.__objectFile.write("\n")
		self.emit("_start:")
	
	def emitStorage(self):
		"""Variable storage assembly code"""
		
		self.emit("SECTION", ".data")
		for k,v in self.__symbolTable.items():
			if v[2] == "CONSTANT" and v[4] == "YES":
				self.emit(self.genInternalName(v[0]), "dd", v[3], f"; {k}")
				
		self.__objectFile.write("\n")
		self.emit("SECTION", ".bss")
		for k,v in self.__symbolTable.items():
			if v[2] == "VARIABLE" and v[4] == "YES":
				emit(self.genInternalName(v[0]), "resd", v[3], f"; {k}")
		
	def emitEpilogue(self, str1 : str, str2 : str):
		"""Output epilogue assembly code"""
		
		self.emit("", "Exit", "{0}")
		self.__objectFile.write("\n")
		self.emitStorage()
			
	def __main__(self):
		"""Main Function"""
		
		self.nextChar()
		self.nextToken()
		
		if self.__token == "class":
			print("classStmts()")
			#classStmts()
		elif self.__token == "def":
			print("defStmts()")
			# defStmts()
		# elif self.__token #If key id
		else:
			self.processError(f"SyntaxError: Keyword \"class\" or \"def\" expected, not {self.__token}")