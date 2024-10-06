def hello():
	return 'world'

def foo(num):
	return [['bar'] * num]

def binary(blob):
	return blob + blob + blob

class Test:
	def __init__(self):
		print('class init')
		self.the_thing = 'it'

	def do_thing(self):
		return 'I did %s' % self.the_thing