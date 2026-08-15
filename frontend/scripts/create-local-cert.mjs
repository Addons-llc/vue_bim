import { execFileSync, spawnSync } from 'node:child_process'
import { existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { networkInterfaces } from 'node:os'
import { resolve } from 'node:path'

const certDir = resolve('.cert')
const keyPath = resolve(certDir, 'localhost-key.pem')
const certPath = resolve(certDir, 'localhost-cert.pem')
const configPath = resolve(certDir, 'localhost-openssl.cnf')

function getLocalIpAddresses() {
  return Object.values(networkInterfaces())
    .flat()
    .filter((network) => network && network.family === 'IPv4' && !network.internal)
    .map((network) => network.address)
}

if (existsSync(keyPath) && existsSync(certPath)) {
  process.exit(0)
}

mkdirSync(certDir, { recursive: true })

const ipAddresses = ['127.0.0.1', ...getLocalIpAddresses()]

function hasCommand(command) {
  return spawnSync('sh', ['-c', `command -v ${command}`], { stdio: 'ignore' }).status === 0
}

if (hasCommand('mkcert')) {
  try {
    execFileSync('mkcert', ['-install'], { stdio: 'inherit' })
  } catch {
    console.error('\nUnable to install the mkcert local CA automatically.')
    console.error('Run `mkcert -install` in your terminal, enter your Mac password, then run `npm run dev:https` again.\n')
    process.exit(1)
  }

  execFileSync('mkcert', [
    '-key-file',
    keyPath,
    '-cert-file',
    certPath,
    'localhost',
    ...ipAddresses,
  ], { stdio: 'inherit' })
  process.exit(0)
}

const altNames = [
  'DNS.1 = localhost',
  ...ipAddresses.map((address, index) => `IP.${index + 1} = ${address}`),
]

writeFileSync(
  configPath,
  `[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
x509_extensions = v3_req

[dn]
CN = localhost

[v3_req]
subjectAltName = @alt_names

[alt_names]
${altNames.join('\n')}
`,
)

execFileSync('openssl', [
  'req',
  '-x509',
  '-newkey',
  'rsa:2048',
  '-nodes',
  '-sha256',
  '-days',
  '365',
  '-keyout',
  keyPath,
  '-out',
  certPath,
  '-config',
  configPath,
], { stdio: 'inherit' })
