<template>
  <view class="page">
    <view class="header">
      <view>
        <text class="title">用药计划</text>
        <text class="subtitle">安排每天的服药时间</text>
      </view>
      <button class="add-button" size="mini" @click="openCreate">新增计划</button>
    </view>

    <view v-if="loading" class="state-card">
      <text>正在加载计划...</text>
    </view>

    <view v-else-if="errorMessage" class="state-card error-card">
      <text class="state-title">暂时无法加载</text>
      <text class="state-text">{{ errorMessage }}</text>
      <button class="retry-button" size="mini" @click="loadPlans">重新加载</button>
    </view>

    <view v-else-if="plans.length === 0" class="state-card">
      <text class="state-title">还没有用药计划</text>
      <text class="state-text">请先添加药品，再为药品设置提醒时间。</text>
      <button class="primary-button" size="mini" @click="openCreate">创建第一个计划</button>
    </view>

    <view v-else class="plan-list">
      <view v-for="plan in plans" :key="plan.id" class="plan-card">
        <view class="plan-top">
          <view>
            <text class="medicine-name">{{ plan.medicine?.name || '未命名药品' }}</text>
            <text v-if="plan.medicine?.specification" class="specification">
              {{ plan.medicine.specification }}
            </text>
          </view>
          <switch
            :checked="plan.is_enabled"
            color="#2f80ed"
            @change="togglePlan(plan, $event)"
          />
        </view>

        <view class="dose-row">
          <text class="label">每次</text>
          <text class="value">{{ plan.dose }}</text>
        </view>

        <view class="time-list">
          <text v-for="item in plan.reminder_times" :key="item" class="time-chip">
            {{ item }}
          </text>
        </view>

        <view class="meta-row">
          <text>{{ formatDateRange(plan) }}</text>
          <text>{{ plan.is_enabled ? '提醒中' : '已暂停' }}</text>
        </view>

        <view class="actions">
          <button class="text-button" size="mini" @click="openEdit(plan.id)">编辑</button>
          <button class="text-button danger" size="mini" @click="confirmDelete(plan)">
            删除
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { deletePlan, getPlans, updatePlan } from '@/api/plans.js'

export default {
  data() {
    return {
      plans: [],
      loading: false,
      errorMessage: ''
    }
  },
  onShow() {
    this.loadPlans()
  },
  onPullDownRefresh() {
    this.loadPlans().finally(() => uni.stopPullDownRefresh())
  },
  methods: {
    async loadPlans() {
      this.loading = true
      this.errorMessage = ''
      try {
        const data = await getPlans()
        this.plans = Array.isArray(data) ? data : (data?.items || [])
      } catch (error) {
        this.errorMessage = error.message || '加载失败'
      } finally {
        this.loading = false
      }
    },
    openCreate() {
      uni.navigateTo({ url: '/pages/plans/form' })
    },
    openEdit(planId) {
      uni.navigateTo({ url: `/pages/plans/form?id=${planId}` })
    },
    async togglePlan(plan, event) {
      const previousValue = plan.is_enabled
      const nextValue = event.detail.value
      plan.is_enabled = nextValue
      try {
        await updatePlan(plan.id, { is_enabled: nextValue })
        uni.showToast({ title: nextValue ? '计划已启用' : '计划已暂停', icon: 'none' })
      } catch (error) {
        plan.is_enabled = previousValue
        uni.showToast({ title: error.message || '操作失败', icon: 'none' })
      }
    },
    confirmDelete(plan) {
      uni.showModal({
        title: '删除用药计划',
        content: `确认删除“${plan.medicine?.name || '该药品'}”的计划吗？`,
        confirmColor: '#d64545',
        success: async (result) => {
          if (!result.confirm) return
          try {
            await deletePlan(plan.id)
            uni.showToast({ title: '已删除', icon: 'success' })
            await this.loadPlans()
          } catch (error) {
            uni.showToast({ title: error.message || '删除失败', icon: 'none' })
          }
        }
      })
    },
    formatDateRange(plan) {
      return `${plan.start_date} 至 ${plan.end_date || '长期'}`
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 36rpx 28rpx 60rpx;
  box-sizing: border-box;
  background: #f5f7fb;
}

.header,
.plan-top,
.meta-row,
.actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header {
  margin-bottom: 28rpx;
}

.title,
.subtitle,
.medicine-name,
.specification,
.state-title,
.state-text {
  display: block;
}

.title {
  color: #1e2a3a;
  font-size: 44rpx;
  font-weight: 700;
}

.subtitle {
  margin-top: 8rpx;
  color: #7b8798;
  font-size: 26rpx;
}

.add-button,
.primary-button {
  color: #fff;
  border: 0;
  background: #2f80ed;
}

.state-card,
.plan-card {
  padding: 32rpx;
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
  margin-bottom: 24rpx;
  color: #7b8798;
  font-size: 26rpx;
}

.retry-button {
  color: #2f80ed;
}

.plan-card {
  margin-bottom: 22rpx;
}

.medicine-name {
  color: #25344a;
  font-size: 34rpx;
  font-weight: 600;
}

.specification {
  margin-top: 6rpx;
  color: #8a95a5;
  font-size: 24rpx;
}

.dose-row {
  margin-top: 24rpx;
}

.label {
  margin-right: 16rpx;
  color: #8a95a5;
}

.value {
  color: #35445a;
}

.time-list {
  margin: 22rpx 0;
}

.time-chip {
  display: inline-block;
  margin: 0 12rpx 12rpx 0;
  padding: 10rpx 20rpx;
  color: #2469bd;
  border-radius: 28rpx;
  background: #eaf3ff;
  font-weight: 600;
}

.meta-row {
  padding-top: 18rpx;
  color: #7b8798;
  border-top: 1rpx solid #edf0f4;
  font-size: 24rpx;
}

.actions {
  justify-content: flex-end;
  margin-top: 20rpx;
}

.text-button {
  margin: 0 0 0 18rpx;
  color: #2f80ed;
  border: 0;
  background: transparent;
}

.danger {
  color: #d64545;
}
</style>
