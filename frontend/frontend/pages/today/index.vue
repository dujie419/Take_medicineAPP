<template>
  <view class="page">
    <app-nav active="today" />
    <view class="hero">
      <text class="greeting">{{ greetingText }}</text>
      <text class="date">{{ dateText }}</text>
      <view class="voice-state">
        <text>语音提醒</text>
        <text class="voice-note" @click="openExactAlarmSettings">{{ voiceNote }}</text>
      </view>
      <button class="history-button" size="mini" @click="openHistory">查看服药记录</button>
    </view>

    <view v-if="loading" class="state-card">
      <text>正在整理今天的提醒...</text>
    </view>

    <view v-else-if="errorMessage" class="state-card error-card">
      <text class="state-title">暂时无法加载今日提醒</text>
      <text class="state-text">{{ errorMessage }}</text>
      <button class="retry-button" size="mini" @click="loadToday">重新加载</button>
    </view>

    <template v-else>
      <view class="summary-card">
        <view class="summary-row">
          <view>
            <text class="summary-number">{{ summary.done }}/{{ summary.total }}</text>
            <text class="summary-label">今日已处理</text>
          </view>
          <view class="summary-detail">
            <text>待处理 {{ summary.pending }}</text>
          </view>
        </view>
        <view class="progress-track">
          <view class="progress-value" :style="{ width: `${progress}%` }"></view>
        </view>
      </view>

      <view v-if="items.length === 0" class="state-card">
        <text class="state-title">今天没有用药提醒</text>
        <text class="state-text">可以在用药计划中新增或启用提醒。</text>
        <button class="retry-button" size="mini" @click="goPlans">查看用药计划</button>
      </view>

      <view v-else class="reminder-list">
        <view v-for="item in items" :key="item.reminder_group_id" class="reminder-card">
          <view class="reminder-header">
            <view>
              <text class="reminder-time">{{ item.time }}</text>
              <text class="period">{{ item.period }}</text>
            </view>
            <text :class="['status-badge', item.status]">{{ groupStatusText(item) }}</text>
          </view>

          <view class="medicine-list">
            <view v-for="medicine in item.medicines" :key="medicine.plan_id" class="medicine-row">
              <view>
                <text class="medicine-name">{{ medicine.name }}</text>
                <text class="dose">每次 {{ medicine.dosage }}</text>
              </view>
              <text :class="['medicine-status', medicine.status]">
                {{ medicineStatusText(medicine) }}
              </text>
            </view>
          </view>

          <view class="speech-box">
            <text class="speech-label">播报文案</text>
            <text class="speech-text">{{ item.speech_text }}</text>
          </view>

          <view class="record-actions">
            <button
              v-if="recordingGroupId !== item.reminder_group_id"
              class="record-button"
              size="mini"
              @click="startRecording(item)"
            >
              录制提醒音
            </button>
            <button
              v-else
              class="record-button recording"
              size="mini"
              @click="stopRecording(item)"
            >
              停止录音
            </button>
            <button class="record-button" size="mini" @click="playRecording(item)">试听</button>
            <button class="record-button danger" size="mini" @click="removeRecording(item)">删除录音</button>
          </view>

          <view v-if="item.status !== 'done'" class="actions">
            <button
              class="action-button taken-button"
              size="mini"
              :disabled="isBusy(item)"
              @click="confirmAction(item, 'taken')"
            >
              已服用
            </button>
            <button
              class="action-button skip-button"
              size="mini"
              :disabled="isBusy(item)"
              @click="confirmAction(item, 'skipped')"
            >
              跳过本次
            </button>
            <button
              class="action-button snooze-button"
              size="mini"
              :loading="isBusy(item)"
              :disabled="isBusy(item)"
              @click="snooze(item)"
            >
              5分钟后提醒
            </button>
          </view>
        </view>
      </view>
    </template>
  </view>
</template>

<script>
import AppNav from '@/components/AppNav.vue'
import { getToday, updateReminderStatus } from '@/api/today.js'
import {
  deleteCustomRecording,
  getReminderPermissionState,
  isNativeReminderAvailable,
  playCustomRecording,
  reconcileMedicationAction,
  requestExactAlarmPermission,
  startCustomRecording,
  stopCustomRecording,
  syncTodayReminders
} from '@/services/reminderManager.js'

export default {
  components: { AppNav },
  data() {
    return {
      today: null,
      loading: false,
      errorMessage: '',
      busyGroupId: '',
      recordingGroupId: '',
      permissionState: null
    }
  },
  computed: {
    summary() {
      return this.today?.summary || { total: 0, done: 0, pending: 0 }
    },
    items() {
      return this.today?.items || []
    },
    progress() {
      return this.summary.total ? Math.round((this.summary.done / this.summary.total) * 100) : 0
    },
    greetingText() {
      if (!this.today) return '今日提醒'
      return `${this.today.greeting}，${this.today.nickname}`
    },
    dateText() {
      if (!this.today?.date) return ''
      const parts = this.today.date.split('-')
      return `${parts[0]}年${Number(parts[1])}月${Number(parts[2])}日`
    },
    voiceNote() {
      if (!isNativeReminderAvailable()) return '请使用 Android App'
      if (!this.permissionState?.notificationGranted) return '通知权限未开启'
      if (!this.permissionState?.exactAlarmGranted) return '提醒可能延迟，点此设置'
      return '通知、震动和语音已开启'
    }
  },
  onShow() {
    this.loadToday()
  },
  onPullDownRefresh() {
    this.loadToday().finally(() => uni.stopPullDownRefresh())
  },
  methods: {
    async loadToday() {
      this.loading = true
      this.errorMessage = ''
      try {
        const data = await getToday()
        this.today = data
        try {
          const result = await syncTodayReminders(data, { requestPermission: true })
          this.permissionState = result.permission || getReminderPermissionState()
        } catch (reminderError) {
          this.permissionState = getReminderPermissionState()
          console.warn('同步本地提醒失败', reminderError)
          uni.showToast({ title: '今日计划已加载，本地提醒同步失败', icon: 'none' })
        }
      } catch (error) {
        this.errorMessage = error.message || '加载失败'
      } finally {
        this.loading = false
      }
    },
    isBusy(item) {
      return this.busyGroupId === item.reminder_group_id
    },
    medicineNames(item) {
      return item.medicines.map((medicine) => medicine.name).join('、')
    },
    confirmAction(item, status) {
      const isTaken = status === 'taken'
      uni.showModal({
        title: isTaken ? '确认已服用' : '确认跳过本次',
        content: `${isTaken ? '确认已经服用' : '确认本次不服用'}：${this.medicineNames(item)}？`,
        confirmColor: isTaken ? '#2f80ed' : '#d97706',
        success: async (result) => {
          if (result.confirm) await this.submitAction(item, status)
        }
      })
    },
    async snooze(item) {
      await this.submitAction(item, 'snoozed')
    },
    async submitAction(item, status) {
      if (this.busyGroupId) return
      this.busyGroupId = item.reminder_group_id
      try {
        await updateReminderStatus(item.reminder_group_id, status)
        await reconcileMedicationAction(item.reminder_group_id, status)
        const messages = {
          taken: '已记录服用',
          skipped: '已跳过本次',
          snoozed: '将在5分钟后提醒'
        }
        uni.showToast({ title: messages[status], icon: 'none' })
        await this.loadToday()
      } catch (error) {
        uni.showToast({ title: error.message || '操作失败', icon: 'none' })
      } finally {
        this.busyGroupId = ''
      }
    },
    groupStatusText(item) {
      if (item.status === 'done') return '已处理'
      if (item.status === 'snoozed') return '稍后提醒'
      return '待处理'
    },
    medicineStatusText(medicine) {
      const labels = {
        pending: '待处理',
        taken: '已服用',
        skipped: '已跳过',
        snoozed: '稍后提醒'
      }
      return labels[medicine.status] || '待处理'
    },
    goPlans() {
      uni.navigateBack()
    },
    openHistory() {
      uni.navigateTo({ url: '/pages/medication-logs/index' })
    },
    openExactAlarmSettings() {
      if (!isNativeReminderAvailable()) {
        uni.showToast({ title: '请在 Android App 中使用提醒功能', icon: 'none' })
        return
      }
      if (!this.permissionState?.exactAlarmGranted) {
        requestExactAlarmPermission()
      }
    },
    async startRecording(item) {
      if (this.recordingGroupId) return
      try {
        await startCustomRecording(item.reminder_group_id)
        this.recordingGroupId = item.reminder_group_id
        this.permissionState = getReminderPermissionState()
        uni.showToast({ title: '开始录音', icon: 'none' })
      } catch (error) {
        uni.showToast({ title: error.message || '无法开始录音', icon: 'none' })
      }
    },
    stopRecording(item) {
      if (this.recordingGroupId !== item.reminder_group_id) return
      try {
        const duration = stopCustomRecording()
        uni.showToast({
          title: duration < 1000 ? '录音过短，请重新录制' : '录音已保存',
          icon: 'none'
        })
      } catch (error) {
        uni.showToast({ title: error.message || '录音保存失败', icon: 'none' })
      } finally {
        this.recordingGroupId = ''
      }
    },
    playRecording(item) {
      if (!playCustomRecording(item.reminder_group_id)) {
        uni.showToast({ title: '还没有可试听的自定义录音', icon: 'none' })
      }
    },
    removeRecording(item) {
      if (deleteCustomRecording(item.reminder_group_id)) {
        uni.showToast({ title: '已恢复系统语音', icon: 'none' })
      } else {
        uni.showToast({ title: '删除录音失败', icon: 'none' })
      }
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 32rpx 28rpx 64rpx;
  box-sizing: border-box;
  background: #f5f7fb;
}

.hero {
  margin-bottom: 24rpx;
  padding: 34rpx;
  border-radius: 28rpx;
  color: #fff;
  background: linear-gradient(135deg, #2f80ed, #56a5ef);
}

.greeting,
.date,
.summary-number,
.summary-label,
.state-title,
.state-text,
.reminder-time,
.period,
.medicine-name,
.dose,
.speech-label,
.speech-text {
  display: block;
}

.greeting {
  font-size: 40rpx;
  font-weight: 700;
}

.date {
  margin-top: 10rpx;
  font-size: 26rpx;
  opacity: 0.9;
}

.voice-state {
  display: flex;
  justify-content: space-between;
  margin-top: 28rpx;
  padding-top: 22rpx;
  border-top: 1rpx solid rgba(255, 255, 255, 0.24);
  font-size: 24rpx;
}

.voice-note {
  opacity: 0.84;
}

.history-button {
  margin: 24rpx 0 0;
  color: #fff;
  border: 1rpx solid rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.12);
}

.state-card,
.summary-card,
.reminder-card {
  margin-bottom: 22rpx;
  padding: 30rpx;
  border-radius: 24rpx;
  background: #fff;
  box-shadow: 0 8rpx 28rpx rgba(31, 52, 85, 0.06);
}

.state-card {
  text-align: center;
}

.error-card {
  border: 1rpx solid #f3c8c8;
}

.state-title {
  margin-bottom: 12rpx;
  color: #27364b;
  font-size: 32rpx;
  font-weight: 600;
}

.state-text {
  margin-bottom: 22rpx;
  color: #7b8798;
  font-size: 26rpx;
}

.retry-button {
  color: #2f80ed;
}

.summary-row,
.reminder-header,
.medicine-row,
.actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.record-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 18rpx;
}

.record-button {
  margin: 0;
  color: #4969a8;
  border: 1rpx solid #c8d5f0;
  background: #f5f8ff;
  font-size: 22rpx;
}

.record-button.recording {
  color: #fff;
  background: #d64545;
}

.record-button.danger {
  color: #b83b3b;
  border-color: #efc4c4;
  background: #fff5f5;
}

.summary-number {
  color: #1f3552;
  font-size: 44rpx;
  font-weight: 700;
}

.summary-label,
.summary-detail {
  color: #7b8798;
  font-size: 24rpx;
}

.progress-track {
  height: 14rpx;
  margin-top: 24rpx;
  overflow: hidden;
  border-radius: 8rpx;
  background: #e8eef6;
}

.progress-value {
  height: 100%;
  border-radius: 8rpx;
  background: #34a66f;
  transition: width 0.2s ease;
}

.reminder-time {
  color: #1f3552;
  font-size: 42rpx;
  font-weight: 700;
}

.period {
  margin-top: 4rpx;
  color: #7b8798;
  font-size: 24rpx;
}

.status-badge {
  padding: 9rpx 18rpx;
  border-radius: 24rpx;
  color: #b45309;
  background: #fff4d6;
  font-size: 24rpx;
}

.status-badge.done {
  color: #217a50;
  background: #e5f7ee;
}

.status-badge.snoozed {
  color: #4969a8;
  background: #eaf0ff;
}

.medicine-list {
  margin: 24rpx 0;
  border-top: 1rpx solid #edf0f4;
}

.medicine-row {
  padding: 22rpx 0;
  border-bottom: 1rpx solid #edf0f4;
}

.medicine-name {
  color: #27364b;
  font-size: 30rpx;
  font-weight: 600;
}

.dose {
  margin-top: 5rpx;
  color: #7b8798;
  font-size: 24rpx;
}

.medicine-status {
  color: #b45309;
  font-size: 24rpx;
}

.medicine-status.taken {
  color: #217a50;
}

.medicine-status.skipped {
  color: #8a5a44;
}

.medicine-status.snoozed {
  color: #4969a8;
}

.speech-box {
  padding: 20rpx;
  border-radius: 18rpx;
  background: #f4f8fd;
}

.speech-label {
  margin-bottom: 8rpx;
  color: #68819f;
  font-size: 22rpx;
}

.speech-text {
  color: #40536b;
  font-size: 26rpx;
  line-height: 1.6;
}

.actions {
  gap: 12rpx;
  margin-top: 24rpx;
}

.action-button {
  flex: 1;
  margin: 0;
  padding: 0 8rpx;
  font-size: 23rpx;
}

.taken-button {
  color: #fff;
  background: #2f80ed;
}

.skip-button {
  color: #9a5b08;
  border: 1rpx solid #efd39e;
  background: #fffaf0;
}

.snooze-button {
  color: #4969a8;
  border: 1rpx solid #c8d5f0;
  background: #f5f8ff;
}
</style>
