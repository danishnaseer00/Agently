/**
 * Parse a raw SSE payload string into event name and data.
 */
export function parseSsePayload(text) {
  const lines = text.split('\n')
  let event = 'message'
  let data = ''
  for (const line of lines) {
    if (line.startsWith('event:')) event = line.replace('event:', '').trim()
    if (line.startsWith('data:')) data += line.replace('data:', '').trim()
  }
  return { event, data }
}
