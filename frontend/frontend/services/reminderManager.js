import { authStore } from '@/common/api.js'
import { getToday } from '@/api/today.js'

// #ifdef APP-PLUS
import * as reminderPlugin from '@/uni_modules/tm-reminder'
// #endif

const NOTIFICATION_PROMPTED_KEY = 'take_medicine_notification_prompted'
let nativeApi = null

// #ifdef APP-PLUS
nativeApi = reminderPlugin
// #endif

function currentUserId() {
  const user = authStore.getStoredUser()
  return user?.id === undefined || user?.id === null ? '' : String(user.id)
}

function epochMillis(value) {
  if (!value) return 0
  const parsed = new Date(value).getTime()
  return Number.isNaN(parsed) ? 0 : parsed
}

function nativeItems(today) {
  return (today?.items || []).map((item) => {
    const medicine = item.medicines?.[0]
    return {
      groupId: item.reminder_group_id,
      plannedAtEpochMs: epochMillis(medicine?.planned_at),
      snoozeUntilEpochMs: epochMillis(medicine?.snooze_until) || null,
      status: item.status === 'done' ? 'done' : item.status,
      speechText: item.speech_text || '',
      medicineNames: (item.medicines || []).map((value) => value.name).join('、')
    }
  }).filter((item) => item.plannedAtEpochMs > 0)
}

function requestNativePermissions(includeMicrophone) {
  if (!nativeApi) return Promise.resolve(null)
  return new Promise((resolve, reject) => {
    nativeApi.requestPermissions(includeMicrophone, resolve, (message) => {
      reject(new Error(message || '未获得系统权限'))
    })
  })
}

export function isNativeReminderAvailable() {
  return Boolean(nativeApi)
}

export function getReminderPermissionState() {
  if (!nativeApi) {
    return {
      notificationGranted: false,
      microphoneGranted: false,
      exactAlarmGranted: false
    }
  }
  return nativeApi.getPermissionState()
}

export async function syncTodayReminders(today = null, { requestPermission = false } = {}) {
  const userId = currentUserId()
  if (!nativeApi || !userId || !authStore.getToken()) return { scheduled: 0, available: false }

  let permission = nativeApi.getPermissionState()
  const hasItems = Boolean(today?.items?.length)
  const prompted = uni.getStorageSync(NOTIFICATION_PROMPTED_KEY)
  if (
    requestPermission &&
    hasItems &&
    !permission.notificationGranted &&
    !prompted
  ) {
    uni.setStorageSync(NOTIFICATION_PROMPTED_KEY, true)
    try {
      permission = await requestNativePermissions(false)
    } catch (error) {
      uni.showToast({ title: error.message, icon: 'none' })
    }
  }

  const data = today || await getToday()
  const scheduled = nativeApi.scheduleReminders(userId, nativeItems(data))
  return { scheduled, available: true, permission: nativeApi.getPermissionState() }
}

export async function refreshTodayReminders(options = {}) {
  if (!authStore.getToken()) return { scheduled: 0, available: Boolean(nativeApi) }
  const today = await getToday()
  return syncTodayReminders(today, options)
}

export function cancelReminderGroup(groupId) {
  const userId = currentUserId()
  if (nativeApi && userId) nativeApi.cancelReminderGroup(userId, groupId)
}

export function cancelCurrentUserReminders() {
  const userId = currentUserId()
  if (nativeApi && userId) nativeApi.cancelUserReminders(userId)
}

export async function reconcileMedicationAction(groupId, status) {
  if (status === 'taken' || status === 'skipped') {
    cancelReminderGroup(groupId)
    return
  }
  await refreshTodayReminders()
}

export async function startCustomRecording(groupId) {
  const userId = currentUserId()
  if (!nativeApi || !userId) throw new Error('请在 Android App 中使用录音提醒')
  const permission = nativeApi.getPermissionState()
  if (!permission.microphoneGranted) {
    await requestNativePermissions(true)
  }
  return nativeApi.startRecording(userId, groupId)
}

export function stopCustomRecording() {
  if (!nativeApi) return 0
  return nativeApi.stopRecording()
}

export function playCustomRecording(groupId) {
  const userId = currentUserId()
  return Boolean(nativeApi && userId && nativeApi.playRecording(userId, groupId))
}

export function deleteCustomRecording(groupId) {
  const userId = currentUserId()
  return Boolean(nativeApi && userId && nativeApi.deleteRecording(userId, groupId))
}

export function requestExactAlarmPermission() {
  if (!nativeApi) return false
  return nativeApi.requestExactAlarmPermission()
}

export function consumeReminderLaunchRoute() {
  return nativeApi ? nativeApi.getLaunchRoute() : ''
}
