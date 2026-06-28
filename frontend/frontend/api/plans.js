import { request } from '@/utils/request.js'

export function getPlans() {
  return request({ url: '/api/v1/plans' })
}

export function getPlan(planId) {
  return request({ url: `/api/v1/plans/${planId}` })
}

export function createPlan(data) {
  return request({ url: '/api/v1/plans', method: 'POST', data })
}

export function updatePlan(planId, data) {
  return request({ url: `/api/v1/plans/${planId}`, method: 'PATCH', data })
}

export function deletePlan(planId) {
  return request({ url: `/api/v1/plans/${planId}`, method: 'DELETE' })
}
