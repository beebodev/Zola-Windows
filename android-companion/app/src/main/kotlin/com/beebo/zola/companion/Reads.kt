package com.beebo.zola.companion

// P10-COMPANION: the digit key finds a row and is not kept — P10-D10

object DigitKey {
    fun canonical(raw: String): String? {
        val spaced = raw.filter { !it.isWhitespace() }
        if (spaced.isEmpty()) return null
        val lead = if (spaced.startsWith("+")) "+" else ""
        val rest = if (lead.isEmpty()) spaced else spaced.drop(1)
        val digits = StringBuilder()
        for (ch in rest) {
            when {
                ch in '0'..'9' -> digits.append(ch)
                ch.isLetter() -> return null
                else -> Unit
            }
        }
        val body = digits.toString()
        if (body.isEmpty()) return null
        if (lead == "+" && body.length in 8..15) return "+$body"
        if (lead.isEmpty() && body.length == 10) return "+1$body"
        if (lead.isEmpty() && body.length == 11 && body.startsWith("1")) return "+$body"
        return null
    }

    fun same(query: String, stored: String): Boolean {
        val left = canonical(query) ?: return false
        val right = canonical(stored) ?: return false
        return left == right
    }
}

data class HistoryRow(
    val providerId: String,
    val kind: String,
    val revision: Int,
    val receivedAtMs: Long,
    val senderRaw: String,
    val body: String,
    val direction: String,
    val threadId: String,
    val participants: List<String>,
    val containsOtp: Boolean = false,
    val completeness: String = "complete",
)

data class HistoryItem(
    val providerId: String,
    val kind: String,
    val revision: Int,
    val receivedAtMs: Long,
    val senderRaw: String,
    val body: String,
    val direction: String,
    val threadId: String,
    val isGroup: Boolean,
    val participantCount: Int,
    val maskKind: String,
    val truncated: Boolean,
    val completeness: String,
)

data class CodeAnswer(
    val status: String,
    val value: String?,
    val valueKind: String?,
    val reason: String?,
)

class ReadDesk(private val clock: () -> Long, private val locks: WakeGate, private val log: PhoneLog) {
    fun history(rows: List<HistoryRow>, query: String, messageLimit: Int = 50, charLimit: Int = 64000): List<HistoryItem> {
        return locks.hold("zola:read") {
            val capMessages = messageLimit.coerceAtMost(50)
            val capChars = charLimit.coerceAtMost(64000)
            val matched = rows.filter { row ->
                row.participants.any { DigitKey.same(query, it) } || DigitKey.same(query, row.senderRaw)
            }
            val items = mutableListOf<HistoryItem>()
            var chars = 0
            for (row in matched) {
                if (items.size >= capMessages) break
                val prepared = Mask.prepare(row.body, row.containsOtp)
                if (items.isNotEmpty() && chars + prepared.body.length > capChars) break
                if (items.isEmpty() && prepared.body.length > capChars) {
                    items.add(item(row, prepared.copy(body = prepared.body.take(capChars), truncated = true)))
                    break
                }
                chars += prepared.body.length
                items.add(item(row, prepared))
            }
            items
        }
    }

    fun readExact(rows: List<HistoryRow>, providerId: String, kind: String): CodeAnswer {
        return locks.hold("zola:read") {
            val now = clock()
            val row = rows.firstOrNull { it.providerId == providerId && it.kind == kind }
            if (row == null || row.receivedAtMs < now - DAY_MS) {
                return@hold CodeAnswer("refused", null, null, "not_identifiable")
            }
            val mask = Mask.kind(row.body, row.containsOtp)
            if (mask == "none" || mask == "unsure") {
                return@hold CodeAnswer("refused", null, null, "not_identifiable")
            }
            val value = Mask.extract(row.body, mask) ?: return@hold CodeAnswer("refused", null, null, "not_identifiable")
            CodeAnswer("ok", value, if (mask == "reset_link") "link" else "code", null)
        }
    }

    fun readCode(rows: List<HistoryRow>, query: String): CodeAnswer {
        return locks.hold("zola:read") {
            val now = clock()
            val row = rows.filter { candidate ->
                (DigitKey.same(query, candidate.senderRaw) || candidate.participants.any { DigitKey.same(query, it) }) &&
                    candidate.receivedAtMs >= now - DAY_MS
            }.maxByOrNull { it.receivedAtMs }
            if (row == null) return@hold CodeAnswer("refused", null, null, "not_identifiable")
            val kind = Mask.kind(row.body, row.containsOtp)
            if (kind == "none" || kind == "unsure") {
                return@hold CodeAnswer("refused", null, null, "not_identifiable")
            }
            val value = Mask.extract(row.body, kind) ?: return@hold CodeAnswer("refused", null, null, "not_identifiable")
            val valueKind = if (kind == "reset_link") "link" else "code"
            CodeAnswer("ok", value, valueKind, null)
        }
    }

    fun diagnostic(counts: Map<String, Int>): Map<String, Int> {
        return locks.hold("zola:read") {
            counts.filterKeys { it in DIAGNOSTIC }
        }
    }

    private fun item(row: HistoryRow, prepared: Prepared): HistoryItem {
        val people = row.participants.distinct()
        return HistoryItem(
            providerId = row.providerId,
            kind = row.kind,
            revision = row.revision,
            receivedAtMs = row.receivedAtMs,
            senderRaw = row.senderRaw,
            body = prepared.body,
            direction = row.direction,
            threadId = row.threadId,
            isGroup = people.size > 2,
            participantCount = people.size,
            maskKind = prepared.maskKind,
            truncated = prepared.truncated,
            completeness = row.completeness,
        )
    }

    companion object {
        const val DAY_MS = 86_400_000L
        val DIAGNOSTIC = setOf(
            "rows_since_baseline",
            "pending_incomplete",
            "exhausted",
            "unacked",
            "rejected",
            "restored",
            "suspected_restored",
            "deleted",
            "provider_reset",
            "cursor_lag",
        )
    }
}

class PhoneLog {
    val lines = mutableListOf<String>()

    fun note(event: String, fields: Map<String, String>) {
        lines.add(event + " " + fields.entries.joinToString(" ") { it.key + "=" + it.value })
    }
}
