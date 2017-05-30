#!/usr/bin/python3
import sys
from tkinter import *
from tkinter.filedialog import askopenfilename
import io
import traceback
import questions

class Gui:
	def __init__(self, root):
		self.root = root

		# input filename
		Label(self.root, text='Input:', width=6).grid(row=0,column=0)

		self.inputFileEntry = Entry(self.root)
		self.inputFileEntry.insert(END, "questions.json")
		self.inputFileEntry.grid(row=0,column=1,sticky=W+E)

		Button(self.root, text="...", command=self.in_file_dialog).grid(row=0,column=2)

		# output filename
		Label(self.root, text='Output:', width=6).grid(row=1,column=0)

		self.outputFileEntry = Entry(self.root)
		self.outputFileEntry.insert(END, "moodle.xml")
		self.outputFileEntry.grid(row=1,column=1,sticky=W+E)

		Button(self.root, text="...", command=self.out_file_dialog).grid(row=1,column=2,sticky=NE+SW)

		# process
		Button(self.root, text="Go", command=self.process).grid(row=0,column=3,rowspan=2,sticky=NE+SW)
		
		# logging area
		textFrame = Frame( self.root )
		scroll = Scrollbar( textFrame )
		self.text = Text( textFrame, yscrollcommand=scroll.set, bg="Black", fg="White" )
		scroll.config( command=self.text.yview )
		
		#pack everything
		textFrame.grid( row=2, column=0, columnspan=4,sticky=N+S+E+W )
		self.text.pack( side=LEFT, fill=BOTH,expand=1 )
		scroll.pack( side=RIGHT, fill=Y )
		
		self.root.columnconfigure(1,weight=1)
		self.root.rowconfigure(2,weight=1)	

	def in_file_dialog(self):
		name = askopenfilename(filetypes =(("Json", "*.json"),("All Files","*.*")),
					title = "Choose an input file.")
		self.inputFileEntry.delete(0,END)
		self.inputFileEntry.insert(END, name)

	def out_file_dialog(self):
		name = askopenfilename(filetypes =(("XML", "*.xml"),("All Files","*.*")),
					title = "Choose an output file.")
		self.outputFileEntry.delete(0,END)
		self.outputFileEntry.insert(END, name)

	def process(self):
		virtFile = io.StringIO()
		stdout, sys.stdout = sys.stdout, virtFile
		stderr, sys.stderr = sys.stderr, virtFile
		
		try:
			questions.process( [self.inputFileEntry.get()], self.outputFileEntry.get() )
		except Exception as e:
			excInfo = sys.exc_info()
			traceback.print_exception(*excInfo)

		sys.stdout = stdout
		sys.stderr = stderr

		virtFile.seek(0)
		self.text.delete(1.0,END)
		self.text.insert( END, virtFile.read() )

		virtFile.close()

def main():
	root = Tk()
	root.title("Moodle Questions")
	gui = Gui(root)
	root.mainloop()

if __name__ == '__main__':
	sys.exit(main())