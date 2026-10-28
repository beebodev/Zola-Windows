package com.beebo.zola.companion

// P10-COMPANION: delivery state belongs to a PC identity, not to a key — P10-D03

data class TextRow(
    val providerId: String,
    val kind: String,
    val dateMs: Long,
    val creator: String,
    val revision: Int,
    val sendable: Boolean,
    val present: Boolean = true,
)

data class PcDelivery(
    val cursors: MutableMap<String, Long>,
    val pending: MutableSet<String>,
    val unacked: MutableSet<String>,
    val acknowledged: MutableSet<String>,
    val deleted: MutableSet<String>,
)

class DeliveryBook(
    val baselineMs: Long,
    private val nowMs: Long,
    private val rows: List<TextRow>,
    private val maxIds: Map<String, Long>,
    private val restoreCreators: Set<String> = setOf("com.sec.android.easyMover"),
) {
    val watermark = mutableMapOf<String, Long>()
    val suspected = linkedSetOf<String>()
    val restored = linkedSetOf<String>()
    val stopped = linkedSetOf<String>()
    private val byPc = linkedMapOf<String, PcDelivery>()

    fun open(pcId: String): PcDelivery {
        byPc[pcId]?.let { return it }
        val floor = maxOf(baselineMs, nowMs - WINDOW_MS)
        val state = PcDelivery(
            cursors = maxIds.mapValues { it.value }.toMutableMap(),
            pending = linkedSetOf(),
            unacked = linkedSetOf(),
            acknowledged = linkedSetOf(),
            deleted = linkedSetOf(),
        )
        rows.filter { it.present && it.sendable && it.dateMs >= floor }.forEach { row ->
            when (classify(row)) {
                "send" -> state.pending.add(key(row))
                "restored" -> restored.add(key(row))
                "suspected_restored" -> suspected.add(key(row))
            }
        }
        byPc[pcId] = state
        return state
    }

    fun classify(row: TextRow): String {
        if (row.creator in restoreCreators) return "restored"
        val newest = watermark[row.kind] ?: return "send"
        if (row.dateMs < newest - SUSPECTED_MS) return "suspected_restored"
        return "send"
    }

    fun noteDelivered(kind: String, dateMs: Long) {
        val current = watermark[kind]
        if (current == null || dateMs > current) watermark[kind] = dateMs
    }

    fun providerReset(kind: String) {
        stopped.add(kind)
    }

    fun deletedBeforeAck(pcId: String, row: TextRow) {
        val state = open(pcId)
        val id = key(row)
        if (id !in state.pending && id !in state.unacked) return
        state.pending.remove(id)
        state.unacked.remove(id)
        state.deleted.add(id)
    }

    fun acknowledgeDeleted(pcId: String, row: TextRow) {
        open(pcId).deleted.remove(key(row))
    }

    private fun key(row: TextRow) = row.kind + ":" + row.providerId

    companion object {
        const val WINDOW_MS = 604_800_000L
        const val SUSPECTED_MS = 172_800_000L
    }
}
