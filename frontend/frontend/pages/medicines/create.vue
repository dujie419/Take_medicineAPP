<template>
	<view class="page">
		<app-nav active="medicines" />
		<view class="header">
			<text class="eyebrow">药品管理</text>
			<text class="title">新增药品</text>
		</view>

		<view class="panel">
			<text class="label">药品名称</text>
			<input class="field" v-model.trim="form.name" placeholder="例如：阿司匹林" maxlength="100" />

			<text class="label">规格</text>
			<input class="field" v-model.trim="form.specification" placeholder="例如：100mg * 30片" maxlength="100" />

			<text class="label">每次用量</text>
			<input class="field" v-model.trim="form.dosage" placeholder="例如：每次 1 片" maxlength="100" />

			<text class="label">说明</text>
			<textarea class="textarea" v-model.trim="form.usage_note" placeholder="例如：饭后服用" maxlength="500" />

			<button class="primary-button" :loading="saving" :disabled="saving" @click="submit">
				保存药品
			</button>
		</view>
	</view>
</template>

<script>
	import AppNav from '../../components/AppNav.vue'
	import { authStore, createMedicine } from '../../common/api'

	export default {
		components: { AppNav },
		data() {
			return {
				saving: false,
				form: {
					name: '',
					specification: '',
					dosage: '',
					usage_note: '',
				},
			}
		},
		onLoad() {
			if (!authStore.getToken()) {
				uni.showToast({ title: '请先登录', icon: 'none' })
				uni.navigateBack()
			}
		},
		methods: {
			async submit() {
				if (!this.form.name) {
					uni.showToast({ title: '药品名称不能为空', icon: 'none' })
					return
				}

				this.saving = true
				try {
					const medicine = await createMedicine(this.form)
					uni.showToast({ title: '已保存', icon: 'success' })
					uni.redirectTo({ url: `/pages/medicines/detail?id=${medicine.id}` })
				} catch (error) {
					uni.showToast({ title: error.message || '保存失败', icon: 'none' })
				} finally {
					this.saving = false
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
	}

	.panel {
		padding: 28rpx;
		border: 1rpx solid #e5e7eb;
		border-radius: 8rpx;
		background: #ffffff;
		box-sizing: border-box;
	}

	.label {
		display: block;
		margin-bottom: 10rpx;
		color: #334155;
		font-size: 28rpx;
	}

	.field,
	.textarea {
		width: 100%;
		margin-bottom: 22rpx;
		padding: 0 22rpx;
		border: 1rpx solid #cbd5e1;
		border-radius: 8rpx;
		background: #ffffff;
		box-sizing: border-box;
		color: #111827;
		font-size: 30rpx;
	}

	.field {
		height: 88rpx;
	}

	.textarea {
		height: 176rpx;
		padding-top: 18rpx;
		line-height: 1.5;
	}

	.primary-button {
		height: 88rpx;
		line-height: 88rpx;
		margin-top: 10rpx;
		border-radius: 8rpx;
		background: #2563eb;
		color: #ffffff;
		font-size: 30rpx;
	}
</style>
