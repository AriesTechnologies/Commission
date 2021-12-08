# --- Imports --- #

import sys
import compiler

if __name__ == "__main__":
	
	c = compiler.Compiler(*sys.argv)
	c.__main__()