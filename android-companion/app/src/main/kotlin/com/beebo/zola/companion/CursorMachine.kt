package com.beebo.zola.companion

// P10-COMPANION: cursors, resends, and the deleted notice live here — P10-D03

data class SeenRow(
    val kind: String,
    val providerId: Long,
    val revision: Int,
    val completeness: String,
    val present: Boolean,
    val dateMs: Long,
    val creator: String,
    val body: String = "",
    val direction: String = "in",
    val sendable: Boolean = true,
    val containsOtp: Boolean = false,
    val rcsFlag: String = "unknown",
)

data class Outgoing(
    val seq: Long,
    val type: String,
    val providerId: String,
    val kind: String,
    val revision: Int,
    val completeness: String,
    val outcome: String?,
    val body: String,
    val maskKind: String,
    val truncated: Boolean,
)

class CursorMachine(private val clock: () -> Long) {
    var deviceId: String = ""
        private set
    var baselineMs: Long = 0
        private set
    var baselined: Boolean = false
        private set
    var seq: Long = 0
        private set
    val cursors = mutableMapOf("sms" to 0L, "mms" to 0L)
    val stopped = linkedSetOf<String>()
    val watermark = mutableMapOf<String, Long>()
    val suspected = linkedSetOf<String>()
    val restored = linkedSetOf<String>()
    val deletedWaiting = linkedSetOf<String>()
    var providerResetCount: Int = 0
        private set
    var exhaustedCount: Int = 0
        private set

    private val slots = linkedMapOf<String, Slot>()

    fun baseline(deviceId: String, smsMax: Long, mmsMax: Long, now: Long): Boolean {
        if (baselined) return false
        this.deviceId = deviceId
        baselineMs = now
        cursors["sms"] = smsMax
        cursors["mms"] = mmsMax
        baselined = true
        return true
    }

    fun rePair() {
        // seq and the baseline stay. A new PC identity does not reset them.
    }

    fun adoptSeq(value: Long) {
        if (value > seq) seq = value
    }

    fun providerReset(kind: String, newMax: Long) {
        val cursor = cursors[kind] ?: return
        if (newMax < cursor) {
            if (stopped.add(kind)) providerResetCount += 1
        }
    }

    fun noteDelivered(kind: String, dateMs: Long) {
        val current = watermark[kind]
        if (current == null || dateMs > current) watermark[kind] = dateMs
    }

    fun admit(row: SeenRow, historical: Boolean = false): List<Outgoing> {
        if (row.kind in stopped) return emptyList()
        val key = key(row.kind, row.providerId)
        if (!row.present) {
            val slot = slots[key] ?: return emptyList()
            if (slot.ackedDeleted) return emptyList()
            val waiting = slot.inFlight || slot.ackedRevision < 0
            if (!waiting) return emptyList()
            slot.present = false
            slot.outcome = "deleted"
            slot.body = ""
            slot.maskKind = "none"
            slot.inFlight = true
            deletedWaiting.add(key)
            return listOf(emit(slot))
        }
        if (row.creator in RESTORE) {
            restored.add(key)
            return emptyList()
        }
        val newest = watermark[row.kind]
        if (newest != null && row.dateMs < newest - DeliveryBook.SUSPECTED_MS) {
            suspected.add(key)
            return emptyList()
        }
        if (!row.sendable || row.direction != "in") return emptyList()
        val cursor = cursors[row.kind] ?: 0L
        val existing = slots[key]
        if (!historical && row.providerId <= cursor && existing == null) return emptyList()
        if (existing != null && row.revision <= existing.ackedRevision) return emptyList()
        if (existing != null && row.revision < existing.revision) return emptyList()
        if (existing != null && row.revision == existing.revision && (existing.inFlight || existing.ackedRevision >= row.revision)) {
            return emptyList()
        }
        val prepared = Mask.prepare(row.body, row.containsOtp)
        val slot = existing ?: Slot(key, row.kind, row.providerId.toString())
        slot.revision = row.revision
        slot.completeness = row.completeness
        slot.body = prepared.body
        slot.maskKind = prepared.maskKind
        slot.truncated = prepared.truncated
        slot.present = true
        slot.dateMs = row.dateMs
        slot.outcome = null
        if (row.completeness == "incomplete") {
            if (existing == null) {
                slot.attempts = 0
                slot.nextRetryAt = clock() + RETRY_MS
            }
            slots[key] = slot
            return pump()
        }
        slot.inFlight = false
        slots[key] = slot
        return pump()
    }

    fun onClock(now: Long): List<Outgoing> {
        slots.values.filter { it.present && it.completeness == "incomplete" && it.outcome == null }.forEach { slot ->
            if (now < slot.nextRetryAt || slot.attempts >= MAX_ATTEMPTS) return@forEach
            slot.attempts += 1
            slot.nextRetryAt = now + RETRY_MS
            if (slot.attempts >= MAX_ATTEMPTS) {
                slot.completeness = "exhausted"
                exhaustedCount += 1
            }
        }
        return pump()
    }

    fun ack(kind: String, providerId: String, revision: Int, word: String): Boolean {
        if (word !in ACKS) return false
        val id = providerId.toLongOrNull() ?: return false
        val slot = slots[key(kind, id)] ?: return false
        if (slot.outcome == "deleted") {
            slot.ackedDeleted = true
            slot.inFlight = false
            deletedWaiting.remove(slot.key)
            return true
        }
        if (revision != slot.revision) return false
        slot.ackedRevision = revision
        slot.inFlight = false
        return true
    }

    fun resendInFlight(): List<Outgoing> {
        return slots.values.filter { it.inFlight }.map { emit(it) }
    }

    fun unackedCount(): Int = slots.values.count { it.inFlight && it.outcome != "deleted" }

    private fun pump(): List<Outgoing> {
        val ready = slots.values.filter { slot ->
            slot.present && slot.outcome == null && !slot.inFlight && slot.revision > slot.ackedRevision &&
                (slot.completeness == "complete" || slot.completeness == "exhausted")
        }.sortedBy { it.providerId.toLong() }
        val sent = mutableListOf<Outgoing>()
        for (slot in ready) {
            if (unackedCount() >= WINDOW) break
            slot.inFlight = true
            sent.add(emit(slot))
        }
        return sent
    }

    private fun emit(slot: Slot): Outgoing {
        seq += 1
        val deleted = slot.outcome == "deleted"
        if (!deleted && (slot.completeness == "complete" || slot.completeness == "exhausted")) {
            noteDelivered(slot.kind, slot.dateMs)
        }
        return Outgoing(
            seq = seq,
            type = if (deleted) "messages.deleted" else "messages.event",
            providerId = slot.providerId,
            kind = slot.kind,
            revision = slot.revision,
            completeness = if (deleted) "complete" else slot.completeness,
            outcome = slot.outcome,
            body = if (deleted || slot.maskKind != "none") "" else slot.body,
            maskKind = if (deleted) "none" else slot.maskKind,
            truncated = if (deleted) false else slot.truncated,
        )
    }

    private fun key(kind: String, providerId: Long) = "$kind:$providerId"

    private class Slot(
        val key: String,
        val kind: String,
        val providerId: String,
        var revision: Int = 0,
        var completeness: String = "incomplete",
        var body: String = "",
        var maskKind: String = "none",
        var truncated: Boolean = false,
        var present: Boolean = true,
        var dateMs: Long = 0,
        var attempts: Int = 0,
        var nextRetryAt: Long = 0,
        var ackedRevision: Int = -1,
        var inFlight: Boolean = false,
        var outcome: String? = null,
        var ackedDeleted: Boolean = false,
    )

    companion object {
        const val WINDOW = 4
        const val RETRY_MS = 600_000L
        const val MAX_ATTEMPTS = 20
        val ACKS = setOf("stored", "updated", "duplicate", "suppressed", "rejected")
        val RESTORE = setOf("com.sec.android.easyMover")
    }
}
