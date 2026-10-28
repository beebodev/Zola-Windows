package com.beebo.zola.companion

// P10-COMPANION: the service talks to the engine through these ports — Phase 5

data class TextRecord(
    val kind: String,
    val providerId: Long,
    val dateMs: Long,
    val dateSentMs: Long,
    val senderRaw: String,
    val body: String,
    val direction: String,
    val threadId: String,
    val participants: List<String>,
    val creator: String,
    val sendable: Boolean,
    val present: Boolean,
    val containsOtp: Boolean,
    val contentTypes: List<String>,
    val attachmentCount: Int,
    val attachmentKind: String?,
    val partsMissing: Boolean,
)

interface TextProvider {
    var queries: Int
    var rowsRead: Int
    fun maxId(kind: String): Long
    fun batch(kind: String, above: Long, also: Set<Long>, limit: Int): List<TextRecord>
    fun recent(kind: String, floorMs: Long, limit: Int, afterId: Long = 0L): List<TextRecord>
    fun history(selector: String, limit: Int): List<TextRecord>
    fun one(kind: String, id: Long): TextRecord?
}

interface LinkListener {
    fun onOpen()
    fun onMessage(text: String)
    fun onClosing()
    fun onClosed(reason: String)
    fun onFailure(reason: String)
}

interface LinkPort {
    var listener: LinkListener
    fun connect(url: String)
    fun close(reason: String)
    fun isOpen(): Boolean
}

interface AlarmPort {
    fun schedule(atMs: Long)
    fun askGrant()
}

interface WakePort {
    fun acquire(tag: String, timeoutMs: Long)
    fun release(tag: String)
}

interface SignerPort {
    fun sign(payload: Map<String, Any?>): String?
    fun publicPem(): String
}

interface EngineStore {
    fun load(): String?
    fun save(body: String)
    fun readInstall(): String? = null
    fun writeInstall(body: String) {}
}

object QueryPlan {
    const val BATCH = 50

    fun above(cursor: Long, pending: Collection<Long>): Pair<String, List<String>> {
        val ids = pending.take(BATCH)
        val selection = buildString {
            append("_id>?")
            if (ids.isNotEmpty()) {
                append(" OR _id IN (")
                append(ids.joinToString(",") { "?" })
                append(")")
            }
        }
        return selection to listOf(cursor.toString()) + ids.map { it.toString() }
    }
}

object Setup {
    fun prompts(sms: Boolean, notifications: Boolean, exact: Boolean): List<String> {
        val missing = mutableListOf<String>()
        if (!sms) missing.add("READ_SMS")
        if (!notifications) missing.add("POST_NOTIFICATIONS")
        if (!exact) missing.add("Alarms & reminders")
        return missing
    }

    fun notice(state: String): String = when (state) {
        "pairing-failed" -> "Pairing failed. Retype the 8 digits."
        "pairing" -> "Pairing"
        "needs-exact-alarm" -> "Alarms & reminders"
        else -> state
    }

    fun canHandOff(address: String, code: String): Boolean {
        return address.trim().isNotEmpty() && code.trim().isNotEmpty()
    }

    // P10-COMPANION: a stored pair must not wipe a new code while it is being typed — C1
    fun clearTypedCode(handedOff: Boolean, paired: Boolean, hasText: Boolean): Boolean {
        return handedOff && paired && hasText
    }

    fun pairIntent(address: String, code: String): HandoffIntent {
        Handoff.address = address
        Handoff.code = code
        return HandoffIntent()
    }

    fun exactAlarmIntent(packageName: String): AlarmGrantIntent {
        return AlarmGrantIntent(
            "android.settings.REQUEST_SCHEDULE_EXACT_ALARM",
            "package:$packageName",
        )
    }
}

class AlarmGrantIntent(val action: String, val data: String)

class HandoffIntent(val extras: Map<String, String>? = null)

object AddressNeedles {
    fun of(selector: String): List<String> {
        val values = linkedSetOf<String>()
        val compact = selector.filter { !it.isWhitespace() }
        if (compact.isNotEmpty()) values.add(compact)
        val canonical = DigitKey.canonical(selector)
        if (canonical != null) {
            values.add(canonical)
            if (canonical.startsWith("+")) values.add(canonical.drop(1))
            if (canonical.startsWith("+1") && canonical.length == 12) values.add(canonical.drop(2))
        }
        return values.toList()
    }
}

object Handoff {
    @Volatile var address: String? = null
    @Volatile var code: String? = null

    fun takeAddress(): String? = address.also { address = null }

    fun takeCode(): String? = code.also { code = null }
}

object CompanionStatus {
    @Volatile var paired: Boolean = false
    @Volatile var connected: Boolean = false
    @Volatile var state: String = "stopped"
    @Volatile var address: String = ""
    @Volatile var counts: String = ""
}
