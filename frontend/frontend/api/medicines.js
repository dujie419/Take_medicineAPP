import { request } from '@/utils/request.js'

export function getMedicines() {
  return request({ url: '/medicines' })
}
