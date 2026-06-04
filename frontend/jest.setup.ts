import '@testing-library/jest-dom'
import { ReadableStream } from 'stream/web'
import { TextEncoder, TextDecoder } from 'util'

if (typeof global.TextEncoder === 'undefined') {
  global.TextEncoder = TextEncoder
}
if (typeof global.TextDecoder === 'undefined') {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  global.TextDecoder = TextDecoder as any
}
if (typeof global.ReadableStream === 'undefined') {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  global.ReadableStream = ReadableStream as any
}

import crypto from 'crypto'
const webCrypto = (crypto.webcrypto || crypto) as any
Object.defineProperty(global, 'crypto', {
  value: webCrypto,
  writable: true,
  configurable: true,
})
if (typeof window !== 'undefined') {
  Object.defineProperty(window, 'crypto', {
    value: webCrypto,
    writable: true,
    configurable: true,
  })
}
