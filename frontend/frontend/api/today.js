import { request } from '@/utils/request.js'

export function getToday() {
  return request({ url: '/api/v1/today' })
}

export function updateReminderStatus(reminderGroupId, status) {
  return request({
    url: '/api/v1/medication-logs',
    method: 'POST',
    data: {
      reminder_group_id: reminderGroupId,
      status
    }
  })
}
