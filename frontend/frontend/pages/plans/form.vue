<template>
  <view class="page">
    <app-nav active="plans" />
    <view v-if="loading" class="state-card">正在加载...</view>

    <view v-else>
      <view v-if="loadError" class="error-banner">
        <text>{{ loadError }}</text>
        <button class="retry-button" size="mini" @click="initialize">重新加载</button>
      </view>

      <view v-if="!loadError && medicines.length === 0" class="empty-card">
        <text class="empty-title">还没有可选择的药品</text>
        <text class="empty-text">请先添加药品，再回来设置用药计划。</text>
        <button class="create-medicine-button" @click="goCreateMedicine">去添加药品</button>
      </view>

      <template v-if="medicines.length > 0">
      <view class="form-card">
        <text class="section-title">药品与剂量</text>

        <view class="field" @click="chooseMedicine">
          <text class="field-label">选择药品</text>
          <text :class="['field-value', { placeholder: !selectedMedicine }]">
            {{ selectedMedicine ? medicineLabel(selectedMedicine) : '请选择已有药品' }}
          </text>
        </view>

        <view class="field">
          <text class="field-label">每次剂量</text>
          <input v-model="form.dose" class="input" maxlength="100" placeholder="例如：1片" />
        </view>
      </view>

      <view class="form-card">
        <text class="section-title">计划日期</text>

        <picker mode="date" :value="form.start_date" @change="setStartDate">
          <view class="field">
            <text class="field-label">开始日期</text>
            <text class="field-value">{{ form.start_date || '请选择' }}</text>
          </view>
        </picker>

        <picker mode="date" :value="form.end_date" @change="setEndDate">
          <view class="field">
            <text class="field-label">结束日期</text>
            <text class="field-value">{{ form.end_date || '长期有效' }}</text>
          </view>
        </picker>

        <button v-if="form.end_date" class="clear-button" size="mini" @click="form.end_date = ''">
          清除结束日期
        </button>
      </view>

      <view class="form-card">
        <view class="section-row">
          <text class="section-title">提醒时间</text>
          <button class="add-time-button" size="mini" @click="addReminder">添加</button>
        </view>

        <view
          v-for="(item, index) in form.reminder_times"
          :key="`${item}-${index}`"
          class="time-row"
        >
          <picker mode="time" :value="item" @change="setReminderTime(index, $event)">
            <view class="time-value">{{ item }}</view>
          </picker>
          <button
            class="remove-button"
            size="mini"
            :disabled="form.reminder_times.length === 1"
            @click="removeReminder(index)"
          >
            删除
          </button>
        </view>
      </view>

      <view class="form-card">
        <text class="section-title">其他设置</text>
        <textarea
          v-model="form.remark"
          class="textarea"
          maxlength="500"
          placeholder="选填，例如：饭后服用"
        />
        <view class="switch-row">
          <text>启用计划</text>
          <switch :checked="form.is_enabled" color="#2f80ed" @change="setEnabled" />
        </view>
      </view>

      <view class="safety-notice">
        本 App 仅用于用药信息管理和提醒，请以医生处方、药品包装和说明书为准。
      </view>

      <button
        class="submit-button"
        :loading="submitting"
        :disabled="submitting || Boolean(loadError)"
        @click="submit"
      >
        {{ isEditing ? '保存修改' : '创建计划' }}
      </button>
      </template>
    </view>
  </view>
</template>

<script>
import AppNav from '@/components/AppNav.vue'
import { getMedicines } from '@/api/medicines.js'
import { createPlan, getPlan, updatePlan } from '@/api/plans.js'
import { refreshTodayReminders } from '@/services/reminderManager.js'

function todayText() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export default {
  components: { AppNav },
  data() {
    return {
      planId: null,
      medicines: [],
      loading: true,
      submitting: false,
      loadError: '',
      initialized: false,
      form: {
        medicine_id: null,
        dose: '',
        start_date: todayText(),
        end_date: '',
        remark: '',
        is_enabled: true,
        reminder_times: ['08:00']
      }
    }
  },
  computed: {
    isEditing() {
      return Boolean(this.planId)
    },
    selectedMedicine() {
      return this.medicines.find((item) => item.id === this.form.medicine_id)
    }
  },
  onLoad(options) {
    this.planId = options.id ? Number(options.id) : null
    uni.setNavigationBarTitle({ title: this.planId ? '编辑用药计划' : '新增用药计划' })
    this.initialize()
  },
  onShow() {
    if (this.initialized) {
      this.initialize()
    }
  },
  methods: {
    async initialize() {
      this.loading = true
      this.loadError = ''
      try {
        const medicineData = await getMedicines()
        this.medicines = Array.isArray(medicineData)
          ? medicineData
          : (medicineData?.items || [])

        if (this.isEditing) {
          const plan = await getPlan(this.planId)
          this.form = {
            medicine_id: plan.medicine_id,
            dose: plan.dose,
            start_date: plan.start_date,
            end_date: plan.end_date || '',
            remark: plan.remark || '',
            is_enabled: plan.is_enabled,
            reminder_times: [...plan.reminder_times]
          }
        }
      } catch (error) {
        this.loadError = error.message || '初始化失败'
      } finally {
        this.loading = false
        this.initialized = true
      }
    },
    medicineLabel(medicine) {
      return [medicine.name, medicine.specification].filter(Boolean).join(' ')
    },
    chooseMedicine() {
      if (this.isEditing) {
        uni.showToast({ title: '编辑计划时不能更换药品', icon: 'none' })
        return
      }
      if (!this.medicines.length) {
        uni.showToast({ title: '暂无可选药品，请先添加药品', icon: 'none' })
        return
      }
      uni.showActionSheet({
        itemList: this.medicines.map(this.medicineLabel),
        success: ({ tapIndex }) => {
          this.form.medicine_id = this.medicines[tapIndex].id
          if (!this.form.dose && this.medicines[tapIndex].dosage) {
            this.form.dose = this.medicines[tapIndex].dosage
          }
        }
      })
    },
    goCreateMedicine() {
      uni.navigateTo({ url: '/pages/medicines/create' })
    },
    setStartDate(event) {
      this.form.start_date = event.detail.value
    },
    setEndDate(event) {
      this.form.end_date = event.detail.value
    },
    setEnabled(event) {
      this.form.is_enabled = event.detail.value
    },
    addReminder() {
      if (this.form.reminder_times.length >= 24) {
        uni.showToast({ title: '每天最多设置 24 个提醒', icon: 'none' })
        return
      }
      const candidates = Array.from({ length: 24 }, (_, hour) => `${String(hour).padStart(2, '0')}:00`)
      const nextTime = candidates.find((item) => !this.form.reminder_times.includes(item))
      this.form.reminder_times.push(nextTime || '12:00')
    },
    setReminderTime(index, event) {
      this.form.reminder_times.splice(index, 1, event.detail.value)
    },
    removeReminder(index) {
      if (this.form.reminder_times.length > 1) {
        this.form.reminder_times.splice(index, 1)
      }
    },
    validate() {
      if (!this.form.medicine_id) return '请选择药品'
      if (!this.form.dose.trim()) return '请填写每次剂量'
      if (!this.form.start_date) return '请选择开始日期'
      if (this.form.end_date && this.form.end_date < this.form.start_date) {
        return '结束日期不能早于开始日期'
      }
      if (!this.form.reminder_times.length) return '请至少添加一个提醒时间'
      const uniqueTimes = new Set(this.form.reminder_times)
      if (uniqueTimes.size !== this.form.reminder_times.length) {
        return '提醒时间不能重复'
      }
      return ''
    },
    async submit() {
      if (this.submitting || this.loadError) return
      const validationMessage = this.validate()
      if (validationMessage) {
        uni.showToast({ title: validationMessage, icon: 'none' })
        return
      }

      const reminderTimes = [...this.form.reminder_times].sort()
      const payload = {
        dose: this.form.dose.trim(),
        daily_times: reminderTimes.length,
        start_date: this.form.start_date,
        end_date: this.form.end_date || null,
        remark: this.form.remark.trim() || null,
        is_enabled: this.form.is_enabled,
        reminder_times: reminderTimes
      }
      if (!this.isEditing) payload.medicine_id = this.form.medicine_id

      this.submitting = true
      try {
        if (this.isEditing) {
          await updatePlan(this.planId, payload)
        } else {
          await createPlan(payload)
        }
        await refreshTodayReminders().catch((error) => {
          console.warn('刷新本地提醒失败', error)
        })
        uni.showToast({ title: this.isEditing ? '修改成功' : '创建成功', icon: 'success' })
        setTimeout(() => uni.navigateBack(), 500)
      } catch (error) {
        uni.showToast({ title: error.message || '保存失败', icon: 'none' })
      } finally {
        this.submitting = false
      }
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 28rpx 28rpx 60rpx;
  box-sizing: border-box;
  background: #f5f7fb;
}

.state-card,
.error-banner,
.form-card,
.empty-card {
  margin-bottom: 24rpx;
  padding: 30rpx;
  border-radius: 22rpx;
  background: #fff;
}

.empty-card {
  text-align: center;
}

.empty-title,
.empty-text {
  display: block;
}

.empty-title {
  color: #26354a;
  font-size: 32rpx;
  font-weight: 600;
}

.empty-text {
  margin: 16rpx 0 24rpx;
  color: #7b8798;
  font-size: 26rpx;
}

.create-medicine-button {
  color: #fff;
  border: 0;
  background: #2f80ed;
}

.error-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #b83b3b;
  border: 1rpx solid #f0bcbc;
  background: #fff5f5;
}

.retry-button {
  flex-shrink: 0;
  margin-left: 20rpx;
  color: #2f80ed;
}

.section-row,
.field,
.time-row,
.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  color: #26354a;
  font-size: 30rpx;
  font-weight: 600;
}

.field {
  min-height: 94rpx;
  border-bottom: 1rpx solid #edf0f4;
}

.field-label {
  color: #4b596d;
}

.field-value {
  max-width: 430rpx;
  color: #26354a;
  text-align: right;
}

.placeholder {
  color: #a0a8b4;
}

.input {
  width: 420rpx;
  text-align: right;
}

.clear-button,
.add-time-button,
.remove-button {
  margin: 18rpx 0 0;
  color: #2f80ed;
  border: 0;
  background: transparent;
}

.time-row {
  min-height: 88rpx;
  border-bottom: 1rpx solid #edf0f4;
}

.time-value {
  min-width: 240rpx;
  color: #2469bd;
  font-size: 32rpx;
  font-weight: 600;
}

.remove-button {
  color: #d64545;
}

.textarea {
  width: 100%;
  height: 150rpx;
  margin: 26rpx 0;
  padding: 20rpx;
  box-sizing: border-box;
  border-radius: 14rpx;
  background: #f7f9fc;
}

.switch-row {
  min-height: 80rpx;
}

.submit-button {
  color: #fff;
  border: 0;
  border-radius: 18rpx;
  background: #2f80ed;
}

.safety-notice {
  margin: 6rpx 8rpx 24rpx;
  padding: 20rpx 24rpx;
  color: #8a6418;
  border: 1rpx solid #f0d79b;
  border-radius: 14rpx;
  background: #fffaf0;
  font-size: 24rpx;
  line-height: 1.6;
}
</style>
