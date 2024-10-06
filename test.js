import createPythonBridge from './bridge.js'

let { process, functions } = await createPythonBridge({ file: './test.py' })

console.log(functions)
console.log(await functions.hello())
console.log(await functions.foo(3))
console.log(await functions.binary(Buffer.alloc(3)))