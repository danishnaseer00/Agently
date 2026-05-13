import { uploadFile } from './client.js'

export async function analyzeImageApi(file) {
  try {
    return await uploadFile('/api/images/upload', file)
  } catch {
    return null
  }
}
