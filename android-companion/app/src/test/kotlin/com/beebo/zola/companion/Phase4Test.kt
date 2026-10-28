package com.beebo.zola.companion

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class Phase4Test {
    @Test
    fun goldenVectorsMatchPythonOrder() {
        val vectors = JSONObject(contractFile("phone_vectors.json").readText())
        val keys = JSONObject(contractFile("phone_test_keys.json").readText())
        val protocol = JSONObject(contractFile("phone_protocol.json").readText())
        val pcTypes = pcToPhone(protocol)
        val cases = vectors.getJSONArray("cases")
        for (index in 0 until cases.length()) {
            val case = cases.getJSONObject(index)
            val got = Intake.decide(case, keys, vectors)
            assertEquals(case.getString("name"), case.getString("expect"), got)
            val type = case.optJSONObject("payload")?.optString("type").orEmpty()
            if (type in pcTypes && got != "accept") {
                assertTrue(case.getString("expect") in protocol.getJSONArray("rejection_reasons").let { reasons ->
                    (0 until reasons.length()).map { reasons.getString(it) }.toSet() + "too-large"
                })
            }
        }
    }

    @Test
    fun pairingMacAgrees() {
        val payload = mapOf("type" to "phone_open", "device_id" to "d", "seq" to 1, "sent_at_ms" to 5, "contract_version" to 3)
        val mac = Intake.mac("00000000", payload)
        assertTrue(Intake.macMatches("00000000", payload, mac))
        assertFalse(Intake.macMatches("00000000", payload, "AAAA"))
    }

    @Test
    fun cursorWalk() {
        var now = 1_000L
        val machine = CursorMachine { now }
        assertTrue(machine.baseline("device", 10, 10, now))
        assertFalse(machine.baseline("other", 1, 1, now))
        assertEquals(10L, machine.cursors["sms"])

        assertTrue(machine.admit(row(11, revision = 2, completeness = "incomplete")).isEmpty())
        val edited = machine.admit(row(11, revision = 3, body = "hello"))
        assertEquals(3, edited.single().revision)
        assertTrue(machine.ack("sms", "11", 3, "updated"))

        val first = machine.admit(row(12, body = "one"))
        val again = machine.resendInFlight().first { it.providerId == "12" }
        assertTrue(again.seq > first.single().seq)
        assertEquals(first.single().revision, again.revision)
        val deleted = machine.admit(row(12, present = false))
        assertEquals("deleted", deleted.single().outcome)
        assertEquals("", deleted.single().body)
        assertEquals("messages.deleted", deleted.single().type)
        assertEquals(1, machine.resendInFlight().count { it.providerId == "12" && it.outcome == "deleted" })
        assertTrue(machine.ack("sms", "12", 1, "suppressed"))
        assertTrue(machine.resendInFlight().none { it.providerId == "12" })

        assertTrue(machine.admit(row(13, completeness = "incomplete")).none { it.providerId == "13" })
        assertEquals("14", machine.admit(row(14, body = "after")).single().providerId)
        assertTrue(machine.ack("sms", "14", 1, "stored"))

        machine.admit(row(15, completeness = "incomplete"))
        var exhausted: Outgoing? = null
        repeat(20) {
            now += CursorMachine.RETRY_MS
            exhausted = machine.onClock(now).firstOrNull { it.providerId == "15" } ?: exhausted
        }
        assertEquals("exhausted", exhausted!!.completeness)
        val finished = machine.admit(row(15, revision = 2, body = "done"))
        assertEquals(2, finished.single().revision)
        assertEquals("complete", finished.single().completeness)
        assertTrue(machine.ack("sms", "15", 2, "stored"))

        val held = machine.admit(row(16, body = "hold"))
        val next = machine.admit(row(17, body = "next"))
        assertTrue(held.isNotEmpty())
        assertEquals("17", next.single().providerId)

        val before = machine.seq
        machine.rePair()
        assertTrue(machine.admit(row(18, body = "repair")).single().seq > before)

        val words = CursorMachine { now }
        words.baseline("device", 0, 0, now)
        for (word in CursorMachine.ACKS) {
            val id = (30 + CursorMachine.ACKS.indexOf(word)).toLong()
            val sent = words.admit(row(id, body = word)).single()
            assertTrue(words.ack("sms", sent.providerId, sent.revision, word))
            assertTrue(words.resendInFlight().none { it.providerId == sent.providerId && it.outcome == null })
        }
    }

    @Test
    fun windowStopsAtFour() {
        val machine = CursorMachine { 0L }
        machine.baseline("device", 0, 0, 0)
        val sent = (1..5).flatMap { machine.admit(row(it.toLong(), body = "m$it")) }
        assertEquals(4, sent.size)
        assertTrue(machine.ack("sms", "1", 1, "stored"))
        val rest = machine.resendInFlight()
        assertTrue(rest.none { it.providerId == "5" })
        val fifth = machine.admit(row(5, body = "m5"))
        assertEquals("5", fifth.single().providerId)
    }

    @Test
    fun providerResetDoesNotLowerTheCursor() {
        val machine = CursorMachine { 0L }
        machine.baseline("device", 100, 80, 0)
        machine.providerReset("sms", 40)
        assertEquals(100L, machine.cursors["sms"])
        assertEquals(1, machine.providerResetCount)
        assertTrue(machine.admit(row(101, body = "nope")).isEmpty())
    }

    @Test
    fun restoreAndSuspectedStayUnsent() {
        val machine = CursorMachine { 0L }
        machine.baseline("device", 0, 0, 0)
        machine.noteDelivered("sms", 1_000_000_000_000L)
        assertTrue(machine.admit(row(21, creator = "com.sec.android.easyMover")).isEmpty())
        assertTrue("sms:21" in machine.restored)
        val old = 1_000_000_000_000L - DeliveryBook.SUSPECTED_MS - 1
        assertTrue(machine.admit(row(22, dateMs = old)).isEmpty())
        assertTrue("sms:22" in machine.suspected)
        machine.noteDelivered("sms", old)
        assertEquals(1_000_000_000_000L, machine.watermark["sms"])
    }

    @Test
    fun blockedAndSentTextsAreNotEvents() {
        val machine = CursorMachine { 0L }
        machine.baseline("device", 0, 0, 0)
        assertTrue(machine.admit(row(23, sendable = false, body = "blocked")).isEmpty())
        assertTrue(machine.admit(row(24, direction = "out", body = "mine")).isEmpty())
    }

    @Test
    fun maskNeverReachesTheFrameOrTheLog() {
        val machine = CursorMachine { 0L }
        machine.baseline("device", 0, 0, 0)
        val sent = machine.admit(row(25, body = "Your code is 482913"))
        assertEquals("", sent.single().body)
        assertEquals("verification_code", sent.single().maskKind)
        val log = PhoneLog()
        log.note("mask", mapOf("kind" to sent.single().maskKind))
        assertFalse(log.lines.any { "482913" in it })
        val huge = machine.admit(row(26, body = "y".repeat(16001)))
        assertTrue(huge.single().truncated)
        assertEquals(16000, huge.single().body.length)
        val hidden = machine.admit(row(27, body = "x".repeat(16001) + " code 482913"))
        assertEquals("", hidden.single().body)
        assertEquals("verification_code", hidden.single().maskKind)
    }

    @Test
    fun frameCeilingAndLoneSurrogate() {
        val huge = Frames.build(mapOf("pad" to "x".repeat(300_000)), "signed", "sig")
        assertNull(huge)
        val text = Canonical.json(mapOf("text" to "\uD800"))
        assertEquals("{\"text\":\"\uFFFD\"}", text)
        assertFalse(Canonical.bytes(mapOf("text" to "\uD800")).contains(0xED.toByte()))
    }

    @Test
    fun readsWakeLocksAndRefusals() {
        val locks = WakeGate()
        val log = PhoneLog()
        var now = 2_000_000_000_000L
        val desk = ReadDesk({ now }, locks, log)
        val rows = listOf(
            HistoryRow("1", "sms", 1, now - 1000, "+1 555-123-4567", "See you at 6:30", "in", "t1", listOf("+15551234567")),
            HistoryRow("2", "sms", 1, now - 1000, "+15551234567", "sent it", "out", "t1", listOf("+15551234567")),
            HistoryRow("3", "mms", 1, now - 1000, "other", "group", "in", "t2", listOf("+15551234567", "a", "b")),
            HistoryRow("4", "sms", 1, now - 500, "+15551234567", "Your code is 482913", "in", "t1", listOf("+15551234567")),
            HistoryRow("5", "sms", 1, now - 1000, "+15551234567", "482913", "in", "t1", listOf("+15551234567")),
            HistoryRow("6", "sms", 1, now - ReadDesk.DAY_MS - 1, "+15551234567", "code 111111", "in", "t1", listOf("+15551234567")),
        )
        val items = desk.history(rows, "(555) 123-4567")
        assertNull(locks.held)
        assertTrue(locks.releases >= 1)
        assertTrue(items.any { it.direction == "out" })
        assertTrue(items.any { it.isGroup && it.threadId == "t2" && it.participantCount == 3 })
        assertTrue(items.none { "482913" in it.body })
        val code = desk.readCode(rows, "5551234567")
        assertEquals("482913", code.value)
        assertEquals("code", code.valueKind)
        log.note("code.read", mapOf("status" to code.status))
        assertFalse(log.lines.any { "482913" in it })
        val unsure = desk.readCode(listOf(rows[4]), "5551234567")
        assertEquals("not_identifiable", unsure.reason)
        assertNull(unsure.value)
        val stale = desk.readCode(listOf(rows[5]), "5551234567")
        assertEquals("not_identifiable", stale.reason)
        val counts = desk.diagnostic(mapOf("unacked" to 2, "provider_id" to 9, "suspected_restored" to 1))
        assertFalse(counts.containsKey("provider_id"))
        assertEquals(1, counts["suspected_restored"])
        try {
            locks.hold("zola:read") { error("boom") }
        } catch (_: IllegalStateException) {
        }
        assertNull(locks.held)
        locks.acquire("zola:event")
        locks.release()
        assertNull(locks.held)
    }

    @Test
    fun backoffDoesNotArmAPingAndIdleIsRecorded() {
        var now = 0L
        val backoff = Backoff { now }
        assertEquals(10_000L, backoff.scheduleReconnect())
        assertEquals(30_000L, backoff.scheduleReconnect())
        assertEquals(60_000L, backoff.scheduleReconnect())
        assertEquals(60_000L, backoff.scheduleReconnect())
        assertTrue(backoff.armed.all { it == "reconnect" })
        assertFalse(backoff.armed.any { "ping" in it })
        val log = ReconnectLog()
        log.reconnect(IdleSample(deepDoze = false, interactive = true, charging = true))
        log.reconnect(IdleSample(deepDoze = true, interactive = false, charging = false))
        assertEquals(2, log.samples.size)
        assertEquals("ask", AlarmPlan.decide(false))
        assertEquals("exact", AlarmPlan.decide(true))
        val debounce = Debounce()
        assertEquals(1000L, debounce.delay(0))
        assertEquals(0L, debounce.delay(5000))
    }

    @Test
    fun baselineFileIsOnceAndPeerOmitsTheCode() {
        val dir = File("build/phase4-state").apply { mkdirs() }
        dir.listFiles()?.forEach { it.delete() }
        val file = InstallFile(dir)
        assertTrue(file.writeOnce("device", 4, 5, 6))
        assertFalse(file.writeOnce("device", 1, 1, 1))
        assertEquals("device", file.stringField("device_id"))
        assertEquals(4L, file.longField("sms_cursor"))
        assertFalse(File(dir, "install.json.tmp").exists())
        val peer = PeerFile(dir)
        peer.write("device", "pc", "100.102.206.71", 0, 3)
        val text = peer.read()!!
        assertFalse(text.contains("12345678"))
        val acks = AckFile(dir)
        acks.add("pc", "sms:9")
        acks.add("pc", "sms:9")
        assertEquals(setOf("sms:9"), acks.load("pc"))
    }

    @Test
    fun pairingDropsTheCodeAndKeepsIdentity() {
        val session = PairingSession()
        session.begin("device", 4, "12345678")
        val open = session.phoneOpen(9, "pem")
        assertTrue(Intake.macMatches("12345678", open, Intake.mac("12345678", open)))
        assertFalse(session.acceptPcBind(mapOf("type" to "pc_bind"), false))
        assertTrue(session.acceptPcBind(mapOf("type" to "pc_bind", "pc_id" to "pc-1", "public_pem" to "key-a"), true))
        assertTrue(session.acceptPcOk(mapOf("type" to "pc_ok")))
        assertNull(session.code)
        assertTrue(session.paired)
        session.begin("device", session.seq, "87654321")
        assertTrue(session.acceptPcBind(mapOf("type" to "pc_bind", "pc_id" to "pc-1", "public_pem" to "key-b"), true))
        assertTrue(session.deliveryKept)
        assertEquals(0L, session.lastPcSeq)
        assertEquals("device", session.deviceId)
    }

    @Test
    fun captureRules() {
        assertFalse(CaptureRules.sendable(1, 0, ""))
        assertEquals("out", CaptureRules.smsDirection(2))
        assertEquals("in", CaptureRules.mmsDirection(1))
        assertEquals(1_700_000_000_000L, CaptureRules.receivedAtMs(1_700_000_000L))
        assertEquals("yes", CaptureRules.rcsFlag(listOf("application/vnd.gsma.rcs-ft")))
        assertEquals("unknown", CaptureRules.rcsFlag(listOf("application/vnd.wap.multipart.related")))
        assertEquals("audio", CaptureRules.attachmentKind("audio/amr"))
        assertTrue(CaptureRules.isGroup(3))
        assertEquals("ws://100.102.206.71:47821", CompanionService.linkUrl("100.102.206.71"))
    }

    private fun row(
        id: Long,
        revision: Int = 1,
        completeness: String = "complete",
        present: Boolean = true,
        body: String = "hello",
        creator: String = "com.google.android.apps.messaging",
        direction: String = "in",
        sendable: Boolean = true,
        dateMs: Long = 1_000_000_000_000L,
    ) = SeenRow("sms", id, revision, completeness, present, dateMs, creator, body, direction, sendable)

    private fun pcToPhone(protocol: JSONObject): Set<String> {
        val types = protocol.getJSONObject("message_types")
        return types.keys().asSequence().filter { types.getJSONObject(it).optString("direction") == "pc_to_phone" }.toSet()
    }

    private fun contractFile(name: String): File {
        var dir: File? = File("").absoluteFile
        repeat(8) {
            val here = dir ?: return@repeat
            val candidate = File(here, "hermes-plugins/zola_workspace/contracts/$name")
            if (candidate.isFile) return candidate
            dir = here.parentFile
        }
        error("missing $name")
    }
}
