<template>
  <view class="page">
    <app-nav active="" />
    <view class="header">
      <view>
        <text class="title">服药记录</text>
        <text class="subtitle">按计划服药时间倒序展示</text>
      </view>
      <text class="total">共 {{ total }} 条</text>
    </view>

    <view v-if="loading && items.length === 0" class="state-card">正在加载...</view>
    <view v-else-if="errorMessage && items.length === 0" class="state-card error-card">
      <text>{{ errorMessage }}</text>
      <button size="mini" @click="reload">重新加载</button>
    </view>
    <view v-else-if="items.length === 0" class="state-card">
      <text class="state-title">还没有服药记录</text>
      <text class="state-text">在“今日提醒”中确认服药后，记录会显示在这里。</text>
    </view>

    <view v-else>
      <view v-for="item in items" :key="item.id" class="log-card">
        <view class="log-head">
          <view>
            <text class="medicine-name">{{ item.medicine_name }}</text>
            <text class="dose">每次 {{ item.dose }}</text>
          </view>
          <text :class="['status', item.status]">{{ statusText(item.status) }}</text>
        </view>
        <view class="time-row">
          <text>计划时间</text>
          <text>{{ formatDateTime(item.planned_at) }}</text>
        </view>
        <view v-if="item.actual_at" class="time-row">
          <text>确认时间</text>
          <text>{{ formatDateTime(item.actual_at) }}</text>
        </view>
        <view v-if="item.status === 'snoozed' && item.snooze_until" class="time-row">
          <text>稍后提醒</text>
          <text>{{ formatDateTime(item.snooze_until) }}</text>
        </view>
      </view>

      <button
        v-if="items.length < total"
        class="load-more"
        :loading="loading"
        :disabled="loading"
        @click="loadMore"
      >
        加载更多
      </button>
    </view>
  </view>
</template>

<script>
import AppNav from '@/components/AppNav.vue'
import { getMedicationLogs } from '@/api/medicationLogs.js'

const PAGE_SIZE = 20

export default {
  components: { AppNav },
  data() {
    return {
      items: [],
      total: 0,
      loading: false,
      errorMessage: ''
    }
  },
  onShow() {
    this.reload()
  },
  onPullDownRefresh() {
    this.reload().finally(() => uni.stopPullDownRefresh())
  },
  methods: {
    async reload() {
      this.items = []
      this.total = 0
      await this.loadPage(0)
    },
    async loadMore() {
      await this.loadPage(this.items.length)
    },
    async loadPage(offset) {
      if (this.loading) return
      this.loading = true
      this.errorMessage = ''
      try {
        const data = await getMedicationLogs({ limit: PAGE_SIZE, offset })
        this.items = offset === 0 ? data.items : this.items.concat(data.items)
        this.total = data.total
      } catch (error) {
        this.errorMessage = error.message || '加载服药记录失败'
        if (offset > 0) {
          uni.showToast({ title: this.errorMessage, icon: 'none' })
        }
      } finally {
        this.loading = false
      }
    },
    statusText(status) {
      return {
        taken: '已服用',
        skipped: '已跳过',
        snoozed: '稍后提醒'
      }[status] || status
    },
    formatDateTime(value) {
      if (!value) return '--'
      const date = new Date(value)
      if (Number.isNaN(date.getTime())) return value
      const pad = (part) => String(part).padStart(2, '0')
      return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
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

.header,
.log-head,
.time-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header {
  margin-bottom: 26rpx;
}

.title,
.subtitle,
.medicine-name,
.dose,
.state-title,
.state-text {
  display: block;
}

.title {
  color: #1e2a3a;
  font-size: 42rpx;
  font-weight: 700;
}

.subtitle,
.total,
.dose,
.time-row,
.state-text {
  color: #7b8798;
  font-size: 24rpx;
}

.subtitle,
.dose {
  margin-top: 8rpx;
}

.state-card,
.log-card {
  margin-bottom: 22rpx;
  padding: 30rpx;
  border-radius: 24rpx;
  background: #fff;
  box-shadow: 0 8rpx 28rpx rgba(31, 52, 85, 0.06);
}

.state-card {
  text-align: center;
}

.state-title {
  margin-bottom: 12rpx;
  font-size: 30rpx;
  font-weight: 600;
}

.medicine-name {
  color: #27364b;
  font-size: 32rpx;
  font-weight: 600;
}

.status {
  padding: 9rpx 18rpx;
  border-radius: 22rpx;
  color: #217a50;
  background: #e5f7ee;
  font-size: 24rpx;
}

.status.skipped {
  color: #8a5a44;
  background: #f8eee8;
}

.status.snoozed {
  color: #4969a8;
  background: #eaf0ff;
}

.time-row {
  margin-top: 20rpx;
  padding-top: 18rpx;
  border-top: 1rpx solid #edf0f4;
}

.load-more {
  color: #2f80ed;
  background: #fff;
}
</style>
