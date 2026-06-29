<template>
  <scroll-view class="app-nav-scroll" scroll-x :show-scrollbar="false">
    <view class="app-nav">
      <view
        v-for="item in items"
        :key="item.key"
        :class="['nav-item', { active: active === item.key }]"
        @click="navigate(item)"
      >
        <text>{{ item.label }}</text>
      </view>
    </view>
  </scroll-view>
</template>

<script>
export default {
  props: {
    active: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      items: [
        { key: 'today', label: '今日提醒', url: '/pages/today/index' },
        { key: 'medicines', label: '我的药品', url: '/pages/medicines/index' },
        { key: 'plans', label: '用药计划', url: '/pages/plans/index' },
        { key: 'profile', label: '我的', url: '/pages/index/index' }
      ]
    }
  },
  methods: {
    navigate(item) {
      if (item.key === this.active) return
      uni.reLaunch({ url: item.url })
    }
  }
}
</script>

<style scoped>
.app-nav-scroll {
  width: 100%;
  margin-bottom: 28rpx;
  white-space: nowrap;
}

.app-nav {
  display: inline-flex;
  min-width: 100%;
  padding: 8rpx;
  border: 1rpx solid #dfe7f1;
  border-radius: 18rpx;
  background: #fff;
  box-sizing: border-box;
  box-shadow: 0 6rpx 20rpx rgba(31, 52, 85, 0.05);
}

.nav-item {
  flex: 1;
  min-width: 150rpx;
  padding: 18rpx 22rpx;
  border-radius: 14rpx;
  color: #64748b;
  font-size: 26rpx;
  text-align: center;
  box-sizing: border-box;
}

.nav-item.active {
  color: #fff;
  background: #2f80ed;
  font-weight: 600;
}
</style>
