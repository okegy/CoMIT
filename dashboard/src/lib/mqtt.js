import { useEffect, useRef, useState, useCallback } from 'react'
import mqtt from 'mqtt'

const DEFAULT_URL = typeof window !== 'undefined' && window.location.protocol === 'https:'
  ? 'wss://broker.emqx.io:8084/mqtt'
  : 'ws://localhost:9001'

const URL = import.meta.env.VITE_MQTT_URL || DEFAULT_URL

export function useMqtt(topics) {
  const clientRef = useRef(null)
  const handlersRef = useRef({})
  const [status, setStatus] = useState('connecting')

  useEffect(() => {
    const client = mqtt.connect(URL, { clientId: 'comit-dashboard-' + Math.random().toString(16).slice(2, 8), reconnectPeriod: 2000 })
    clientRef.current = client
    client.on('connect', () => { setStatus('connected'); client.subscribe(topics) })
    client.on('reconnect', () => setStatus('connecting'))
    client.on('close', () => setStatus('disconnected'))
    client.on('error', () => setStatus('disconnected'))
    client.on('message', (topic, payload) => {
      const h = handlersRef.current[topic]
      if (h) { try { h(topic, JSON.parse(payload.toString())) } catch { /* ignore */ } }
    })
    return () => client.end(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const setHandler = useCallback((topic, fn) => { handlersRef.current[topic] = fn }, [])
  const publish = useCallback((topic, obj) => {
    clientRef.current?.publish(topic, JSON.stringify(obj))
  }, [])

  return { status, setHandler, publish }
}
