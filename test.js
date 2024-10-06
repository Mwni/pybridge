import createPythonBridge from './bridge.js'

{
	let { process, functions } = await createPythonBridge({ file: './test.py' })

	console.log(functions)
	console.log(await functions.hello())
	console.log(await functions.foo(3))
	console.log(await functions.binary(Buffer.alloc(3)))

	process.kill()
}

{
	let { process, functions } = await createPythonBridge({ file: './test.py', className: 'Test' })

	console.log(functions)
	console.log(await functions.do_thing())

	process.kill()
}