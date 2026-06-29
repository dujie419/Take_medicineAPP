import { request } from '@/utils/request.js'

export function getMedicationLogs({ limit = 20, offset = 0 } = {}) {
  return request({
    url: `/api/v1/medication-logs?limit=${limit}&offset=${offset}`
  })
}
