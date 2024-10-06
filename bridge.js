import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { spawn } from 'child_process'


const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

export default function createPythonBridge({ file, env = process.env, python = 'python3', stdio = 'inherit' }){
	let queue = []
	let process = spawn(
		python,
		[path.join(__dirname, 'bridge.py'), file],
		{
			stdio: [stdio, stdio, stdio, 'pipe', 'pipe'],
			env,
		}
	)

	let [ writeStream, readStream ] = process.stdio.slice(3)
	let readBuffer = Buffer.alloc(0)

	readStream.on('data', data => {
		readBuffer = Buffer.concat([readBuffer, data])

		while(readBuffer.length >= 6){
			let responseType = readBuffer.readUint8(0)
			let dataType = readBuffer.readUint8(1)
			let length = readBuffer.readUInt32BE(2)

            if (readBuffer.length < 6 + length)
				return

			let payload = readBuffer.slice(6, 6 + length)
			let data = dataType === 1
				? payload
				: JSON.parse(payload)

			readBuffer = readBuffer.slice(6 + length)

			let { resolve, reject } = queue.shift()

			if(responseType === 1)
				resolve(data)
			else
				reject(data)
		}
	})

	function callPy(functionIndex, value){
		let data
		let dataType

		if(value instanceof Buffer){
			dataType = 1
			data = value
		}else{
			dataType = 0
			data = Buffer.from(JSON.stringify(value), 'utf8')
		}

		let header = Buffer.alloc(5)

		header.writeUint8(functionIndex)
		header.writeUint32BE(data.length)

		writeStream.write(header)
		writeStream.write(data)
	}

	process.on('error', error => reject(error))
	
	return new Promise((res, rej) => {
		let resolve = functionNames => {
			let functions = {}

			for(let name of functionNames){
				functions[name] = async value => {
					callPy(functionNames.indexOf(name), value)

					return await new Promise((resolve, reject) => {
						queue.push({
							resolve,
							reject: message => reject(
								new Error(`Error across bridge: ${message}`)
							)
						})
					})
				}
			}

			res({ process, functions })
		}

		let reject = message => {
			rej(new Error(`Failed to initialize bridge: ${message}`))
		}

		queue.push({ resolve, reject })
	})
}