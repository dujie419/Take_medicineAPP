package com.takemedicine.reminder

import android.Manifest
import android.app.AlarmManager
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.media.MediaPlayer
import android.media.MediaRecorder
import android.net.Uri
import android.os.Build
import android.speech.tts.UtteranceProgressListener
import android.os.SystemClock
import android.provider.Settings
import android.speech.tts.TextToSpeech
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import io.dcloud.uts.UTSAndroid
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.security.MessageDigest
import java.util.Locale
import kotlin.math.max

private const val CHANNEL_ID = "take_medicine_reminders"
private const val PREFS_NAME = "take_medicine_alarm_registry"
private const val ROUTE_TODAY = "/pages/today/index"
private const val REPEAT_MILLIS = 5L * 60L * 1000L
private const val WINDOW_MILLIS = 2L * 60L * 60L * 1000L
private const val MAX_ALARMS = 25

object MedicineReminderNative {
    private var recorder: MediaRecorder? = null
    private var recordingStartedAt = 0L
    private var recordingFile: File? = null

    private fun context(): Context =
        requireNotNull(UTSAndroid.getAppContext()) { "Android context unavailable" }

    private fun alarmManager(context: Context): AlarmManager =
        context.getSystemService(Context.ALARM_SERVICE) as AlarmManager

    private fun requestCode(userId: String, groupId: String, repeatIndex: Int): Int =
        "$userId|$groupId|$repeatIndex".hashCode() and 0x7fffffff

    private fun registryKey(userId: String): String = "user:$userId"

    private fun alarmIntent(
        context: Context,
        userId: String,
        groupId: String,
        repeatIndex: Int,
        speechText: String,
        medicineNames: String,
    ): PendingIntent {
        val intent = Intent(context, MedicineAlarmReceiver::class.java).apply {
            putExtra("user_id", userId)
            putExtra("group_id", groupId)
            putExtra("speech_text", speechText)
            putExtra("medicine_names", medicineNames)
        }
        return PendingIntent.getBroadcast(
            context,
            requestCode(userId, groupId, repeatIndex),
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
    }

    private fun scheduleOne(
        context: Context,
        triggerAt: Long,
        pendingIntent: PendingIntent,
    ) {
        val manager = alarmManager(context)
        if (Build.VERSION.SDK_INT >= 31 && !manager.canScheduleExactAlarms()) {
            manager.setWindow(
                AlarmManager.RTC_WAKEUP,
                triggerAt,
                60L * 1000L,
                pendingIntent,
            )
        } else {
            manager.setExactAndAllowWhileIdle(
                AlarmManager.RTC_WAKEUP,
                triggerAt,
                pendingIntent,
            )
        }
    }

    fun scheduleReminders(userId: String, itemsJson: String): Int {
        val context = context()
        cancelUserReminders(userId)
        val now = System.currentTimeMillis()
        val requestCodes = mutableSetOf<String>()
        var scheduled = 0
        val items = JSONArray(itemsJson)

        for (itemIndex in 0 until items.length()) {
            val item = items.getJSONObject(itemIndex)
            val status = item.optString("status", "pending")
            if (status != "pending" && status != "snoozed") continue

            val groupId = item.getString("groupId")
            val plannedAt = item.getLong("plannedAtEpochMs")
            val snoozeAt = if (item.isNull("snoozeUntilEpochMs")) 0L
                else item.optLong("snoozeUntilEpochMs", 0L)
            val endAt = plannedAt + WINDOW_MILLIS
            if (endAt < now) continue

            var firstAt = if (status == "snoozed" && snoozeAt > 0L) snoozeAt else plannedAt
            if (firstAt < now) {
                val elapsed = max(0L, now - plannedAt)
                firstAt = plannedAt + ((elapsed + REPEAT_MILLIS - 1L) / REPEAT_MILLIS) * REPEAT_MILLIS
            }

            for (repeatIndex in 0 until MAX_ALARMS) {
                val triggerAt = firstAt + repeatIndex * REPEAT_MILLIS
                if (triggerAt > endAt) break
                val pendingIntent = alarmIntent(
                    context,
                    userId,
                    groupId,
                    repeatIndex,
                    item.optString("speechText"),
                    item.optString("medicineNames"),
                )
                scheduleOne(context, triggerAt, pendingIntent)
                requestCodes.add(
                    listOf(groupId, repeatIndex.toString()).joinToString("|")
                )
                scheduled += 1
            }
        }

        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .putStringSet(registryKey(userId), requestCodes)
            .apply()
        return scheduled
    }

    fun cancelReminderGroup(userId: String, groupId: String) {
        val context = context()
        val manager = alarmManager(context)
        for (repeatIndex in 0 until MAX_ALARMS) {
            manager.cancel(
                alarmIntent(context, userId, groupId, repeatIndex, "", "")
            )
        }
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val remaining = prefs.getStringSet(registryKey(userId), emptySet())
            ?.filterNot { it.startsWith("$groupId|") }
            ?.toSet()
            ?: emptySet()
        prefs.edit().putStringSet(registryKey(userId), remaining).apply()
    }

    fun cancelUserReminders(userId: String) {
        val context = context()
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val entries = prefs.getStringSet(registryKey(userId), emptySet()) ?: emptySet()
        val manager = alarmManager(context)
        entries.forEach { entry ->
            val splitAt = entry.lastIndexOf('|')
            if (splitAt <= 0) return@forEach
            val groupId = entry.substring(0, splitAt)
            val repeatIndex = entry.substring(splitAt + 1).toIntOrNull() ?: return@forEach
            manager.cancel(alarmIntent(context, userId, groupId, repeatIndex, "", ""))
        }
        prefs.edit().remove(registryKey(userId)).apply()
    }

    private fun recordingFile(userId: String, groupId: String): File {
        val digest = MessageDigest.getInstance("SHA-256")
            .digest(groupId.toByteArray())
            .joinToString("") { "%02x".format(it) }
        val directory = File(context().filesDir, "medicine-reminders/$userId")
        directory.mkdirs()
        return File(directory, "$digest.m4a")
    }

    fun startRecording(userId: String, groupId: String): String {
        stopRecordingSafely()
        val target = recordingFile(userId, groupId)
        val nextRecorder = if (Build.VERSION.SDK_INT >= 31) {
            MediaRecorder(context())
        } else {
            @Suppress("DEPRECATION")
            MediaRecorder()
        }
        nextRecorder.setAudioSource(MediaRecorder.AudioSource.MIC)
        nextRecorder.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
        nextRecorder.setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
        nextRecorder.setOutputFile(target.absolutePath)
        nextRecorder.prepare()
        nextRecorder.start()
        recorder = nextRecorder
        recordingFile = target
        recordingStartedAt = SystemClock.elapsedRealtime()
        return target.absolutePath
    }

    fun stopRecording(): Long {
        val duration = if (recordingStartedAt == 0L) 0L
            else SystemClock.elapsedRealtime() - recordingStartedAt
        val current = recorder ?: return 0L
        try {
            current.stop()
        } catch (error: RuntimeException) {
            recordingFile?.delete()
            throw error
        } finally {
            current.release()
            recorder = null
            recordingStartedAt = 0L
        }
        if (duration < 1000L) {
            recordingFile?.delete()
        }
        return duration
    }

    private fun stopRecordingSafely() {
        if (recorder == null) return
        try {
            stopRecording()
        } catch (_: Exception) {
            recorder?.release()
            recorder = null
            recordingStartedAt = 0L
        }
    }

    fun playRecording(userId: String, groupId: String): Boolean {
        val file = recordingFile(userId, groupId)
        if (!file.exists()) return false
        return playFile(file)
    }

    fun deleteRecording(userId: String, groupId: String): Boolean {
        val file = recordingFile(userId, groupId)
        return !file.exists() || file.delete()
    }

    fun hasRecording(userId: String, groupId: String): Boolean =
        recordingFile(userId, groupId).exists()

    fun permissionStateJson(): String {
        val context = context()
        val notificationGranted = Build.VERSION.SDK_INT < 33 ||
            ContextCompat.checkSelfPermission(
                context,
                "android.permission.POST_NOTIFICATIONS",
            ) == PackageManager.PERMISSION_GRANTED
        val microphoneGranted = ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.RECORD_AUDIO,
        ) == PackageManager.PERMISSION_GRANTED
        val exactAlarmGranted = Build.VERSION.SDK_INT < 31 ||
            alarmManager(context).canScheduleExactAlarms()
        return JSONObject()
            .put("notificationGranted", notificationGranted)
            .put("microphoneGranted", microphoneGranted)
            .put("exactAlarmGranted", exactAlarmGranted)
            .toString()
    }

    fun requestExactAlarmPermission(): Boolean {
        if (Build.VERSION.SDK_INT < 31 || alarmManager(context()).canScheduleExactAlarms()) {
            return true
        }
        val activity = UTSAndroid.getUniActivity() ?: return false
        activity.startActivity(
            Intent(
                Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM,
                Uri.parse("package:${activity.packageName}"),
            )
        )
        return false
    }

    fun getLaunchRoute(): String {
        val activity = UTSAndroid.getUniActivity() ?: return ""
        val route = activity.intent?.getStringExtra("take_medicine_route") ?: ""
        activity.intent?.removeExtra("take_medicine_route")
        return route
    }

    fun playFile(file: File, onComplete: (() -> Unit)? = null): Boolean {
        return try {
            val player = MediaPlayer()
            player.setDataSource(file.absolutePath)
            player.setOnCompletionListener {
                it.release()
                onComplete?.invoke()
            }
            player.setOnErrorListener { value, _, _ ->
                value.release()
                onComplete?.invoke()
                true
            }
            player.prepare()
            player.start()
            true
        } catch (_: Exception) {
            false
        }
    }

    fun customRecordingFile(context: Context, userId: String, groupId: String): File {
        val digest = MessageDigest.getInstance("SHA-256")
            .digest(groupId.toByteArray())
            .joinToString("") { "%02x".format(it) }
        return File(context.filesDir, "medicine-reminders/$userId/$digest.m4a")
    }
}

class MedicineAlarmReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val userId = intent.getStringExtra("user_id") ?: return
        val groupId = intent.getStringExtra("group_id") ?: return
        val speechText = intent.getStringExtra("speech_text").orEmpty()
        val medicineNames = intent.getStringExtra("medicine_names").orEmpty()

        createChannel(context)
        val launchIntent = context.packageManager.getLaunchIntentForPackage(context.packageName)
            ?.apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
                putExtra("take_medicine_route", ROUTE_TODAY)
            }
        val contentIntent = launchIntent?.let {
            PendingIntent.getActivity(
                context,
                requestCodeForNotification(userId, groupId),
                it,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
            )
        }
        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(context.applicationInfo.icon)
            .setContentTitle("按时吃药提醒")
            .setContentText(if (medicineNames.isBlank()) speechText else "该服用：$medicineNames")
            .setStyle(NotificationCompat.BigTextStyle().bigText(speechText))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setAutoCancel(true)
            .setVibrate(longArrayOf(0L, 500L, 300L, 500L))
            .apply { if (contentIntent != null) setContentIntent(contentIntent) }
            .build()
        try {
            (context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager)
                .notify(requestCodeForNotification(userId, groupId), notification)
        } catch (_: SecurityException) {
            // Android 13+ notification permission may be denied. Audio fallback
            // remains available while the OS allows this receiver to run.
        }

        val pendingResult = goAsync()
        val recording = MedicineReminderNative.customRecordingFile(context, userId, groupId)
        if (
            recording.exists() &&
            MedicineReminderNative.playFile(recording) { pendingResult.finish() }
        ) {
            return
        }
        speak(context, speechText) { pendingResult.finish() }
    }

    private fun createChannel(context: Context) {
        if (Build.VERSION.SDK_INT < 26) return
        val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val channel = NotificationChannel(
            CHANNEL_ID,
            "用药提醒",
            NotificationManager.IMPORTANCE_HIGH,
        ).apply {
            description = "按时吃药的到点通知与重复提醒"
            enableVibration(true)
            vibrationPattern = longArrayOf(0L, 500L, 300L, 500L)
        }
        manager.createNotificationChannel(channel)
    }

    private fun speak(context: Context, text: String, onComplete: () -> Unit) {
        if (text.isBlank()) {
            onComplete()
            return
        }
        var engine: TextToSpeech? = null
        engine = TextToSpeech(context.applicationContext) { status ->
            if (status == TextToSpeech.SUCCESS) {
                engine?.language = Locale.SIMPLIFIED_CHINESE
                engine?.setSpeechRate(0.85f)
                engine?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                    override fun onStart(utteranceId: String?) = Unit

                    override fun onDone(utteranceId: String?) {
                        engine?.shutdown()
                        onComplete()
                    }

                    @Deprecated("Deprecated in Android")
                    override fun onError(utteranceId: String?) {
                        engine?.shutdown()
                        onComplete()
                    }
                })
                engine?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "medicine-reminder")
            } else {
                engine?.shutdown()
                onComplete()
            }
        }
    }

    private fun requestCodeForNotification(userId: String, groupId: String): Int =
        "$userId|$groupId|notification".hashCode() and 0x7fffffff
}
