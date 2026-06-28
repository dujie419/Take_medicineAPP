<template>
	<view class="page">
		<view class="profile-header">
			<view>
				<text class="eyebrow">个人资料</text>
				<text class="title">{{ isLoggedIn ? displayName : '请先登录' }}</text>
			</view>
			<view class="status" :class="{ active: isLoggedIn }">
				<text>{{ isLoggedIn ? '已登录' : '未登录' }}</text>
			</view>
		</view>

		<view v-if="isLoggedIn" class="panel">
			<view class="info-row">
				<text class="label">称呼</text>
				<text class="value">{{ user.nickname }}</text>
			</view>
			<view class="info-row">
				<text class="label">手机号</text>
				<text class="value">{{ user.phone }}</text>
			</view>
			<view class="info-row">
				<text class="label">时区</text>
				<text class="value">{{ user.timezone }}</text>
			</view>
		</view>

		<view v-if="isLoggedIn" class="panel">
			<text class="section-title">修改称呼</text>
			<input
				class="field"
				v-model.trim="nicknameForm"
				placeholder="请输入称呼"
				maxlength="30"
			/>
			<button class="primary-button" :loading="saving" :disabled="saving" @click="saveNickname">
				保存称呼
			</button>
		</view>

		<view v-else class="panel">
			<text class="section-title">手机号验证码登录</text>
			<input
				class="field"
				v-model.trim="loginForm.phone"
				type="number"
				placeholder="请输入手机号"
				maxlength="11"
			/>
			<view class="code-row">
				<input
					class="field code-field"
					v-model.trim="loginForm.code"
					type="number"
					placeholder="验证码"
					maxlength="6"
				/>
				<button class="secondary-button" :disabled="sendingCode" @click="sendCode">
					{{ sendingCode ? '发送中' : '获取验证码' }}
				</button>
			</view>
			<button class="primary-button" :loading="loggingIn" :disabled="loggingIn" @click="submitLogin">
				登录
			</button>
			<text class="hint">开发环境验证码固定为 123456</text>
		</view>

		<view class="panel compact">
			<view class="info-row">
				<text class="label">后端地址</text>
				<text class="value">{{ baseUrl }}</text>
			</view>
			<button v-if="isLoggedIn" class="primary-button" @click="goMedicines">我的药品</button>
			<button v-if="isLoggedIn" class="ghost-button" @click="logout">退出登录</button>
		</view>
	</view>
</template>

<script>
	import {
		authStore,
		fetchCurrentUser,
		login,
		sendSmsCode,
		updateCurrentUser,
	} from '../../common/api'

	export default {
		data() {
			return {
				baseUrl: authStore.getBaseUrl(),
				user: authStore.getStoredUser(),
				nicknameForm: '',
				loginForm: {
					phone: '',
					code: '',
				},
				sendingCode: false,
				loggingIn: false,
				saving: false,
			}
		},
		computed: {
			isLoggedIn() {
				return Boolean(authStore.getToken() && this.user)
			},
			displayName() {
				return this.user?.nickname || '我的'
			},
		},
		onLoad() {
			this.restoreCurrentUser()
		},
		methods: {
			showError(error) {
				uni.showToast({
					title: error.message || '操作失败',
					icon: 'none',
				})
			},
			async restoreCurrentUser() {
				if (!authStore.getToken()) {
					return
				}

				try {
					this.user = await fetchCurrentUser()
					this.nicknameForm = this.user.nickname
				} catch (error) {
					authStore.clearAuth()
					this.user = null
				}
			},
			async sendCode() {
				if (!this.loginForm.phone) {
					uni.showToast({ title: '请输入手机号', icon: 'none' })
					return
				}

				this.sendingCode = true
				try {
					await sendSmsCode(this.loginForm.phone)
					uni.showToast({ title: '验证码已发送', icon: 'success' })
				} catch (error) {
					this.showError(error)
				} finally {
					this.sendingCode = false
				}
			},
			async submitLogin() {
				if (!this.loginForm.phone || !this.loginForm.code) {
					uni.showToast({ title: '请输入手机号和验证码', icon: 'none' })
					return
				}

				this.loggingIn = true
				try {
					this.user = await login(this.loginForm.phone, this.loginForm.code)
					this.nicknameForm = this.user.nickname
					uni.showToast({ title: '登录成功', icon: 'success' })
					setTimeout(() => {
						this.goMedicines()
					}, 500)
				} catch (error) {
					this.showError(error)
				} finally {
					this.loggingIn = false
				}
			},
			async saveNickname() {
				if (!this.nicknameForm) {
					uni.showToast({ title: '称呼不能为空', icon: 'none' })
					return
				}

				this.saving = true
				try {
					this.user = await updateCurrentUser({ nickname: this.nicknameForm })
					this.nicknameForm = this.user.nickname
					uni.showToast({ title: '已保存', icon: 'success' })
				} catch (error) {
					this.showError(error)
				} finally {
					this.saving = false
				}
			},
			logout() {
				authStore.clearAuth()
				this.user = null
				this.nicknameForm = ''
				this.loginForm.code = ''
				uni.showToast({ title: '已退出', icon: 'none' })
			},
			goMedicines() {
				uni.navigateTo({ url: '/pages/medicines/index' })
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

	.profile-header {
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

	.status {
		min-width: 104rpx;
		padding: 10rpx 14rpx;
		border: 1rpx solid #cbd5e1;
		border-radius: 8rpx;
		color: #64748b;
		font-size: 24rpx;
		text-align: center;
		box-sizing: border-box;
	}

	.status.active {
		border-color: #16a34a;
		color: #15803d;
		background: #f0fdf4;
	}

	.panel {
		margin-bottom: 24rpx;
		padding: 28rpx;
		border: 1rpx solid #e5e7eb;
		border-radius: 8rpx;
		background: #ffffff;
		box-sizing: border-box;
	}

	.compact {
		padding-bottom: 20rpx;
	}

	.section-title {
		display: block;
		margin-bottom: 18rpx;
		color: #111827;
		font-size: 30rpx;
		font-weight: 600;
	}

	.info-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 18rpx 0;
		border-bottom: 1rpx solid #f1f5f9;
	}

	.info-row:last-child {
		border-bottom: 0;
	}

	.label {
		color: #64748b;
		font-size: 28rpx;
	}

	.value {
		max-width: 430rpx;
		color: #111827;
		font-size: 28rpx;
		text-align: right;
		word-break: break-all;
	}

	.field {
		width: 100%;
		height: 88rpx;
		margin-bottom: 18rpx;
		padding: 0 22rpx;
		border: 1rpx solid #cbd5e1;
		border-radius: 8rpx;
		background: #ffffff;
		box-sizing: border-box;
		color: #111827;
		font-size: 30rpx;
	}

	.code-row {
		display: flex;
		gap: 16rpx;
		align-items: center;
	}

	.code-field {
		flex: 1;
		margin-bottom: 0;
	}

	.primary-button,
	.secondary-button,
	.ghost-button {
		height: 88rpx;
		line-height: 88rpx;
		border-radius: 8rpx;
		font-size: 30rpx;
	}

	.primary-button {
		margin-top: 18rpx;
		background: #2563eb;
		color: #ffffff;
	}

	.secondary-button {
		width: 210rpx;
		margin: 0;
		padding: 0;
		background: #0f766e;
		color: #ffffff;
	}

	.ghost-button {
		margin-top: 18rpx;
		border: 1rpx solid #cbd5e1;
		background: #ffffff;
		color: #334155;
	}

	.hint {
		display: block;
		margin-top: 18rpx;
		color: #64748b;
		font-size: 24rpx;
	}
</style>
