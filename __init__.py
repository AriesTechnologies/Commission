# --- Imports --- #

import sys
import compiler


# --- Main Def --- #

def __main__(args):
	
	c = compiler.Compiler(*args)
	
	c.createHeaders()
	c.__main__()
	

if __name__ == "__main__":
	__main__(sys.argv)