package com.beebo.zola.companion

import android.app.Notification
import android.app.NotificationManager
import android.content.ComponentName
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification

// P10-NOTIFY: the listener hands postings to the one engine — G-ONE-ENGINE

class NotificationListener : NotificationListenerService() {
    override fun onListenerConnected() {
        NoticeFeed.current = { captureActive() }
        val active = captureActive()
        val granted = accessGranted()
        hand { engine -> engine.onListenerConnected(active, granted = granted) }
    }

    override fun onListenerDisconnected() {
        NoticeFeed.current = null
        val granted = accessGranted()
        hand { engine ->
            engine.onListenerDisconnected()
            engine.onAccessChanged(granted)
        }
        requestRebind(ComponentName(this, NotificationListener::class.java))
    }

    override fun onNotificationPosted(sbn: StatusBarNotification) {
        val notice = NoticeCapture.from(sbn) ?: return
        hand { engine -> engine.onPosted(notice) }
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification) {
        hand { engine -> engine.onRemoved(sbn.key ?: return@hand) }
    }

    private fun accessGranted(): Boolean {
        val manager = getSystemService(NotificationManager::class.java) ?: return false
        return manager.isNotificationListenerAccessGranted(
            ComponentName(this, NotificationListener::class.java),
        )
    }

    private fun captureActive(): List<PostedNotice> {
        val active = try {
            activeNotifications
        } catch (_: Exception) {
            return emptyList()
        } ?: return emptyList()
        return active.mapNotNull { NoticeCapture.from(it) }
    }

    private fun hand(job: (CompanionEngine) -> Unit) {
        if (CompanionBridge.ready()) {
            CompanionBridge.submit(job)
            return
        }
        try {
            startForegroundService(android.content.Intent(this, CompanionService::class.java))
        } catch (_: RuntimeException) {
            android.util.Log.i(CompanionService.TAG, "zola.companion listener result=gap")
            return
        }
        CompanionBridge.submit(job)
    }
}

object NoticeFeed {
    @Volatile var current: (() -> List<PostedNotice>?)? = null
}

object NoticeCapture {
    fun from(sbn: StatusBarNotification?): PostedNotice? {
        if (sbn == null) return null
        val notification = sbn.notification ?: return null
        val extras = notification.extras ?: return null
        val rawMessages = extras.getParcelableArray(Notification.EXTRA_MESSAGES)
        val messages = mutableListOf<NoticeMessage>()
        val user = extras.getParcelable(Notification.EXTRA_MESSAGING_PERSON, android.app.Person::class.java)
        if (rawMessages != null) {
            val parsed = Notification.MessagingStyle.Message.getMessagesFromBundleArray(rawMessages)
            for (message in parsed) {
                val person = message.senderPerson
                val sender = person?.name?.toString() ?: message.sender?.toString().orEmpty()
                val fromUser = person != null && user != null && samePerson(person, user)
                messages.add(
                    NoticeMessage(
                        sender = sender,
                        text = message.text?.toString().orEmpty(),
                        timestampMs = message.timestamp,
                        fromUser = fromUser,
                    ),
                )
            }
        }
        val templateExtra = extras.getString(Notification.EXTRA_TEMPLATE)?.substringAfterLast('.').orEmpty()
        val template = when {
            messages.isNotEmpty() -> "MessagingStyle"
            templateExtra.isEmpty() -> "none"
            else -> templateExtra
        }
        val flags = notification.flags
        return PostedNotice(
            packageName = sbn.packageName ?: "",
            key = sbn.key ?: "",
            template = if (template.isEmpty()) "none" else template,
            category = notification.category,
            channelId = notification.channelId,
            flagNames = flagNames(flags),
            extrasKeys = extras.keySet().toList(),
            messages = messages,
            title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString().orEmpty(),
            text = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString().orEmpty(),
            bigText = extras.getCharSequence(Notification.EXTRA_BIG_TEXT)?.toString().orEmpty(),
            conversationTitle = extras.getCharSequence(Notification.EXTRA_CONVERSATION_TITLE)?.toString().orEmpty(),
            groupConversation = extras.getBoolean(Notification.EXTRA_IS_GROUP_CONVERSATION),
            whenMs = notification.`when`,
            postMs = sbn.postTime,
            groupSummary = flags and Notification.FLAG_GROUP_SUMMARY != 0,
            ongoing = flags and Notification.FLAG_ONGOING_EVENT != 0,
            foregroundService = flags and Notification.FLAG_FOREGROUND_SERVICE != 0,
            media = template == "MediaStyle" || extras.containsKey(Notification.EXTRA_MEDIA_SESSION),
        )
    }

    private fun samePerson(left: android.app.Person, right: android.app.Person): Boolean {
        val leftKey = left.key
        val rightKey = right.key
        if (!leftKey.isNullOrEmpty() && leftKey == rightKey) return true
        val leftName = left.name?.toString().orEmpty()
        val rightName = right.name?.toString().orEmpty()
        return leftName.isNotEmpty() && leftName == rightName
    }

    private fun flagNames(flags: Int): List<String> {
        val names = mutableListOf<String>()
        if (flags and Notification.FLAG_AUTO_CANCEL != 0) names.add("AUTO_CANCEL")
        if (flags and Notification.FLAG_ONGOING_EVENT != 0) names.add("ONGOING_EVENT")
        if (flags and Notification.FLAG_NO_CLEAR != 0) names.add("NO_CLEAR")
        if (flags and Notification.FLAG_FOREGROUND_SERVICE != 0) names.add("FOREGROUND_SERVICE")
        if (flags and Notification.FLAG_GROUP_SUMMARY != 0) names.add("GROUP_SUMMARY")
        if (flags and Notification.FLAG_LOCAL_ONLY != 0) names.add("LOCAL_ONLY")
        if (flags and Notification.FLAG_ONLY_ALERT_ONCE != 0) names.add("ONLY_ALERT_ONCE")
        if (flags and Notification.FLAG_HIGH_PRIORITY != 0) names.add("HIGH_PRIORITY")
        if (flags and Notification.FLAG_BUBBLE != 0) names.add("BUBBLE")
        if (flags and Notification.FLAG_INSISTENT != 0) names.add("INSISTENT")
        return names
    }
}
