// CoMIT MQTT broker — aedes, zero system install.
// TCP on 1883 (Python services) + WebSocket on 9001 (browser dashboard).
import net from 'node:net'
import http from 'node:http'
import { Aedes } from 'aedes'
import { WebSocketServer, createWebSocketStream } from 'ws'

const aedes = (Aedes.createBroker ? await Aedes.createBroker() : new Aedes())

aedes.on('client', (client) => {
  console.log(`[broker] client connected: ${client.id}`)
})
aedes.on('clientError', (client, err) => {
  console.log(`[broker] clientError ${client?.id}: ${err.message}`)
})
aedes.on('publish', (packet, client) => {
  if (client && packet.topic.startsWith('v2x/')) {
    console.log(`[broker] ${client.id} -> ${packet.topic}`)
  }
})

net.createServer((socket) => aedes.handle(socket)).listen(1883, () =>
  console.log('[broker] MQTT TCP listening on :1883'))

const httpServer = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain' })
  res.end('CoMIT MQTT WebSocket endpoint: ws://localhost:9001\n')
})
const wss = new WebSocketServer({ server: httpServer })
wss.on('connection', (socket, req) => {
  try {
    aedes.handle(createWebSocketStream(socket), req)
  } catch (err) {
    console.log('[broker] ws connection rejected:', err.message)
    socket.close()
  }
})
// never die to malformed handshakes / aborted upgrades
httpServer.on('clientError', (err, socket) => {
  if (socket.writable) socket.end('HTTP/1.1 400 Bad Request\r\n\r\n')
})
wss.on('error', (err) => console.log('[broker] wss error:', err.message))
httpServer.listen(9001, () =>
  console.log('[broker] MQTT WebSocket listening on :9001'))
