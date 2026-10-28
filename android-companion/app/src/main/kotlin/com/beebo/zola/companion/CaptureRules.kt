package com.beebo.zola.companion

// P10-COMPANION: provider columns decide send, direction, and the RCS flag — P10-D04

object CaptureRules {
    fun sendable(spamReport: Int, spamType: Int, blockFiltered: String): Boolean {
        return spamReport == 0 && spamType == 0 && blockFiltered.isEmpty()
    }

    fun smsDirection(type: Int): String = if (type == 2) "out" else "in"

    fun mmsDirection(msgBox: Int): String = if (msgBox == 2) "out" else "in"

    fun receivedAtMs(date: Long): Long = if (date in 1..999_999_999_999L) date * 1000 else date

    fun rcsFlag(contentTypes: List<String>): String {
        val proved = contentTypes.any { type ->
            val lower = type.lowercase()
            "rcs" in lower || lower.startsWith("application/vnd.gsma.")
        }
        return if (proved) "yes" else "unknown"
    }

    fun attachmentKind(contentType: String): String {
        val lower = contentType.lowercase()
        return when {
            lower.startsWith("image/") -> "image"
            lower.startsWith("video/") -> "video"
            lower.startsWith("audio/") -> "audio"
            else -> "other"
        }
    }

    fun isGroup(participantCount: Int): Boolean = participantCount > 2
}
