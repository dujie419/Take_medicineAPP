<template>
	<view class="page">
		<app-nav active="medicines" />
		<view class="header">
			<text class="eyebrow">药品详情</text>
			<text class="title">{{ medicine ? medicine.name : '加载中' }}</text>
		</view>

		<view v-if="medicine" class="panel">
			<view class="info-row">
				<text class="label">药品名称</text>
				<text class="value">{{ medicine.name }}</text>
			</view>
			<view class="info-row">
				<text class="label">规格</text>
				<text class="value">{{ medicine.specification || '未填写' }}</text>
			</view>
			<view class="info-row">
				<text class="label">每次用量</text>
				<text class="value">{{ medicine.dosage || '未填写' }}</text>
			</view>
			<view class="info-row">
				<text class="label">说明</text>
				<text class="value">{{ medicine.usage_note || '未填写' }}</text>
			</view>
			<view class="info-row">
				<text class="label">图片路径</text>
				<text class="value">{{ medicine.original_image_path || '暂无' }}</text>
			</view>
			<view class="info-row">
				<text class="label">识别可信度</text>
				<text class="value">{{ confidenceText }}</text>
			</view>
		</view>

		<view v-else class="panel">
			<text class="loading-text">加载中...</text>
		</view>
	</view>
</template>

<script>
	import AppNav from '../../components/AppNav.vue'
	import { authStore, fetchMedicineDetail } from '../../common/api'

	export default {
		components: { AppNav },
		data() {
			return {
				medicineId: null,
				medicine: null,
			}
		},
		computed: {
			confidenceText() {
				if (!this.medicine || this.medicine.ai_confidence === null || this.medicine.ai_confidence === undefined) {
					return '暂无'
				}
				return `${Math.round(this.medicine.ai_confidence * 100)}%`
			},
		},
		onLoad(options) {
			if (!authStore.getToken()) {
				uni.showToast({ title: '请先登录', icon: 'none' })
				uni.navigateBack()
				return
			}

			this.medicineId = options.id
			this.loadMedicine()
		},
		methods: {
			async loadMedicine() {
				try {
					this.medicine = await fetchMedicineDetail(this.medicineId)
				} catch (error) {
					uni.showToast({ title: error.message || '加载失败', icon: 'none' })
				}
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
		word-break: break-all;
	}

	.panel {
		padding: 28rpx;
		border: 1rpx solid #e5e7eb;
		border-radius: 8rpx;
		background: #ffffff;
		box-sizing: border-box;
	}

	.info-row {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 24rpx;
		padding: 20rpx 0;
		border-bottom: 1rpx solid #f1f5f9;
	}

	.info-row:last-child {
		border-bottom: 0;
	}

	.label {
		flex: 0 0 168rpx;
		color: #64748b;
		font-size: 28rpx;
	}

	.value {
		flex: 1;
		color: #111827;
		font-size: 28rpx;
		line-height: 1.5;
		text-align: right;
		word-break: break-all;
	}

	.loading-text {
		color: #64748b;
		font-size: 28rpx;
	}
</style>
