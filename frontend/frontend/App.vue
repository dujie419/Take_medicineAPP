<script>
	import { authStore } from '@/common/api.js'
	import {
		cancelCurrentUserReminders,
		consumeReminderLaunchRoute,
		refreshTodayReminders
	} from '@/services/reminderManager.js'

	export default {
		onLaunch: function() {
			console.log('App Launch')
			uni.$on('take-medicine:auth-clearing', cancelCurrentUserReminders)
		},
		onShow: function() {
			console.log('App Show')
			if (authStore.getToken()) {
				refreshTodayReminders().catch((error) => {
					console.warn('同步本地用药提醒失败', error)
				})
			}
			if (consumeReminderLaunchRoute() === '/pages/today/index') {
				setTimeout(() => uni.reLaunch({ url: '/pages/today/index' }), 0)
			}
		},
		onHide: function() {
			console.log('App Hide')
		}
	}
</script>

<style>
	page {
		background: #f5f7fa;
		color: #1f2937;
		font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
	}

	button {
		border-radius: 8rpx;
	}
</style>
