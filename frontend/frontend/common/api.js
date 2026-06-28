const TOKEN_KEY = 'take_medicine_token'
const USER_KEY = 'take_medicine_user'
const BASE_URL_KEY = 'take_medicine_base_url'

const DEFAULT_BASE_URL = 'http://127.0.0.1:8000'

function getBaseUrl() {
  return uni.getStorageSync(BASE_URL_KEY) || DEFAULT_BASE_URL
}

function getToken() {
  return uni.getStorageSync(TOKEN_KEY) || ''
}

function setToken(token) {
  uni.setStorageSync(TOKEN_KEY, token)
}

function getStoredUser() {
  return uni.getStorageSync(USER_KEY) || null
}

function setStoredUser(user) {
  uni.setStorageSync(USER_KEY, user)
}

function clearAuth() {
  uni.removeStorageSync(TOKEN_KEY)
  uni.removeStorageSync(USER_KEY)
}

function request({ url, method = 'GET', data, auth = false }) {
  const headers = {}
  const token = getToken()

  if (auth && token) {
    headers.Authorization = `Bearer ${token}`
  }

  return new Promise((resolve, reject) => {
    uni.request({
      url: `${getBaseUrl()}${url}`,
      method,
      data,
      header: headers,
      success: (response) => {
        const body = response.data || {}
        if (response.statusCode >= 200 && response.statusCode < 300 && body.code === 0) {
          resolve(body.data)
          return
        }

        reject(new Error(body.message || '请求失败'))
      },
      fail: () => {
        reject(new Error('无法连接后端服务'))
      },
    })
  })
}

export function setBaseUrl(baseUrl) {
  uni.setStorageSync(BASE_URL_KEY, baseUrl)
}

export function sendSmsCode(phone) {
  return request({
    url: '/api/v1/auth/sms-codes',
    method: 'POST',
    data: { phone },
  })
}

export async function login(phone, code) {
  const data = await request({
    url: '/api/v1/auth/login',
    method: 'POST',
    data: { phone, code },
  })

  setToken(data.access_token)
  setStoredUser(data.user)
  return data.user
}

export async function fetchCurrentUser() {
  const user = await request({
    url: '/api/v1/auth/me',
    auth: true,
  })

  setStoredUser(user)
  return user
}

export async function updateCurrentUser(payload) {
  const user = await request({
    url: '/api/v1/auth/me',
    method: 'PATCH',
    data: payload,
    auth: true,
  })

  setStoredUser(user)
  return user
}

export function fetchMedicines() {
  return request({
    url: '/api/v1/medicines',
    auth: true,
  })
}

export function createMedicine(payload) {
  return request({
    url: '/api/v1/medicines',
    method: 'POST',
    data: payload,
    auth: true,
  })
}

export function fetchMedicineDetail(id) {
  return request({
    url: `/api/v1/medicines/${id}`,
    auth: true,
  })
}

export const authStore = {
  getBaseUrl,
  getToken,
  getStoredUser,
  clearAuth,
}
