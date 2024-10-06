import os
import sys
import json
import struct
import importlib.util
import inspect

script = sys.argv[1]
class_name = sys.argv[3] if len(sys.argv) == 4 else None
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
	offset = 5 + length

	if len(buffer) < offset:
		raise 'incomplete'
	
	value = buffer[5:offset]

	if type_idx == 1:
		return offset, value
	else:
		return offset, json.loads(value.decode('utf-8'))
	
def unpack_values(buffer):
	count = struct.unpack('>b', buffer[0:1])
	values = []

	while len(buffer) > 0:
		offset, value = unpack_value(buffer)
		values.append(value)
		buffer = buffer[offset:]

	return values
	
	
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

	if class_name:
		instance = getattr(module, class_name)()
		functions = [
			(name, getattr(instance, name)) for name
			in dir(instance)
			if callable(getattr(instance, name))
			and not name.startswith('__')
		]
	else:
		functions = [
			(name, func) for name, func
			in inspect.getmembers(module, inspect.isfunction)
		]

	
	
	write_file.write(b'\x01' + pack_value([name for name, _ in functions]))
	write_file.flush()
except Exception as e:
	write_file.write(b'\x00' + pack_value(str(e)))
	write_file.flush()
	exit(1)


while True:
	header = read_file.read(5)
	function_index, length = struct.unpack('>bI', header)
	args = unpack_values(read_file.read(length)) if length > 0 else []

	try:
		result = functions[function_index][1](*args)
		write_file.write(b'\x01' + pack_value(result))
	except Exception as e:
		write_file.write(b'\x00' + pack_value(str(e)))
	finally:
		write_file.flush()