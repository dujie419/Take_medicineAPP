<template>
	<view class="page">
		<view class="header">
			<text class="eyebrow">AI 图片识药</text>
			<text class="title">拍照识药</text>
		</view>

		<view class="panel">
			<view v-if="imagePath" class="preview-wrap" @click="previewImage">
				<image class="preview" :src="imagePath" mode="aspectFill" />
			</view>
			<view v-else class="empty-image">
				<text>选择药盒、药瓶、处方或用药清单图片</text>
			</view>

			<view class="button-row">
				<button class="secondary-button" :disabled="recognizing || saving" @click="chooseFromCamera">拍照</button>
				<button class="secondary-button album" :disabled="recognizing || saving" @click="chooseFromAlbum">相册</button>
			</view>
			<button class="primary-button" :loading="recognizing" :disabled="!imagePath || recognizing || saving" @click="recognize">
				上传识别
			</button>
		</view>

		<view v-if="result" class="notice">
			<text>{{ result.overall_risk_notice || riskNotice }}</text>
		</view>
		<view v-else class="notice">
			<text>{{ riskNotice }}</text>
		</view>

		<view v-if="result" class="result-meta">
			<text>图片类型：{{ result.document_type || '未知' }}</text>
			<text>识别模式：{{ result.recognition_mode }}</text>
		</view>

		<view v-for="(medicine, index) in medicines" :key="medicine.local_id" class="medicine-card">
			<view class="card-header">
				<text class="card-title">药品 {{ index + 1 }}</text>
				<button class="delete-button" @click="removeMedicine(index)">删除</button>
			</view>

			<text class="label">药品名称</text>
			<input class="field" v-model.trim="medicine.name" placeholder="例如：阿司匹林" maxlength="100" />

			<text class="label">规格</text>
			<input class="field" v-model.trim="medicine.specification" placeholder="例如：100mg * 30片" maxlength="100" />

			<text class="label">每次用量</text>
			<input class="field" v-model.trim="medicine.dosage" placeholder="例如：每次 1 片" maxlength="100" />

			<text class="label">说明</text>
			<textarea class="textarea" v-model.trim="medicine.usage_note" placeholder="例如：饭后服用" maxlength="500" />

			<view class="confidence-row">
				<text class="confidence-label">可信度</text>
				<text class="confidence-value">{{ confidenceText(medicine.ai_confidence) }}</text>
			</view>
			<text class="risk-text">{{ medicine.risk_notice || '请人工确认后保存' }}</text>
		</view>

		<view v-if="result" class="footer-actions">
			<button class="ghost-button" :disabled="saving" @click="addMedicine">添加漏识别药品</button>
			<button class="primary-button" :loading="saving" :disabled="saving || medicines.length === 0" @click="saveAll">
				批量保存药品
			</button>
		</view>
	</view>
</template>

<script>
	import { authStore, batchCreateMedicines, recognizeMedicineImage } from '../../common/api'

	export default {
		data() {
			return {
				imagePath: '',
				result: null,
				medicines: [],
				recognizing: false,
				saving: false,
				riskNotice: 'AI识别结果仅供参考，请以医生处方、药品包装和说明书为准。',
			}
		},
		onLoad() {
			if (!authStore.getToken()) {
				uni.showToast({ title: '请先登录', icon: 'none' })
				uni.navigateBack()
			}
		},
		methods: {
			chooseFromCamera() {
				this.chooseImage(['camera'])
			},
			chooseFromAlbum() {
				this.chooseImage(['album'])
			},
			chooseImage(sourceType) {
				uni.chooseImage({
					count: 1,
					sizeType: ['compressed'],
					sourceType,
					success: (res) => {
						this.imagePath = res.tempFilePaths[0]
						this.result = null
						this.medicines = []
					},
				})
			},
			previewImage() {
				if (!this.imagePath) return
				uni.previewImage({ urls: [this.imagePath], current: this.imagePath })
			},
			async recognize() {
				this.recognizing = true
				try {
					const result = await recognizeMedicineImage(this.imagePath)
					this.result = result
					this.medicines = (result.medicines || []).map((item) => this.toEditableMedicine(item, result.image_path))
					if (this.medicines.length === 0) {
						this.addMedicine()
					}
					uni.showToast({ title: '识别完成', icon: 'success' })
				} catch (error) {
					uni.showToast({ title: error.message || '识别失败', icon: 'none' })
				} finally {
					this.recognizing = false
				}
			},
			toEditableMedicine(item = {}, imagePath = '') {
				return {
					local_id: `${Date.now()}_${Math.random()}`,
					name: item.name || '',
					specification: item.specification || '',
					dosage: item.dosage || '',
					usage_note: item.usage_note || '',
					original_image_path: imagePath,
					ai_confidence: item.confidence ?? null,
					risk_notice: item.risk_notice || '',
				}
			},
			addMedicine() {
				this.medicines.push(this.toEditableMedicine({}, this.result?.image_path || ''))
			},
			removeMedicine(index) {
				this.medicines.splice(index, 1)
			},
			confidenceText(value) {
				if (value === null || value === undefined || value === '') {
					return '暂无'
				}
				return `${Math.round(Number(value) * 100)}%`
			},
			async saveAll() {
				const payload = this.medicines.map((medicine) => ({
					name: medicine.name,
					specification: medicine.specification,
					dosage: medicine.dosage,
					usage_note: medicine.usage_note,
					original_image_path: medicine.original_image_path,
					ai_confidence: medicine.ai_confidence,
				}))

				if (payload.some((medicine) => !medicine.name)) {
					uni.showToast({ title: '药品名称不能为空', icon: 'none' })
					return
				}

				this.saving = true
				try {
					await batchCreateMedicines(payload)
					uni.showToast({ title: '已保存', icon: 'success' })
					setTimeout(() => {
						uni.redirectTo({ url: '/pages/medicines/index' })
					}, 500)
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

	.panel,
	.medicine-card,
	.notice,
	.result-meta {
		margin-bottom: 24rpx;
		padding: 28rpx;
		border: 1rpx solid #e5e7eb;
		border-radius: 8rpx;
		background: #ffffff;
		box-sizing: border-box;
	}

	.preview-wrap,
	.empty-image {
		width: 100%;
		height: 360rpx;
		margin-bottom: 22rpx;
		border-radius: 8rpx;
		overflow: hidden;
		background: #f8fafc;
	}

	.preview {
		width: 100%;
		height: 100%;
	}

	.empty-image {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 36rpx;
		border: 1rpx dashed #cbd5e1;
		color: #64748b;
		font-size: 28rpx;
		text-align: center;
		box-sizing: border-box;
	}

	.button-row {
		display: flex;
		gap: 16rpx;
		margin-bottom: 16rpx;
	}

	.primary-button,
	.secondary-button,
	.ghost-button,
	.delete-button {
		height: 88rpx;
		line-height: 88rpx;
		border-radius: 8rpx;
		font-size: 30rpx;
	}

	.primary-button {
		background: #2563eb;
		color: #ffffff;
	}

	.secondary-button {
		flex: 1;
		margin: 0;
		background: #0f766e;
		color: #ffffff;
	}

	.secondary-button.album {
		background: #334155;
	}

	.ghost-button {
		margin-bottom: 16rpx;
		border: 1rpx solid #cbd5e1;
		background: #ffffff;
		color: #334155;
	}

	.notice {
		color: #92400e;
		background: #fffbeb;
		border-color: #fde68a;
		font-size: 26rpx;
		line-height: 1.6;
	}

	.result-meta {
		display: flex;
		justify-content: space-between;
		gap: 18rpx;
		color: #64748b;
		font-size: 26rpx;
	}

	.card-header,
	.confidence-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.card-header {
		margin-bottom: 20rpx;
	}

	.card-title {
		color: #111827;
		font-size: 32rpx;
		font-weight: 600;
	}

	.delete-button {
		width: 112rpx;
		height: 64rpx;
		line-height: 64rpx;
		margin: 0;
		padding: 0;
		background: #fee2e2;
		color: #b91c1c;
		font-size: 26rpx;
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

	.confidence-row {
		margin-bottom: 12rpx;
		color: #334155;
		font-size: 28rpx;
	}

	.confidence-value {
		font-weight: 600;
	}

	.risk-text {
		display: block;
		color: #64748b;
		font-size: 24rpx;
		line-height: 1.6;
	}

	.footer-actions {
		padding-bottom: 24rpx;
	}
</style>
