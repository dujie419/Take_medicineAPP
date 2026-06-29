import { request } from '@/utils/request.js'

export function getMedicines() {
  return request({ url: '/api/v1/medicines' })
}
