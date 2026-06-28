<template>
	<view class="content">
		<image class="logo" src="/static/logo.png"></image>
		<view class="text-area">
			<text class="title">按时吃药</text>
			<text class="subtitle">从一份清晰的用药计划开始</text>
		</view>
		<button class="plan-button" @click="openPlans">进入用药计划</button>
	</view>
</template>

<script>
	export default {
		methods: {
			openPlans() {
				uni.navigateTo({
					url: '/pages/plans/index'
				})
			}
		}
	}
</script>

<style>
	.content {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
	}

	.logo {
		height: 200rpx;
		width: 200rpx;
		margin-top: 200rpx;
		margin-left: auto;
		margin-right: auto;
		margin-bottom: 50rpx;
	}

	.text-area {
		display: flex;
		justify-content: center;
		align-items: center;
		flex-direction: column;
	}

	.title {
		font-size: 36rpx;
		font-weight: 700;
		color: #27364b;
	}

	.subtitle {
		margin-top: 14rpx;
		font-size: 26rpx;
		color: #7b8798;
	}

	.plan-button {
		margin-top: 56rpx;
		padding: 0 56rpx;
		color: #fff;
		border: 0;
		border-radius: 18rpx;
		background: #2f80ed;
	}
</style>
