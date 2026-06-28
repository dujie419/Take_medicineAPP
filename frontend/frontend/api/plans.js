import { request } from '@/utils/request.js'

export function getPlans() {
  return request({ url: '/plans' })
}

export function getPlan(planId) {
  return request({ url: `/plans/${planId}` })
}

export function createPlan(data) {
  return request({ url: '/plans', method: 'POST', data })
}

export function updatePlan(planId, data) {
  return request({ url: `/plans/${planId}`, method: 'PATCH', data })
}

export function deletePlan(planId) {
  return request({ url: `/plans/${planId}`, method: 'DELETE' })
}
