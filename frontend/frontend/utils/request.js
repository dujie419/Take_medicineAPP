const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

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
      success: (response) => {
        if (response.statusCode === 401) {
          uni.removeStorageSync('token')
          uni.removeStorageSync('user')
          reject(new Error('登录已失效，请重新登录'))
          return
        }

        if (response.statusCode < 200 || response.statusCode >= 300) {
          reject(new Error(response.data?.message || response.data?.detail || '请求失败'))
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
      fail: () => reject(new Error('无法连接后端服务，请检查网络和 API 地址'))
    })
  })
}
