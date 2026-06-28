const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

function errorMessage(data, fallback) {
  if (typeof data?.message === 'string' && data.message) return data.message
  if (typeof data?.detail === 'string' && data.detail) return data.detail
  return fallback
}

export function request(options) {
  if (!API_BASE_URL) {
    return Promise.reject(new Error('未配置 VITE_API_BASE_URL，请先设置后端服务地址'))
  }

  const token = uni.getStorageSync('token')
  const headers = {
    'Content-Type': 'application/json',
    ...(options.header || {})
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE_URL}${options.url}`,
      method: options.method || 'GET',
      data: options.data,
      header: headers,
      timeout: options.timeout || 15000,
      success: (response) => {
        if (response.statusCode === 401) {
          uni.removeStorageSync('token')
          uni.removeStorageSync('user')
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
