import { authStore } from '@/common/api.js'

function errorMessage(data, fallback) {
  if (typeof data?.message === 'string' && data.message) return data.message
  if (typeof data?.detail === 'string' && data.detail) return data.detail
  return fallback
}

function returnToLogin(message = '登录已失效，请重新登录') {
  uni.$emit('take-medicine:auth-clearing')
  authStore.clearAuth()
  uni.showToast({ title: message, icon: 'none' })
  setTimeout(() => {
    uni.reLaunch({ url: '/pages/index/index' })
  }, 500)
}

export function request(options) {
  const token = authStore.getToken()
  if (!token) {
    returnToLogin('请先登录')
    return Promise.reject(new Error('请先登录'))
  }

  const headers = {
    'Content-Type': 'application/json',
    ...(options.header || {})
  }
  headers.Authorization = `Bearer ${token}`

  return new Promise((resolve, reject) => {
    uni.request({
      url: `${authStore.getBaseUrl().replace(/\/$/, '')}${options.url}`,
      method: options.method || 'GET',
      data: options.data,
      header: headers,
      timeout: options.timeout || 15000,
      success: (response) => {
        if (response.statusCode === 401) {
          returnToLogin()
          reject(new Error('登录已失效，请重新登录'))
          return
        }

        if (response.statusCode < 200 || response.statusCode >= 300) {
          reject(new Error(errorMessage(response.data, `请求失败（${response.statusCode}）`)))
          return
        }

        if (response.data && typeof response.data.code !== 'undefined') {
          if (response.data.code !== 0) {
            reject(new Error(response.data.message || '请求失败'))
            return
          }
          resolve(response.data.data)
          return
        }

        resolve(response.data)
      },
      fail: (error) => {
        const message = error?.errMsg?.includes('timeout')
          ? '请求超时，请检查网络后重试'
          : '无法连接后端服务，请检查网络和 API 地址'
        reject(new Error(message))
      }
    })
  })
}
