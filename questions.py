#!/usr/bin/python3
import sys, json, itertools
import random, copy
import getopt

class Question:
	class UnknownStyle(Exception):
		def __init__(self, value):
			self.value = value
		def __str__(self):
			return str(self.value)

	class NotMCQ(Exception):
		def __init__(self, value):
			self.value = value
		def __str__(self):
			return str(self.value)

	def __variations_possible( self, options, select ):
		""" find the total number possible combinations of select items
			given that we have options values to select from 
			this code is kludgy as hell but works, should probably
			replace with some sort of binomial solution? """	

		variations = 0
		for i in range(2**options):
			if bin(i).count('1') == select:
				variations += 1

		return variations

	def __validate( self ):

		# unrecognized style
		if self.__style not in self.__styles:
			raise self.UnknownStyle('Question type "%s" is not recognized' % self.__style)

	
		if self.__style != 'cloze':
			# check for options
			if self.__options is None or len(self.__options) == 0:
				raise self.NotMCQ( 'No answer options supplied' )

			# must select at least two options otherwise it's not a MCQ
			if self.__select < 2:
				raise self.NotMCQ('Must select more than 2 options or it\'s not an MCQ')

			# can't select more options than there are
			if self.__select > len(self.__options):
				print( '    WARNING - Can\'t select %d options if only %d supplied' % (self.__select, len(self.__options)), file=sys.stderr)
				print( '    WARNING - Reducing options selected to %d' % len(self.__options), file=sys.stderr )
				self.__select = len(self.__options)


	def __init__( self, text, options, style, select, variate, code ):
		self.__styles = ('choice', 'order', 'cloze')
		self.text = text
		self.__options = options
		self.__style = style
		self.__select = select
		self.__variate = variate
		self.code = code

		if type(self.text) is not list:
			self.text = [self.text]

		self.__validate()
		self.__variations = self.create_variations()

	def create_variations( self ):
		variations = []

		if self.__style == 'cloze':
			return variations

		elif self.__style == 'choice':
			# find number of possible variations
			# have to include the correct answer in each one for -1 from options and select
			vposs = self.__variations_possible( len(self.__options)-1, self.__select-1 )
			if vposs < self.__variate:
				print( '    WARNING - Not possible to generate %d unique variations of %d answers from %d wrong answers' % \
					(self.__variate, self.__select, len(self.__options)-1), file=sys.stderr )
				print( '    WARNING - Reducing variations produced to %d' % (vposs), file=sys.stderr )
				self.__variate = vposs

			right = self.__options[0]
			wrong = self.__options[1:]

			variations = [ (right,)+i for i in itertools.combinations(wrong, self.__select-1) ]

		elif self.__style == 'order':
			selectvariations = [ i for i in itertools.combinations(self.__options, self.__select) ]

			variations = []
			for right in selectvariations:
				wrongs = set(itertools.permutations( right ))
				wrongs.remove(right)
				wrongs = list(wrongs)

				for i in range(self.__variate):
					variation = [right] + list( random.sample(wrongs, self.__variate-1) )
					variation = [ ', '.join(i) for i in variation ]
					variations.append( variation )

		variations = random.sample( variations, self.__variate )

		return variations

	def num_variations( self ):
		if self.__style == 'cloze': return 1

		return len(self.__variations)

	def get_cloze( self, v ):
		if self.__style == 'cloze': return ''

		variations = list(self.__variations[v])
		replacements = [ ("<","ᐸ"), (">","ᐳ"), (" ","&nbsp;")]#, ("{","&#123;"), ("}","&#125;") ]

		for i in range(len(variations)):
			for c, r in replacements:
				variations[i] = variations[i].replace(c,r)

		cloze = '{1:MCV:='
		cloze += '~'.join( variations )
		cloze += '}'
		return cloze

	def get_text(self):
		text = self.text
		replacements = [ ("<","ᐸ"), (">","ᐳ")]#, ("{","&#123;"), ("}","&#125;") ]

		for i in range(len(text)):
			for c, r in replacements:
				text[i] = text[i].replace(c,r)

		return "<br/>".join(text)

	def has_code(self):
		return self.code != []

	def get_code(self):
		code = self.code
		replacements = [ ("<","ᐸ"), (">","ᐳ"), (" ","&nbsp;")]#, ("{","&#123;"), ("}","&#125;") ]
		
		for i in range(len(code)):
			for c, r in replacements:
				code[i] = code[i].replace(c,r)

			code[i] = "<span style=\"font-family: 'courier new', courier, monospace;\">{}<br /></span>".format( code[i] )

		return "".join(code)
				

def process( infilenames, outfilename ):
	questions = {}

	for filename in infilenames:
		print( 'Reading "%s"' % filename )
		with open( filename, encoding='utf-8') as f:
			text = f.read()
			structure = json.loads( text )

			# make sure defaults section is fully populated
			if 'defaults' not in structure:
				structure['defaults'] = {}
			if 'variations' not in structure['defaults']:
				structure['defaults']['variations'] = 5
			if 'select' not in structure['defaults']:
				structure['defaults']['select'] = 4
			if 'type' not in structure['defaults']:
				structure['defaults']['type'] = 'choice'

			if 'questions' not in structure:
				structure['questions'] = {}

			# loop over every question in the json and create a Question() object
			for title, body in structure['questions'].items():
				print( "  {}".format(title) )
				if title not in questions:
					questions[title] = []

				if type(body) is not list:
					body = [body]
				
				for b in body:
					if type(b) not in [dict]:
						continue

					print( "    {}...".format( ''.join(b.get("question"))[:60] ) )
					try:
						q = Question( text=b.get("question"), \
					   			   options=b.get("options"), \
						 			 style=b.get("type",       structure['defaults']['type']), \
									select=b.get("select",     structure['defaults']['select']), \
					   			   variate=b.get("variations", structure['defaults']['variations']),
					   			      code=b.get("code", []) )

						questions[title].append( q )

					except (Question.NotMCQ, Question.UnknownStyle) as e:
						print( 'ERROR - %s' % e )
						print( 'ERROR - Skipping question' )
					
				print()

		# cleanup
		for title in [ k for k, v in questions.items() if v == [] ]:
			del questions[title]
		
		print('Generated {} questions'.format(len(questions)) )
		for title, question in questions.items():
			print( "    {} - {} variations".format(title,len(question)) )

	print()
	print( 'Writing "{}"'.format(outfilename) )
	with open( outfilename, 'w', encoding='utf-8' ) as f:
		print( '<?xml version="1.0" encoding="UTF-8"?>', file=f )
		print( '<quiz>', file=f )

		for title, question in questions.items():
			if sum([ i.num_variations() for i in question]) <= 0:
				continue

			print( '  <question type="category">',                              file=f ) 
			print( '    <category>',                                            file=f ) 
			print( '      <text>$course$/Scripted_questions/%s</text>' % title, file=f ) 
			print( '    </category>',                                           file=f ) 
			print( '  </question>',                                             file=f ) 

			count = 1
			for q in question:
				for v in range(q.num_variations()):
					# add the html formatting required to the question text
					vartitle = '%s - variation %d' % (title, count)
					count += 1

					print( '  <question type="cloze">',        file=f )
					print( '    <name>',                       file=f )
					print( '      <text>%s</text>' % vartitle, file=f )
					print( '    </name>',                      file=f )
					print( '    <questiontext format="html">', file=f )
					print( '      <text><![CDATA[<p>%s</p>' % q.get_text(), file=f )
					if q.has_code():
						print( '                 <p>%s</p>' % q.get_code(), file=f )
					print( '                     <p>%s</p>]]></text>' % q.get_cloze(v), file=f )
					print( '    </questiontext>',              file=f )
					print( '  </question>',                    file=f )

			print( file=f )

		print( '</quiz>', file=f )

	return 0

if __name__ == '__main__':
	outfilename = 'moodle.xml'

	options, args = getopt.getopt( sys.argv[1:], 'ho:', ["help", "output="] )

	for opt, arg in options:
		if opt in ('-h', '--help'):
			print( "" )
		elif opt in ('-o', '--output'):
			outfilename = arg

	if len(args) == 0:
		args = ["questions.json"]

	sys.exit( process(args, outfilename) )
