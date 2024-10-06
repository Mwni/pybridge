import os
import sys
import json
import struct
import importlib.util
import inspect

script = sys.argv[1]
read_fd = 3
write_fd = 4

read_file = os.fdopen(read_fd, 'rb')
write_file = os.fdopen(write_fd, 'wb')

def pack_value(value):
	if type(value) == bytes:
		type_idx = 1
	else:
		value = json.dumps(value).encode('utf-8')
		type_idx = 0
	
	return struct.pack('>bI', type_idx, len(value)) + value


def unpack_value(buffer):
	type_idx, length = struct.unpack('>bI', buffer[0:5])

	if len(buffer) - 5 < length:
		raise 'incomplete'
	
	value = buffer[5:5+length]

	if type_idx == 1:
		return value
	else:
		return json.loads(value.decode('utf-8'))
	
try:
	script_dir, script_file = os.path.split(script)
	module_name, _ = os.path.splitext(script_file)

	if script_dir not in sys.path:
		sys.path.insert(0, script_dir)
	
	spec = importlib.util.spec_from_file_location(module_name, script)
	module = importlib.util.module_from_spec(spec)
	
	if not module:
		raise '%s is not a python module' % script
	
	spec.loader.exec_module(module)
	
	functions = [
		(name, obj) for name, obj
		in inspect.getmembers(module, inspect.isfunction)
	]
	
	write_file.write(b'\x01' + pack_value([name for name, _ in functions]))
	write_file.flush()
except Exception as e:
	write_file.write(b'\x00' + pack_value(str(e)))
	write_file.flush()
	exit(1)


while True:
	call_header = read_file.read(5)
	
	'''
	if not length:
		exit()
		
	message_length = struct.unpack('!I', length_data)[0]

	# Read the message
	message_data = read_file.read(message_length)
	if len(message_data) < message_length:
		exit()

	task = json.loads(message_data.decode('utf-8'))

	result = DO_THING(**task)

	result_data = json.dumps(result).encode('utf-8')
	result_length = struct.pack('!I', len(result_data))

	write_file.write(result_length)
	write_file.write(result_data)
	write_file.flush()
'''