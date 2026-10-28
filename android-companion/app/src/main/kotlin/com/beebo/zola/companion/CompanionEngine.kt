package com.beebo.zola.companion

import org.json.JSONArray
import org.json.JSONObject

// P10-COMPANION: one engine owns pairing, delivery, reads, and the durable seq — Phase 5

class CompanionEngine(
    private val clock: () -> Long,
    private val provider: TextProvider,
    private val link: LinkPort,
    private val alarms: AlarmPort,
    private val wakes: WakePort,
    private val signer: SignerPort,
    private val store: EngineStore,
    private val log: PhoneLogFile,
    private val writer: FrameWriter,
    private val idle: () -> IdleSample = { IdleSample(false, false, false) },
    private val canExactAlarm: () -> Boolean,
) : LinkListener {
    private var deviceId: String = ""
    private var baselineMs: Long = 0
    private var seq: Long = 1
    private var address: String = ""
    private var code: String = ""
    private var pcId: String = ""
    private var pcKey: String = ""
    private var lastPcSeq: Long = 0
    private var pairingHigh: Long = 0
    private var pairingStarted: Long = 0
    private var connecting: Boolean = false
    private var rejectedCount: Int = 0
    private var rowsSinceBaseline: Int = 0
    private var paired: Boolean = false
    private var providerReset: Int = 0
    private var permissionsHeld: Int = 0
    private var batteryExempt: Int = 0
    private val stopped = linkedSetOf<String>()
    private val highWater = mutableMapOf("sms" to 0L, "mms" to 0L)
    private val pcs = linkedMapOf<String, PcMemory>()
    private val backoff = Backoff(clock)
    private var bootstrapped = false
    private var stateLoaded = false
    private val desk = ReadDesk(clock, WakeGate(), PhoneLog())

    init {
        link.listener = this
    }

    fun boot() {
        // P10-COMPANION: a later service start must not reload over live slots — C11
        if (!stateLoaded) {
            load()
            if (!bootstrapped) openInstall()
            stateLoaded = true
        }
        publish()
        // P10-COMPANION: a service start reads above the cursor, so a text that arrived while the process was dead is not waiting on a provider change — C9
        if (paired) scanAboveCursors()
        if (paired) connectIfNeeded()
        if (paired && link.isOpen()) pcs[pcId]?.let { drain(it) }
    }

    private fun openInstall() {
            val saved = store.readInstall()?.let { JSONObject(it) }
            if (saved != null && saved.optString("device_id").isNotEmpty()) {
                deviceId = saved.getString("device_id")
                baselineMs = saved.optLong("baseline_ms")
                val sms = saved.optLong("sms_cursor")
                val mms = saved.optLong("mms_cursor")
                highWater["sms"] = sms
                highWater["mms"] = mms
                val fresh = pc()
                fresh.cursors["sms"] = sms
                fresh.cursors["mms"] = mms
            } else {
                deviceId = java.util.UUID.randomUUID().toString().replace("-", "")
                baselineMs = clock()
                val sms = provider.maxId("sms")
                val mms = provider.maxId("mms")
                highWater["sms"] = sms
                highWater["mms"] = mms
                val fresh = pc()
                fresh.cursors["sms"] = sms
                fresh.cursors["mms"] = mms
                val install = JSONObject()
                install.put("device_id", deviceId)
                install.put("baseline_ms", baselineMs)
                install.put("sms_cursor", sms)
                install.put("mms_cursor", mms)
                store.writeInstall(install.toString())
            }
            bootstrapped = true
            save()
    }

    fun handoff(host: String, typed: String) {
        if (!bootstrapped) boot()
        address = host.trim()
        code = typed.trim()
        if (!Setup.canHandOff(address, code)) {
            log.note("pairing", mapOf("result" to "missing"))
            publish()
            return
        }
        pairingHigh = 0
        pairingStarted = clock()
        CompanionStatus.state = "pairing"
        CompanionStatus.address = address
        save()
        log.note("pairing", mapOf("result" to "handed"))
        connectIfNeeded(force = true)
    }

    fun onAlarm(sample: IdleSample) {
        log.note(
            "reconnect",
            mapOf(
                "deep" to sample.deepDoze.toString(),
                "interactive" to sample.interactive.toString(),
                "charging" to sample.charging.toString(),
            ),
        )
        connectIfNeeded()
    }

    fun onNetworkUp() {
        if (!paired && code.isEmpty()) return
        connectIfNeeded()
    }

    fun onProviderChanged() {
        log.note("scan", emptyMap())
        scanAboveCursors()
    }

    private fun scanAboveCursors() {
        if (!bootstrapped) return
        checkReset("sms")
        checkReset("mms")
        if (!paired) return
        val memory = pcs[pcId] ?: return
        for (kind in listOf("sms", "mms")) {
            if (kind in stopped) continue
            val also = memory.slots.filter {
                it.kind == kind && (it.inFlight || !it.acked || it.completeness != "complete")
            }.map { it.providerId }.toSet()
            provider.batch(kind, memory.cursors[kind] ?: 0, also, QueryPlan.BATCH).forEach { admit(it, seeded = false) }
        }
    }

    fun tick() {
        val now = clock()
        if (code.isNotEmpty() && now - pairingStarted >= PAIRING_WAIT_MS) failPairing("timeout")
        val memory = pcs[pcId] ?: return
        memory.slots.filter { it.completeness == "incomplete" && !it.acked && it.outcome == null }.forEach { slot ->
            if (now - slot.since >= RETRY_MS || slot.attempts >= MAX_ATTEMPTS) {
                slot.completeness = "exhausted"
                val payload = slot.payload.toMutableMap()
                payload["completeness"] = "exhausted"
                dispatch(slot, payload)
            }
        }
    }

    fun noteDevice(permissions: Int, battery: Boolean) {
        permissionsHeld = permissions
        batteryExempt = if (battery) 1 else 0
    }

    fun deviceId(): String = deviceId

    fun seq(): Long = seq

    fun counts(): Map<String, Int> {
        val memory = pcs[pcId]
        return mapOf(
            "pending_incomplete" to (memory?.slots?.count { it.completeness == "incomplete" && !it.acked } ?: 0),
            "exhausted" to (memory?.slots?.count { it.completeness == "exhausted" } ?: 0),
            "unacked" to (memory?.slots?.count { it.inFlight && it.outcome == null } ?: 0),
            "restored" to (memory?.restored?.size ?: 0),
            "suspected_restored" to (memory?.suspected?.size ?: 0),
            "deleted" to (memory?.deleted?.size ?: 0),
            "provider_reset" to providerReset,
        )
    }

    override fun onOpen() {
        connecting = false
        CompanionStatus.connected = true
        log.note("reconnect", mapOf("socket" to "open"))
        if (!paired || code.isNotEmpty()) {
            sendPairing("phone_open", mapOf("public_pem" to signer.publicPem()))
            return
        }
        sendHello()
        sendHealth()
        resendInFlight()
        // P10-COMPANION: a verified reconnect reads above the cursor, so a text that arrived while the link was down is sent — C9
        scanAboveCursors()
        pcs[pcId]?.let { drain(it) }
    }

    override fun onMessage(text: String) {
        val json = try {
            JSONObject(text)
        } catch (_: Exception) {
            log.note("refused", mapOf("reason" to "malformed"))
            return
        }
        val payloadJson = json.optJSONObject("payload") ?: run {
            log.note("refused", mapOf("reason" to "malformed"))
            return
        }
        val payload = toMap(payloadJson)
        val signature = json.optString("signature")
        if (json.optString("kind") == "pairing") {
            val type = payload["type"]?.toString().orEmpty().ifEmpty { "unknown" }
            log.note("pairing", mapOf("type" to type, "result" to "received"))
            if (code.isEmpty() || !Intake.macMatches(code, payload, signature)) {
                log.note("refused", mapOf("reason" to "bad-signature"))
                log.note("pairing", mapOf("type" to type, "result" to "ignored", "reason" to "bad-signature"))
                if (code.isNotEmpty()) failPairing("bad-signature")
                return
            }
            val incoming = (payload["seq"] as? Number)?.toLong() ?: 0
            if (incoming <= pairingHigh) {
                log.note("refused", mapOf("reason" to "replay"))
                log.note("pairing", mapOf("type" to type, "result" to "ignored", "reason" to "replay"))
                failPairing("replay")
                return
            }
            pairingHigh = incoming
            noteVerified()
            when (type) {
                "pc_bind" -> acceptBind(payload)
                "pc_ok" -> {
                    lastPcSeq = incoming
                    acceptOk()
                }
                else -> log.note("pairing", mapOf("type" to type, "result" to "ignored", "reason" to "unexpected"))
            }
            return
        }
        val reason = Intake.classify(
            text.toByteArray(Charsets.UTF_8),
            VerifyContext(
                pairedPublic = pcKey,
                pairedDeviceId = deviceId,
                lastSeq = lastPcSeq,
                nowMs = clock(),
                pairingCode = code,
            ),
        )
        if (reason != "accept") {
            log.note("refused", mapOf("reason" to reason))
            return
        }
        lastPcSeq = (payload["seq"] as Number).toLong()
        save()
        noteVerified()
        when (payload["type"]) {
            "keepalive.ping" -> {
                val sample = idle()
                log.note(
                    "idle",
                    mapOf(
                        "deep" to sample.deepDoze.toString(),
                        "light" to sample.lightDoze.toString(),
                        "interactive" to sample.interactive.toString(),
                        "charging" to sample.charging.toString(),
                    ),
                )
                sendPong()
            }
            "messages.ack" -> onAck(payload)
            "history.read.request" -> onHistory(payload)
            "code.read.request" -> onCode(payload)
            "diagnostic_read" -> onDiagnostic(payload)
        }
        // P10-COMPANION: a verified frame drains any room in the in-flight window — C11
        pcs[pcId]?.let { drain(it) }
    }

    override fun onClosing() {
        log.note("disconnect", mapOf("reason" to "peer-closed", "who" to "phone"))
        if (link.isOpen()) link.close("peer-closed")
    }

    override fun onClosed(reason: String) {
        connecting = false
        CompanionStatus.connected = false
        wakes.release("zola:event")
        log.note("disconnect", mapOf("reason" to disconnectReason(reason), "who" to "phone"))
        if (reason == "rebind") return
        if (!paired && code.isNotEmpty()) failPairing("closed")
        armAlarm()
    }

    override fun onFailure(reason: String) {
        connecting = false
        CompanionStatus.connected = false
        log.note("disconnect", mapOf("reason" to disconnectReason(reason), "who" to "phone"))
        wakes.release("zola:event")
        wakes.release("zola:read")
        armAlarm()
    }

    private fun acceptBind(payload: Map<String, Any?>) {
        val id = payload["pc_id"]?.toString().orEmpty()
        val key = payload["public_pem"]?.toString().orEmpty()
        if (id.isEmpty() || key.isEmpty()) {
            log.note("pairing", mapOf("type" to "pc_bind", "result" to "ignored", "reason" to "missing"))
            return
        }
        val known = pcs.containsKey(id)
        pcId = id
        pcKey = key
        if (!known) openPc(id)
        sendPairing("phone_bind", mapOf("public_pem" to signer.publicPem()))
    }

    private fun acceptOk() {
        paired = true
        code = ""
        save()
        publish()
        sendHello()
        sendHealth()
        resendInFlight()
        sendSeed()
    }

    private fun openPc(id: String) {
        val now = clock()
        val floor = maxOf(baselineMs, now - DeliveryBook.WINDOW_MS)
        val rows = window("sms", floor) + window("mms", floor)
        val cursors = mapOf("sms" to provider.maxId("sms"), "mms" to provider.maxId("mms"))
        val book = DeliveryBook(baselineMs, now, rows.map { it.toTextRow() }, cursors)
        val opened = book.open(id)
        val memory = PcMemory()
        memory.cursors.putAll(cursors)
        memory.pending.addAll(opened.pending)
        memory.restored.addAll(book.restored)
        memory.suspected.addAll(book.suspected)
        pcs[id] = memory
        save()
    }

    private fun sendSeed() {
        val memory = pcs[pcId] ?: return
        if (memory.pending.isEmpty()) return
        val now = clock()
        val floor = maxOf(baselineMs, now - DeliveryBook.WINDOW_MS)
        val rows = window("sms", floor) + window("mms", floor)
        val wanted = memory.pending.toSet()
        memory.pending.clear()
        rows.filter { "${it.kind}:${it.providerId}" in wanted }.forEach { admit(it, seeded = true) }
    }

    private fun admit(row: TextRecord, seeded: Boolean) {
        if (row.kind in stopped) return
        val memory = pcs[pcId] ?: return
        val key = "${row.kind}:${row.providerId}"
        val existing = memory.slots.firstOrNull { it.key == key }
        if (!row.present) {
            if (existing == null || existing.acked || existing.outcome == "deleted") return
            existing.outcome = "deleted"
            memory.deleted.add(key)
            val payload = base(row, existing.revision, "complete", "messages.deleted")
            payload["outcome"] = "deleted"
            existing.payload = payload
            dispatch(existing, payload)
            log.note("deleted", mapOf("kind" to row.kind, "id" to hid(row.kind, row.providerId)))
            return
        }
        if (row.creator == "com.sec.android.easyMover") {
            memory.restored.add(key)
            log.note("restored", mapOf("kind" to row.kind, "id" to hid(row.kind, row.providerId)))
            save()
            return
        }
        val newest = memory.watermark[row.kind]
        if (newest != null && row.dateMs < newest - DeliveryBook.SUSPECTED_MS) {
            memory.suspected.add(key)
            log.note("suspected", mapOf("kind" to row.kind, "id" to hid(row.kind, row.providerId)))
            save()
            return
        }
        if (!row.sendable || row.direction != "in") return
        val cursor = memory.cursors[row.kind] ?: 0
        val completeness = when {
            row.partsMissing || row.senderRaw.isEmpty() -> "incomplete"
            row.kind == "mms" && row.body.isEmpty() && row.attachmentCount == 0 -> "incomplete"
            else -> "complete"
        }
        val fingerprint = listOf(row.body, completeness, row.dateMs, row.senderRaw, row.attachmentCount).joinToString("|")
        val hash = IdHash.of(fingerprint)
        val remembered = memory.revisions[key]
        val unchanged = remembered != null && remembered.substringAfter(':') == hash
        if (!seeded && existing == null && row.providerId <= cursor && (remembered == null || unchanged)) return
        val firstSight = existing == null && remembered == null
        val slot = existing ?: Slot(key, row.kind, row.providerId).also {
            memory.slots.add(it)
            if (remembered == null) rowsSinceBaseline += 1
            if (remembered != null) {
                val parts = remembered.split(':', limit = 2)
                it.revision = parts[0].toIntOrNull() ?: 1
                it.fingerprintHash = parts.getOrElse(1) { "" }
            }
        }
        if (slot.acked && hash == slot.fingerprintHash) return
        if (slot.inFlight && hash == slot.fingerprintHash) return
        slot.revision = if (slot.fingerprintHash.isEmpty() || hash == slot.fingerprintHash) {
            if (slot.fingerprintHash.isEmpty()) 1 else slot.revision
        } else {
            slot.revision + 1
        }
        slot.fingerprintHash = hash
        memory.revisions[key] = slot.revision.toString() + ":" + hash
        slot.completeness = completeness
        slot.dateMs = row.dateMs
        slot.outcome = null
        if (completeness == "incomplete") {
            if (slot.since == 0L) slot.since = clock()
            slot.attempts += 1
            if (slot.attempts >= MAX_ATTEMPTS || clock() - slot.since >= RETRY_MS) {
                slot.completeness = "exhausted"
            }
        }
        val payload = base(row, slot.revision, slot.completeness, "messages.event")
        slot.payload = payload
        if (firstSight) {
            log.note(
                "seen",
                mapOf(
                    "kind" to row.kind,
                    "id" to hid(row.kind, row.providerId),
                    "completeness" to completeness,
                ),
            )
        }
        if (slot.completeness == "incomplete") {
            save()
            log.note("incomplete", mapOf("kind" to row.kind, "id" to hid(row.kind, row.providerId), "attempts" to slot.attempts.toString()))
            return
        }
        if (slot.completeness == "exhausted") {
            log.note("exhausted", mapOf("kind" to row.kind, "id" to hid(row.kind, row.providerId)))
        } else {
            log.note("detect", mapOf("kind" to row.kind, "id" to hid(row.kind, row.providerId)))
        }
        val inFlight = memory.slots.count { it.inFlight && it.outcome == null }
        if (inFlight >= 4) {
            save()
            return
        }
        dispatch(slot, payload)
    }

    private fun dispatch(slot: Slot, payload: Map<String, Any?>): Boolean {
        val fresh = payload.toMutableMap()
        fresh["seq"] = reserveSeq()
        fresh["sent_at_ms"] = clock()
        slot.payload = fresh
        val flying = pcs[pcId]?.slots?.any { it.inFlight } == true
        slot.inFlight = true
        save()
        val signature = signer.sign(fresh)
        if (signature == null) {
            slot.inFlight = false
            save()
            log.note("sign", mapOf("result" to "failed", "id" to hid(slot.kind, slot.providerId)))
            return false
        }
        val frame = Frames.build(fresh, "signed", signature) ?: return false
        if (!flying) wakes.acquire("zola:event", 20_000)
        writer.send(frame)
        log.note("send", mapOf("type" to fresh["type"].toString(), "id" to hid(slot.kind, slot.providerId), "revision" to slot.revision.toString()))
        if (slot.completeness == "complete" || slot.completeness == "exhausted") {
            val memory = pcs[pcId]
            val current = memory?.watermark?.get(slot.kind)
            if (memory != null && (current == null || slot.dateMs > current)) memory.watermark[slot.kind] = slot.dateMs
        }
        save()
        return true
    }

    private fun resendInFlight() {
        val memory = pcs[pcId] ?: return
        memory.slots.filter { it.inFlight }.forEach { slot ->
            dispatch(slot, freshPayload(slot, memory))
        }
    }

    private fun freshPayload(slot: Slot, memory: PcMemory): Map<String, Any?> {
        val row = provider.one(slot.kind, slot.providerId)
        if (row == null || !row.present) {
            slot.outcome = "deleted"
            memory.deleted.add(slot.key)
            val payload = linkedMapOf<String, Any?>(
                "type" to "messages.deleted",
                "device_id" to deviceId,
                "contract_version" to 3,
                "provider_id" to slot.providerId.toString(),
                "kind" to slot.kind,
                "revision" to slot.revision,
                "outcome" to "deleted",
            )
            slot.payload = payload
            return payload
        }
        val payload = base(row, slot.revision, slot.completeness, "messages.event")
        slot.payload = payload
        return payload
    }

    private fun onAck(payload: Map<String, Any?>) {
        val word = payload["result"]?.toString().orEmpty()
        if (word !in CursorMachine.ACKS) return
        val kind = payload["kind"]?.toString().orEmpty()
        val id = payload["provider_id"]?.toString()?.toLongOrNull() ?: return
        val revision = (payload["revision"] as? Number)?.toInt() ?: return
        val memory = pcs[pcId] ?: return
        val slot = memory.slots.firstOrNull { it.kind == kind && it.providerId == id } ?: return
        if (slot.outcome == "deleted") {
            slot.inFlight = false
            slot.acked = true
            memory.deleted.add(slot.key)
        } else if (revision == slot.revision) {
            slot.inFlight = false
            slot.acked = true
            memory.acknowledged.add(slot.key)
            val hole = memory.slots.any { it.kind == kind && it.providerId < id && it.inFlight }
            if (!hole) memory.cursors[kind] = maxOf(memory.cursors[kind] ?: 0, id)
            if (word == "rejected") rejectedCount += 1
        } else {
            return
        }
        prune(memory)
        save()
        log.note("ack", mapOf("result" to word, "kind" to kind, "id" to hid(kind, id)))
        if (memory.slots.none { it.inFlight }) wakes.release("zola:event")
        drain(memory)
        sendHealth()
    }

    private fun prune(memory: PcMemory) {
        memory.slots.removeAll { slot ->
            slot.acked && slot.completeness == "complete" && slot.providerId <= (memory.cursors[slot.kind] ?: 0L)
        }
    }

    private fun drain(memory: PcMemory) {
        val waiting = memory.slots.filter {
            !it.inFlight && !it.acked && it.outcome == null && it.completeness != "incomplete"
        }
        for (slot in waiting) {
            if (memory.slots.count { it.inFlight && it.outcome == null } >= 4) break
            // P10-COMPANION: a slot saved to disk has no payload, so drain rebuilds it — C11
            if (slot.payload.isEmpty()) freshPayload(slot, memory)
            dispatch(slot, slot.payload)
        }
    }

    private fun onHistory(payload: Map<String, Any?>) {
        val request = payload["request_id"]?.toString().orEmpty()
        wakes.acquire("zola:read", 20_000)
        // P10-COMPANION: a read logs the wake lock it holds — C2
        log.note("wake", mapOf("tag" to "zola:read", "result" to "held"))
        try {
            val selector = payload["selector"]?.toString().orEmpty()
            val maxMessages = ((payload["max_messages"] as? Number)?.toInt() ?: 50).coerceIn(1, 50)
            val maxCharacters = ((payload["max_characters"] as? Number)?.toInt() ?: 64_000).coerceIn(1, 64_000)
            val rows = provider.history(selector, 200)
                .distinctBy { it.kind to it.providerId }
                .sortedByDescending { it.dateMs }
            val items = mutableListOf<Map<String, Any?>>()
            var used = 0
            var capped = 0
            for (row in rows) {
                if (items.size >= maxMessages) {
                    capped = 1
                    break
                }
                val prepared = Mask.prepare(row.body, row.containsOtp)
                var body = prepared.body
                var truncated = if (prepared.truncated) 1 else 0
                if (used + body.length > maxCharacters) {
                    val room = maxCharacters - used
                    if (room <= 0 || items.isNotEmpty()) {
                        capped = 1
                        break
                    }
                    body = body.take(room)
                    truncated = 1
                    capped = 1
                }
                used += body.length
                val people = row.participants.distinct()
                val item = linkedMapOf<String, Any?>(
                    "provider_id" to row.providerId.toString(),
                    "kind" to row.kind,
                    "revision" to 1,
                    "completeness" to "complete",
                    "received_at_ms" to row.dateMs,
                    "date_sent_ms" to row.dateSentMs,
                    "sender_raw" to row.senderRaw,
                    "is_group" to if (people.size > 2) 1 else 0,
                    "participant_count" to people.size,
                    "rcs_flag" to CaptureRules.rcsFlag(row.contentTypes),
                    "direction" to row.direction,
                    "truncated" to truncated,
                    "thread_id" to row.threadId,
                    "body" to body,
                )
                if (prepared.maskKind != "none") item["mask_kind"] = prepared.maskKind
                items.add(item)
                if (capped == 1) break
            }
            if (rows.size > items.size) capped = 1
            val message = baseResult("history.read.result", request)
            message["status"] = "ok"
            message["items"] = items
            message["capped"] = capped
            sendLoose(message)
            log.note("read", mapOf("type" to "history", "request" to request, "count" to items.size.toString()))
        } finally {
            wakes.release("zola:read")
            log.note("wake", mapOf("tag" to "zola:read", "result" to "released"))
        }
    }

    private fun onCode(payload: Map<String, Any?>) {
        val request = payload["request_id"]?.toString().orEmpty()
        val id = payload["provider_id"]?.toString().orEmpty()
        val kind = payload["kind"]?.toString().orEmpty()
        wakes.acquire("zola:read", 20_000)
        // P10-COMPANION: a read logs the wake lock it holds — C2
        log.note("wake", mapOf("tag" to "zola:read", "result" to "held"))
        try {
            val row = id.toLongOrNull()?.let { provider.one(kind, it) }
            val history = if (row == null) emptyList() else listOf(row.toHistory())
            val answer = desk.readExact(history, id, kind)
            val message = baseResult("code.read.result", request)
            message["status"] = answer.status
            if (answer.value != null) {
                message["value"] = answer.value
                message["value_kind"] = answer.valueKind
            }
            if (answer.reason != null) message["reason"] = answer.reason
            sendLoose(message)
            log.note("read", mapOf("type" to "exact", "request" to request, "status" to answer.status))
        } finally {
            wakes.release("zola:read")
            log.note("wake", mapOf("tag" to "zola:read", "result" to "released"))
        }
    }

    private fun onDiagnostic(payload: Map<String, Any?>) {
        val request = payload["request_id"]?.toString().orEmpty()
        wakes.acquire("zola:read", 20_000)
        // P10-COMPANION: a read logs the wake lock it holds — C2
        log.note("wake", mapOf("tag" to "zola:read", "result" to "held"))
        try {
            val message = baseResult("diagnostic_read.result", request)
            message["status"] = "ok"
            counts().forEach { message[it.key] = it.value }
            message["rows_since_baseline"] = rowsSinceBaseline
            message["rejected"] = rejectedCount
            message["cursor_lag"] = cursorLag()
            sendLoose(message)
            log.note("read", mapOf("type" to "diagnostic", "request" to request))
        } finally {
            wakes.release("zola:read")
            log.note("wake", mapOf("tag" to "zola:read", "result" to "released"))
        }
    }

    private fun sendHello() {
        val memory = pcs[pcId]
        sendLoose(
            linkedMapOf(
                "type" to "hello",
                "app_version" to "1.0.0",
                "capabilities" to listOf("receive_messages", "read_history", "read_code", "device_health", "keepalive"),
                "cursors" to (memory?.cursors?.toMap() ?: emptyMap()),
                "pending_incomplete" to counts()["pending_incomplete"],
                "notification_queue_depth" to 0,
            ),
        )
    }

    private fun sendHealth() {
        val fields = linkedMapOf<String, Any?>(
            "type" to "device.health",
            "service_state" to CompanionStatus.state,
            "permissions_held" to permissionsHeld,
            "battery_exempt" to batteryExempt,
        )
        counts().forEach { fields[it.key] = it.value }
        sendLoose(fields)
    }

    private fun sendPong() {
        sendLoose(linkedMapOf("type" to "keepalive.pong"))
    }

    private fun sendPairing(type: String, extra: Map<String, Any?>) {
        val payload = linkedMapOf<String, Any?>(
            "type" to type,
            "device_id" to deviceId,
            "seq" to reserveSeq(),
            "sent_at_ms" to clock(),
            "contract_version" to 3,
        )
        extra.forEach { payload[it.key] = it.value }
        val material = Canonical.json(payload)
        log.note(
            "pairing",
            mapOf(
                "material_bytes" to material.toByteArray(Charsets.UTF_8).size.toString(),
                "material_sha" to IdHash.of(material),
            ),
        )
        val mac = Intake.mac(code, payload)
        val frame = Frames.build(payload, "pairing", mac) ?: return
        writer.send(frame)
    }

    private fun sendLoose(fields: Map<String, Any?>) {
        var current = fields
        while (true) {
            val payload = linkedMapOf<String, Any?>(
                "type" to current["type"],
                "device_id" to deviceId,
                "seq" to reserveSeq(),
                "sent_at_ms" to clock(),
                "contract_version" to 3,
            )
            current.forEach { if (it.key != "type") payload[it.key] = it.value }
            val signature = signer.sign(payload) ?: run {
                log.note("sign", mapOf("result" to "failed"))
                return
            }
            val frame = Frames.build(payload, "signed", signature)
            if (frame != null) {
                writer.send(frame)
                return
            }
            val items = current["items"] as? List<*> ?: return
            if (items.size <= 1) return
            val next = LinkedHashMap(current)
            next["items"] = items.dropLast(1)
            next["capped"] = 1
            current = next
        }
    }

    private fun cursorLag(): Int {
        val memory = pcs[pcId] ?: return 0
        var lag = 0L
        for (kind in listOf("sms", "mms")) {
            val max = provider.maxId(kind)
            val cursor = memory.cursors[kind] ?: 0L
            if (max > cursor) lag += max - cursor
        }
        return lag.coerceAtMost(Int.MAX_VALUE.toLong()).toInt()
    }

    private fun base(row: TextRecord, revision: Int, completeness: String, type: String): MutableMap<String, Any?> {
        val people = row.participants.distinct()
        val prepared = Mask.prepare(row.body, row.containsOtp)
        val payload = linkedMapOf<String, Any?>(
            "type" to type,
            "device_id" to deviceId,
            "contract_version" to 3,
            "provider_id" to row.providerId.toString(),
            "kind" to row.kind,
            "revision" to revision,
        )
        if (type == "messages.deleted") return payload
        payload["completeness"] = completeness
        payload["received_at_ms"] = row.dateMs
        payload["date_sent_ms"] = row.dateSentMs
        payload["sender_raw"] = row.senderRaw
        payload["is_group"] = if (people.size > 2) 1 else 0
        payload["participant_count"] = people.size.coerceAtLeast(1)
        payload["rcs_flag"] = CaptureRules.rcsFlag(row.contentTypes)
        payload["attachment_has"] = if (row.attachmentCount > 0) 1 else 0
        payload["attachment_count"] = row.attachmentCount
        if (row.attachmentKind != null) payload["attachment_kind"] = row.attachmentKind
        payload["body"] = if (prepared.maskKind == "none") prepared.body else ""
        if (prepared.maskKind != "none") payload["mask_kind"] = prepared.maskKind
        payload["truncated"] = if (prepared.truncated) 1 else 0
        return payload
    }

    private fun baseResult(type: String, request: String) = linkedMapOf<String, Any?>(
        "type" to type,
        "request_id" to request,
    )

    private fun reserveSeq(): Long {
        val current = seq
        seq = current + 1
        save()
        return current
    }

    private fun connectIfNeeded(force: Boolean = false) {
        if (address.isEmpty()) return
        if (!paired && code.isEmpty()) return
        if (!force && CompanionStatus.state == "pairing-failed" && code.isEmpty()) return
        // P10-COMPANION: a typed code replaces a live session — C1
        if (force && link.isOpen()) link.close("rebind")
        if (force) connecting = false
        if (link.isOpen() || connecting) return
        connecting = true
        try {
            link.connect(CompanionService.linkUrl(address))
        } catch (_: RuntimeException) {
            connecting = false
            log.note("disconnect", mapOf("reason" to "bad-address"))
        }
    }

    private fun window(kind: String, floor: Long): List<TextRecord> {
        val all = mutableListOf<TextRecord>()
        var after = 0L
        while (true) {
            val page = provider.recent(kind, floor, QueryPlan.BATCH, after)
            if (page.isEmpty()) break
            all.addAll(page)
            val next = page.maxOf { it.providerId }
            if (page.size < QueryPlan.BATCH || next <= after) break
            after = next
        }
        return all
    }

    private fun failPairing(reason: String) {
        code = ""
        CompanionStatus.state = "pairing-failed"
        log.note("pairing", mapOf("result" to "failed", "reason" to reason))
        publish()
        if (reason == "timeout" && link.isOpen()) link.close("failure")
    }

    private fun disconnectReason(reason: String): String {
        if (reason == "rebind") return "superseded"
        return if (reason in DISCONNECT_REASONS) reason else "failure"
    }

    private fun hid(kind: String, id: Long): String = IdHash.of("$kind:$id")

    private fun noteVerified() {
        backoff.reset()
    }

    private fun armAlarm() {
        if (!canExactAlarm()) {
            alarms.askGrant()
            CompanionStatus.state = "needs-exact-alarm"
            log.note("alarm", mapOf("result" to "ask"))
            publish()
            return
        }
        alarms.schedule(backoff.scheduleReconnect())
    }

    private fun checkReset(kind: String) {
        val max = provider.maxId(kind)
        val seen = highWater[kind] ?: 0
        if (max > seen) {
            highWater[kind] = max
            save()
            return
        }
        if (max < seen && stopped.add(kind)) {
            providerReset += 1
            log.note("provider-reset", mapOf("kind" to kind))
            save()
            if (paired) sendHealth()
        }
    }

    private fun pc(): PcMemory = pcs.getOrPut("install") { PcMemory() }

    private fun publish() {
        CompanionStatus.paired = paired
        CompanionStatus.address = address
        if (CompanionStatus.state != "needs-exact-alarm") {
            val current = CompanionStatus.state
            CompanionStatus.state = when {
                code.isNotEmpty() -> "pairing"
                current == "pairing-failed" -> "pairing-failed"
                paired && CompanionStatus.connected -> "connected"
                paired -> "paired"
                else -> "stopped"
            }
        }
        CompanionStatus.counts = counts().entries.joinToString(",") { it.key + "=" + it.value }
    }

    private fun load() {
        val text = store.load() ?: return
        val root = JSONObject(text)
        deviceId = root.optString("device_id")
        baselineMs = root.optLong("baseline_ms")
        seq = root.optLong("seq", 1)
        address = root.optString("address")
        pcId = root.optString("pc_id")
        pcKey = root.optString("pc_key")
        lastPcSeq = root.optLong("last_pc_seq")
        paired = root.optBoolean("paired")
        providerReset = root.optInt("provider_reset")
        rejectedCount = root.optInt("rejected")
        rowsSinceBaseline = root.optInt("rows_since_baseline")
        val water = root.optJSONObject("high_water")
        if (water != null) {
            val names = water.keys()
            while (names.hasNext()) {
                val name = names.next()
                highWater[name] = water.getLong(name)
            }
        }
        bootstrapped = deviceId.isNotEmpty()
        stopped.clear()
        val stoppedJson = root.optJSONArray("stopped")
        if (stoppedJson != null) {
            for (index in 0 until stoppedJson.length()) stopped.add(stoppedJson.getString(index))
        }
        pcs.clear()
        val all = root.optJSONObject("pcs") ?: return
        val names = all.keys()
        while (names.hasNext()) {
            val name = names.next()
            pcs[name] = PcMemory.from(all.getJSONObject(name))
        }
    }

    private fun save() {
        val root = JSONObject()
        root.put("device_id", deviceId)
        root.put("baseline_ms", baselineMs)
        root.put("seq", seq)
        root.put("address", address)
        root.put("pc_id", pcId)
        root.put("pc_key", pcKey)
        root.put("last_pc_seq", lastPcSeq)
        root.put("paired", paired)
        root.put("provider_reset", providerReset)
        root.put("rejected", rejectedCount)
        root.put("rows_since_baseline", rowsSinceBaseline)
        root.put("high_water", JSONObject(highWater as Map<*, *>))
        val stoppedJson = JSONArray()
        stopped.forEach { stoppedJson.put(it) }
        root.put("stopped", stoppedJson)
        val all = JSONObject()
        pcs.forEach { all.put(it.key, it.value.toJson()) }
        root.put("pcs", all)
        store.save(root.toString())
        publish()
    }

    companion object {
        const val RETRY_MS = 600_000L
        const val MAX_ATTEMPTS = 20
        const val PAIRING_WAIT_MS = 30_000L
        val DISCONNECT_REASONS = setOf(
            "pong-missed",
            "peer-closed",
            "network-lost",
            "failure",
            "pc-shutdown",
            "phone-shutdown",
            "superseded",
        )
    }
}

private class Slot(
    val key: String,
    val kind: String,
    val providerId: Long,
    var revision: Int = 1,
    var completeness: String = "complete",
    var fingerprintHash: String = "",
    var inFlight: Boolean = false,
    var attempts: Int = 0,
    var since: Long = 0,
    var outcome: String? = null,
    var dateMs: Long = 0,
    var acked: Boolean = false,
    var payload: Map<String, Any?> = emptyMap(),
)

private class PcMemory {
    val cursors = mutableMapOf("sms" to 0L, "mms" to 0L)
    val pending = linkedSetOf<String>()
    val acknowledged = linkedSetOf<String>()
    val restored = linkedSetOf<String>()
    val suspected = linkedSetOf<String>()
    val deleted = linkedSetOf<String>()
    val revisions = linkedMapOf<String, String>()
    val watermark = mutableMapOf<String, Long>()
    val slots = mutableListOf<Slot>()

    fun toJson(): JSONObject {
        val json = JSONObject()
        json.put("cursors", JSONObject(cursors as Map<*, *>))
        json.put("pending", JSONArray(pending.toList()))
        json.put("acknowledged", JSONArray(acknowledged.toList()))
        json.put("restored", JSONArray(restored.toList()))
        json.put("suspected", JSONArray(suspected.toList()))
        json.put("deleted", JSONArray(deleted.toList()))
        json.put("revisions", JSONObject(revisions as Map<*, *>))
        json.put("watermark", JSONObject(watermark as Map<*, *>))
        val array = JSONArray()
        slots.forEach { slot ->
            val item = JSONObject()
            item.put("key", slot.key)
            item.put("kind", slot.kind)
            item.put("provider_id", slot.providerId)
            item.put("revision", slot.revision)
            item.put("completeness", slot.completeness)
            item.put("fingerprint_hash", slot.fingerprintHash)
            item.put("in_flight", slot.inFlight)
            item.put("attempts", slot.attempts)
            item.put("since", slot.since)
            item.put("outcome", slot.outcome ?: "")
            item.put("date_ms", slot.dateMs)
            item.put("acked", slot.acked)
            array.put(item)
        }
        json.put("slots", array)
        return json
    }

    companion object {
        fun from(json: JSONObject): PcMemory {
            val memory = PcMemory()
            val cursors = json.optJSONObject("cursors")
            if (cursors != null) {
                val names = cursors.keys()
                while (names.hasNext()) {
                    val name = names.next()
                    memory.cursors[name] = cursors.getLong(name)
                }
            }
            copy(json.optJSONArray("pending"), memory.pending)
            copy(json.optJSONArray("acknowledged"), memory.acknowledged)
            copy(json.optJSONArray("restored"), memory.restored)
            copy(json.optJSONArray("suspected"), memory.suspected)
            copy(json.optJSONArray("deleted"), memory.deleted)
            val revisions = json.optJSONObject("revisions")
            if (revisions != null) {
                val names = revisions.keys()
                while (names.hasNext()) {
                    val name = names.next()
                    memory.revisions[name] = revisions.getString(name)
                }
            }
            val watermark = json.optJSONObject("watermark")
            if (watermark != null) {
                val names = watermark.keys()
                while (names.hasNext()) {
                    val name = names.next()
                    memory.watermark[name] = watermark.getLong(name)
                }
            }
            val slots = json.optJSONArray("slots")
            if (slots != null) {
                for (index in 0 until slots.length()) {
                    val item = slots.getJSONObject(index)
                    val slot = Slot(item.getString("key"), item.getString("kind"), item.getLong("provider_id"))
                    slot.revision = item.optInt("revision", 1)
                    slot.completeness = item.optString("completeness", "complete")
                    val storedHash = item.optString("fingerprint_hash")
                    slot.fingerprintHash = if (storedHash.isNotEmpty()) {
                        storedHash
                    } else {
                        val raw = item.optString("fingerprint")
                        if (raw.isEmpty()) "" else IdHash.of(raw)
                    }
                    slot.inFlight = item.optBoolean("in_flight")
                    slot.attempts = item.optInt("attempts")
                    slot.since = item.optLong("since")
                    slot.outcome = item.optString("outcome").ifEmpty { null }
                    slot.dateMs = item.optLong("date_ms")
                    slot.acked = item.optBoolean("acked")
                    memory.slots.add(slot)
                }
            }
            return memory
        }

        private fun copy(array: JSONArray?, into: MutableSet<String>) {
            if (array == null) return
            for (index in 0 until array.length()) into.add(array.getString(index))
        }
    }
}

private fun TextRecord.toTextRow() = TextRow(
    providerId.toString(),
    kind,
    dateMs,
    creator,
    1,
    sendable,
    present,
)

private object IdHash {
    fun of(material: String): String {
        val digest = java.security.MessageDigest.getInstance("SHA-256").digest(material.toByteArray(Charsets.UTF_8))
        return digest.take(8).joinToString("") { "%02x".format(it) }
    }
}

private fun TextRecord.toHistory() = HistoryRow(
    providerId.toString(),
    kind,
    1,
    dateMs,
    senderRaw,
    body,
    direction,
    threadId,
    participants,
    containsOtp,
)
