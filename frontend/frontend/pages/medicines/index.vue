<template>
	<view class="page">
		<view class="header">
			<view>
				<text class="eyebrow">药品管理</text>
				<text class="title">我的药品</text>
			</view>
			<button class="add-button" @click="goCreate">新增</button>
		</view>

		<view v-if="loading" class="state-panel">
			<text>加载中...</text>
		</view>

		<view v-else-if="medicines.length === 0" class="state-panel">
			<text class="empty-title">暂无药品</text>
			<text class="empty-text">先添加常用药品，B 同学的用药计划模块就可以选择它们。</text>
			<button class="primary-button" @click="goCreate">添加药品</button>
		</view>

		<view v-else class="list">
			<view
				v-for="medicine in medicines"
				:key="medicine.id"
				class="medicine-card"
				@click="goDetail(medicine.id)"
			>
				<view>
					<text class="medicine-name">{{ medicine.name }}</text>
					<text class="medicine-meta">{{ formatMedicineMeta(medicine) }}</text>
				</view>
				<text class="arrow">›</text>
			</view>
		</view>
	</view>
</template>

<script>
	import { authStore, fetchMedicines } from '../../common/api'

	export default {
		data() {
			return {
				loading: false,
				medicines: [],
			}
		},
		onShow() {
			this.loadMedicines()
		},
		methods: {
			async loadMedicines() {
				if (!authStore.getToken()) {
					uni.showToast({ title: '请先登录', icon: 'none' })
					uni.navigateBack()
					return
				}

				this.loading = true
				try {
					this.medicines = await fetchMedicines()
				} catch (error) {
					uni.showToast({ title: error.message || '加载失败', icon: 'none' })
				} finally {
					this.loading = false
				}
			},
			formatMedicineMeta(medicine) {
				const parts = [medicine.specification, medicine.dosage].filter(Boolean)
				return parts.length > 0 ? parts.join(' · ') : '未填写规格和用量'
			},
			goCreate() {
				uni.navigateTo({ url: '/pages/medicines/create' })
			},
			goDetail(id) {
				uni.navigateTo({ url: `/pages/medicines/detail?id=${id}` })
			},
		},
	}
</script>

<style>
	.page {
		min-height: 100vh;
		padding: 32rpx;
		box-sizing: border-box;
	}

	.header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 28rpx;
	}

	.eyebrow {
		display: block;
		margin-bottom: 8rpx;
		color: #64748b;
		font-size: 24rpx;
	}

	.title {
		display: block;
		color: #111827;
		font-size: 44rpx;
		font-weight: 700;
		line-height: 1.25;
	}

	.add-button {
		width: 132rpx;
		height: 72rpx;
		line-height: 72rpx;
		margin: 0;
		border-radius: 8rpx;
		background: #2563eb;
		color: #ffffff;
		font-size: 28rpx;
	}

	.state-panel,
	.medicine-card {
		padding: 28rpx;
		border: 1rpx solid #e5e7eb;
		border-radius: 8rpx;
		background: #ffffff;
		box-sizing: border-box;
	}

	.state-panel {
		color: #64748b;
		font-size: 28rpx;
	}

	.empty-title {
		display: block;
		margin-bottom: 12rpx;
		color: #111827;
		font-size: 32rpx;
		font-weight: 600;
	}

	.empty-text {
		display: block;
		margin-bottom: 24rpx;
		color: #64748b;
		font-size: 26rpx;
		line-height: 1.6;
	}

	.primary-button {
		height: 88rpx;
		line-height: 88rpx;
		border-radius: 8rpx;
		background: #2563eb;
		color: #ffffff;
		font-size: 30rpx;
	}

	.list {
		display: flex;
		flex-direction: column;
		gap: 18rpx;
	}

	.medicine-card {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.medicine-name {
		display: block;
		margin-bottom: 10rpx;
		color: #111827;
		font-size: 32rpx;
		font-weight: 600;
	}

	.medicine-meta {
		display: block;
		color: #64748b;
		font-size: 26rpx;
	}

	.arrow {
		color: #94a3b8;
		font-size: 48rpx;
	}
</style>
