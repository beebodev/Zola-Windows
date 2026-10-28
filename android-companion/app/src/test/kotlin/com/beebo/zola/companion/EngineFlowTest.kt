package com.beebo.zola.companion

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.security.KeyPairGenerator
import java.security.Signature
import java.security.spec.ECGenParameterSpec
import java.util.Base64
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean

// P10-COMPANION: the service path, not the pieces — Phase 5

class EngineFlowTest {
    @Test
    fun pairHelloPingEventAckRestartReconnectReadsAndReset() {
        val rig = Rig()
        rig.engine.boot()
        assertEquals(0, rig.provider.rowsRead)
        assertTrue(rig.provider.queries >= 2)

        rig.engine.handoff("100.102.206.71", "12345678")
        assertEquals(1, rig.link.opens)
        val open = rig.frames().last()
        assertEquals("pairing", open.getString("kind"))
        assertEquals("phone_open", open.getJSONObject("payload").getString("type"))

        rig.replyPairing("pc_bind", mapOf("pc_id" to "pc-live", "public_pem" to rig.pcPublic))
        rig.replyPairing("pc_ok", emptyMap())
        val signed = rig.signedFrames()
        assertEquals("hello", signed[0].getJSONObject("payload").getString("type"))
        assertTrue(rig.verify(signed[0]))
        assertEquals("device.health", signed[1].getJSONObject("payload").getString("type"))

        val beforePing = rig.link.sent.size
        rig.replySigned("keepalive.ping", emptyMap())
        val pong = rig.signedFrames().last()
        assertEquals("keepalive.pong", pong.getJSONObject("payload").getString("type"))
        assertTrue(rig.link.sent.size > beforePing)
        assertEquals(0, rig.backoffIndex())

        rig.provider.add(sms(11, "hello there"))
        rig.engine.onProviderChanged()
        val event = rig.signedFrames().last { it.getJSONObject("payload").getString("type") == "messages.event" }
        val payload = event.getJSONObject("payload")
        assertTrue(rig.verify(event))
        for (field in listOf(
            "received_at_ms", "date_sent_ms", "sender_raw", "is_group", "participant_count", "rcs_flag",
            "attachment_has", "attachment_count",
        )) {
            assertTrue(payload.has(field))
        }
        assertEquals(11, payload.getLong("received_at_ms"))
        assertFalse(payload.get("is_group") is Boolean)
        rig.replySigned("messages.ack", mapOf("provider_id" to "11", "kind" to "sms", "revision" to 1, "result" to "stored"))
        assertEquals(0, rig.wakes.held.count { it == "zola:event" })

        val seq = rig.engine.seq()
        val stored = rig.store.text
        val restarted = rig.restart()
        restarted.engine.boot()
        assertTrue(restarted.link.opens >= 1)
        val hello = restarted.signedFrames().first { it.getJSONObject("payload").getString("type") == "hello" }
        assertTrue(hello.getJSONObject("payload").getLong("seq") > seq - 1)
        assertTrue(restarted.signedFrames().none { it.getJSONObject("payload").optString("type") == "messages.event" })

        restarted.provider.add(sms(11, "hello there"))
        restarted.replySigned(
            "history.read.request",
            mapOf("request_id" to "h1", "selector" to "5551234567", "max_messages" to 10, "max_characters" to 1000, "deadline_ms" to restarted.clock.now),
        )
        val history = restarted.signedFrames().last { it.getJSONObject("payload").getString("type") == "history.read.result" }
        assertEquals(1, history.getJSONObject("payload").getJSONArray("items").length())

        restarted.provider.add(sms(12, "Your code is 482913", date = restarted.clock.now))
        restarted.engine.onProviderChanged()
        restarted.replySigned("messages.ack", mapOf("provider_id" to "12", "kind" to "sms", "revision" to 1, "result" to "stored"))
        restarted.replySigned("code.read.request", mapOf("request_id" to "c1", "provider_id" to "12", "kind" to "sms"))
        val code = restarted.signedFrames().last { it.getJSONObject("payload").getString("type") == "code.read.result" }
        assertEquals("482913", code.getJSONObject("payload").getString("value"))
        assertFalse(restarted.log.text().contains("482913"))

        restarted.provider.add(sms(13, "pending", date = restarted.clock.now))
        restarted.engine.onProviderChanged()
        restarted.provider.remove(13)
        restarted.engine.onProviderChanged()
        val deleted = restarted.signedFrames().last { it.getJSONObject("payload").getString("type") == "messages.deleted" }
        assertEquals("13", deleted.getJSONObject("payload").getString("provider_id"))
        assertEquals("deleted", deleted.getJSONObject("payload").getString("outcome"))
        assertFalse(deleted.getJSONObject("payload").has("body"))

        restarted.provider.maxSms = 1
        restarted.engine.onProviderChanged()
        assertTrue(restarted.engine.counts()["provider_reset"]!! >= 1)
        assertTrue(stored!!.isNotEmpty() || rig.store.text != null)
    }

    @Test
    fun signingUsesTheSamePayloadTheFrameCarries() {
        val rig = Rig()
        rig.engine.boot()
        rig.engine.handoff("100.102.206.71", "12345678")
        rig.replyPairing("pc_bind", mapOf("pc_id" to "pc-live", "public_pem" to rig.pcPublic))
        rig.replyPairing("pc_ok", emptyMap())
        rig.provider.add(sms(11, "plain"))
        rig.engine.onProviderChanged()
        val event = rig.signedFrames().last { it.getJSONObject("payload").getString("type") == "messages.event" }
        assertTrue(rig.verify(event))
    }

    @Test
    fun signingFailureSendsNothing() {
        val rig = Rig()
        rig.pair()
        val before = rig.link.sent.size
        rig.signer.fail = true
        rig.provider.add(sms(11, "plain"))
        rig.engine.onProviderChanged()
        assertEquals(before, rig.link.sent.size)
        assertTrue(rig.log.text().contains("sign"))
        rig.signer.fail = false
        rig.engine.onProviderChanged()
        assertTrue(rig.link.sent.size > before)
    }

    @Test
    fun newPcGetsSevenDaysAndRotationKeepsState() {
        val now = 1_700_000_000_000L
        val rig = Rig(now - 2 * DeliveryBook.WINDOW_MS)
        rig.provider.maxSms = 9
        rig.engine.boot()
        rig.clock.now = now
        rig.provider.add(sms(1, "old", date = now - DeliveryBook.WINDOW_MS - 1))
        rig.provider.add(sms(2, "edge", date = now - DeliveryBook.WINDOW_MS + 10_000))
        rig.provider.add(sms(3, "week", date = now - 6 * 86_400_000L))
        rig.pair()
        val ids = rig.signedFrames()
            .map { it.getJSONObject("payload") }
            .filter { it.optString("type") == "messages.event" }
            .map { it.getString("provider_id") }
            .toSet()
        assertEquals(setOf("2", "3"), ids)
        val acked = rig.engine.seq()
        rig.replySigned("messages.ack", mapOf("provider_id" to "2", "kind" to "sms", "revision" to 1, "result" to "stored"))
        val beforeRotate = rig.link.sent.size
        rig.engine.handoff("100.102.206.71", "12345678")
        rig.replyPairing("pc_bind", mapOf("pc_id" to "pc-live", "public_pem" to rig.pcPublic))
        rig.replyPairing("pc_ok", emptyMap())
        val duringRotate = rig.frames().drop(beforeRotate)
        assertTrue(duringRotate.none { it.getJSONObject("payload").optString("provider_id") == "2" && it.getJSONObject("payload").optString("type") == "messages.event" })
        val beforeOther = rig.link.sent.size
        rig.engine.handoff("100.102.206.71", "87654321")
        rig.replyPairing("pc_bind", mapOf("pc_id" to "pc-other", "public_pem" to rig.pcPublic), code = "87654321")
        rig.replyPairing("pc_ok", emptyMap(), code = "87654321")
        val other = rig.frames().drop(beforeOther).map { it.getJSONObject("payload") }.filter { it.optString("type") == "messages.event" }.map { it.getString("provider_id") }
        assertTrue(other.contains("2"))
        assertFalse(other.contains("1"))
    }

    @Test
    fun providerBatchIsBounded() {
        val rig = Rig()
        rig.pair()
        repeat(100) { rig.provider.add(sms(1000L + it, "m")) }
        rig.provider.rowsRead = 0
        rig.provider.queries = 0
        rig.engine.onProviderChanged()
        assertTrue(rig.provider.rowsRead <= 50)
        assertTrue(rig.provider.lastLimit <= 50)
        assertTrue(rig.provider.queries >= 1)
    }

    @Test
    fun incompleteExhaustsOnTimeOrAttempts() {
        val rig = Rig()
        rig.pair()
        rig.provider.add(sms(11, "wait", sender = ""))
        rig.engine.onProviderChanged()
        assertTrue(rig.signedFrames().none { it.getJSONObject("payload").optString("completeness") == "exhausted" })
        rig.clock.now += 600_000
        rig.engine.tick()
        val exhausted = rig.signedFrames().last { it.getJSONObject("payload").optString("provider_id") == "11" }
        assertEquals("exhausted", exhausted.getJSONObject("payload").getString("completeness"))
        rig.replySigned("messages.ack", mapOf("provider_id" to "11", "kind" to "sms", "revision" to 1, "result" to "stored"))
        rig.provider.replace(sms(11, "done", sender = "+15551234567"))
        rig.engine.onProviderChanged()
        val later = rig.signedFrames().last { it.getJSONObject("payload").optString("provider_id") == "11" }
        assertTrue(later.getJSONObject("payload").getInt("revision") > 1)
    }

    @Test
    fun logOmitsBodyAddressAndCode() {
        val rig = Rig()
        rig.pair()
        rig.provider.add(sms(11, "https://id.example/reset?token=aaaaaaaaaaaaaaaaaaaa", sender = "+15551234567"))
        rig.engine.onProviderChanged()
        val text = rig.log.text()
        assertFalse(text.contains("https://"))
        assertFalse(text.contains("15551234567"))
        assertFalse(text.contains("aaaaaaaaaaaaaaaaaaaa"))
        assertTrue(text.contains("zola.companion") || text.contains("detect"))
    }

    @Test
    fun reconnectWithoutACodeUsesTheStoredPeer() {
        val rig = Rig()
        rig.pair()
        rig.link.open = false
        rig.engine.onAlarm(IdleSample(false, false, true))
        assertTrue(rig.link.opens >= 2)
        assertEquals("hello", rig.signedFrames().last { it.getJSONObject("payload").getString("type") == "hello" }.getJSONObject("payload").getString("type"))
        rig.link.failNext = true
        rig.link.open = false
        rig.engine.onNetworkUp()
        assertTrue(rig.alarms.armed.isNotEmpty())
        assertTrue(rig.log.text().contains("failure") || rig.log.text().contains("network-lost"))
    }

    @Test
    fun refusedPcFrameIsLoggedAndNotActedOn() {
        val rig = Rig()
        rig.pair()
        val before = rig.link.sent.size
        rig.replySigned("keepalive.ping", emptyMap(), seq = 1)
        assertEquals(before, rig.link.sent.size)
        assertTrue(rig.log.text().contains("replay") || rig.log.text().contains("refused"))
    }

    @Test
    fun handoffKeepsTheCodeOutOfTheIntent() {
        val intent = Setup.pairIntent("100.102.206.71", "12345678")
        assertNull(intent.extras)
        assertEquals("12345678", Handoff.code)
        assertEquals(listOf("READ_SMS", "Alarms & reminders"), Setup.prompts(sms = false, notifications = true, exact = false))
    }

    @Test
    fun alarmsButtonOpensThePerAppExactAlarmPage() {
        val intent = Setup.exactAlarmIntent("com.beebo.zola.companion")
        assertEquals("android.settings.REQUEST_SCHEDULE_EXACT_ALARM", intent.action)
        assertEquals("package:com.beebo.zola.companion", intent.data)
    }

    @Test
    fun providerRowsCarryTheContractFields() {
        val rig = Rig()
        rig.pair()
        val rows = listOf(
            sms(21, "hello"),
            mms(22, "note"),
            mms(23, "", attachmentCount = 1, attachmentKind = "image", contentTypes = listOf("image/jpeg")),
            mms(24, "all", participants = listOf("+15551234567", "+15557654321", "+15550001111")),
            sms(25, "Your code is 482913"),
        )
        rows.forEach { row ->
            rig.provider.add(row)
            rig.engine.onProviderChanged()
            val payload = rig.signedFrames().last { it.getJSONObject("payload").optString("provider_id") == row.providerId.toString() }
                .getJSONObject("payload")
            for (field in listOf(
                "received_at_ms", "date_sent_ms", "sender_raw", "is_group", "participant_count", "rcs_flag",
                "attachment_has", "attachment_count", "truncated", "completeness", "revision",
            )) {
                assertTrue(payload.has(field))
            }
            assertFalse(payload.get("is_group") is Boolean)
            assertFalse(payload.get("truncated") is Boolean)
            assertFalse(payload.get("attachment_has") is Boolean)
            rig.replySigned(
                "messages.ack",
                mapOf("provider_id" to row.providerId.toString(), "kind" to row.kind, "revision" to 1, "result" to "stored"),
            )
        }
        val masked = rig.signedFrames().last { it.getJSONObject("payload").optString("provider_id") == "25" }.getJSONObject("payload")
        assertEquals("verification_code", masked.getString("mask_kind"))
        assertEquals("", masked.getString("body"))
        val group = rig.signedFrames().last { it.getJSONObject("payload").optString("provider_id") == "24" }.getJSONObject("payload")
        assertEquals(1, group.getInt("is_group"))
        assertEquals(3, group.getInt("participant_count"))
    }

    @Test
    fun stateFileOmitsBodiesAndStaysBounded() {
        val rig = Rig()
        rig.pair()
        rig.provider.add(sms(11, "SENTINEL-BODY", sender = "+15550009999"))
        rig.engine.onProviderChanged()
        val stored = rig.store.text.orEmpty()
        assertFalse(stored.contains("SENTINEL-BODY"))
        assertFalse(stored.contains("15550009999"))
        repeat(500) { index ->
            rig.provider.add(sms(1000L + index, "BODY-$index", sender = "+15550001111"))
            rig.engine.onProviderChanged()
            ackNewEvents(rig)
        }
        val after = rig.store.text.orEmpty()
        assertFalse(after.contains("BODY-"))
        assertFalse(after.contains("15550001111"))
        assertTrue(after.length < 40_000)
    }

    @Test
    fun interruptedSaveKeepsInstallIdentity() {
        val dir = File("build/crash-${System.nanoTime()}").apply { mkdirs() }
        val state = File(dir, "companion-state.json")
        val install = File(dir, "install.json")
        val store = FileStore(state)
        val first = standalone(store)
        first.boot()
        val id = first.deviceId()
        val installJson = JSONObject(install.readText())
        assertEquals(id, installJson.getString("device_id"))
        val baseline = installJson.getLong("baseline_ms")
        File(dir, "companion-state.json.tmp").writeText("{")
        standalone(store).boot()
        assertEquals(id, JSONObject(state.readText()).getString("device_id"))
        assertEquals(baseline, JSONObject(state.readText()).getLong("baseline_ms"))
        state.delete()
        File(dir, "companion-state.json.tmp").writeText("{")
        val second = standalone(store)
        second.boot()
        assertEquals(id, second.deviceId())
        assertEquals(baseline, JSONObject(state.readText()).getLong("baseline_ms"))
        assertEquals(id, JSONObject(install.readText()).getString("device_id"))
    }

    @Test
    fun secondPcPairsWhenItsSeqStartsAtOne() {
        val rig = Rig()
        rig.pair()
        val saved = JSONObject(rig.store.text!!)
        saved.put("last_pc_seq", 500)
        rig.store.text = saved.toString()
        val next = rig.restart()
        next.engine.boot()
        next.link.open = false
        next.pcSeq = 0
        next.engine.handoff("100.102.206.71", "87654321")
        next.replyPairing("pc_bind", mapOf("pc_id" to "pc-other", "public_pem" to next.pcPublic), code = "87654321")
        val types = next.frames().map { it.getJSONObject("payload").optString("type") }
        assertTrue(types.contains("phone_bind"))
    }

    @Test
    fun newPcReceivesOnlyTheSixtyInTheWindow() {
        val now = 1_700_000_000_000L
        val rig = Rig(now - 2 * DeliveryBook.WINDOW_MS)
        rig.provider.maxSms = 0
        rig.engine.boot()
        rig.clock.now = now
        rig.provider.maxSms = 80
        repeat(20) { index ->
            rig.provider.add(sms(index + 1L, "old", date = now - DeliveryBook.WINDOW_MS - 86_400_000L))
        }
        repeat(60) { index ->
            rig.provider.add(sms(21L + index, "win", date = now - 3_600_000L))
        }
        rig.pair()
        val ids = ackNewEvents(rig, rounds = 80)
        assertEquals(60, ids.size)
        assertTrue(ids.all { it.toLong() >= 21L })
    }

    @Test
    fun historyReturnsNewestWithContractFields() {
        val rig = Rig()
        rig.pair()
        rig.provider.add(sms(1, "old", date = 1, sender = "15551234567"))
        rig.provider.add(sms(2, "mid", date = 2, sender = "15551234567"))
        rig.provider.add(sms(3, "new", date = 3, sender = "15551234567"))
        rig.replySigned(
            "history.read.request",
            mapOf("request_id" to "h-new", "selector" to "+1 (555) 123-4567", "max_messages" to 1, "max_characters" to 1000, "deadline_ms" to rig.clock.now),
        )
        val items = rig.signedFrames().last { it.getJSONObject("payload").optString("type") == "history.read.result" }
            .getJSONObject("payload").getJSONArray("items")
        assertEquals(1, items.length())
        assertEquals("3", items.getJSONObject(0).getString("provider_id"))
        assertTrue(items.getJSONObject(0).has("received_at_ms"))
        assertTrue(items.getJSONObject(0).has("revision"))
        assertTrue(AddressNeedles.of("+15551234567").contains("15551234567"))
        val text = rig.log.text()
        val held = text.indexOf("wake tag=zola:read result=held")
        val released = text.indexOf("wake tag=zola:read result=released")
        assertTrue(held >= 0)
        assertTrue(released > held)
    }

    @Test
    fun historyStaysInsideTheFrameBudget() {
        val rig = Rig()
        rig.pair()
        repeat(8) { index ->
            rig.provider.add(sms(50L + index, "Z".repeat(20000), date = index.toLong(), sender = "+15551234567"))
        }
        rig.replySigned(
            "history.read.request",
            mapOf("request_id" to "h-cap", "selector" to "5551234567", "max_messages" to 50, "max_characters" to 30000, "deadline_ms" to rig.clock.now),
        )
        val payload = rig.signedFrames().last { it.getJSONObject("payload").optString("type") == "history.read.result" }
            .getJSONObject("payload")
        assertTrue(payload.getJSONArray("items").length() < 8)
        assertTrue(payload.optInt("capped") == 1 || payload.optInt("truncated") == 1)
    }

    @Test
    fun sixTextsDrainWhenAcksFreeTheWindow() {
        val rig = Rig()
        rig.pair()
        repeat(6) { rig.provider.add(sms(100L + it, "m$it")) }
        rig.engine.onProviderChanged()
        val ids = ackNewEvents(rig, rounds = 8)
        assertEquals(setOf("100", "101", "102", "103", "104", "105"), ids)
    }

    @Test
    fun serviceStartScansAboveTheCursor() {
        val rig = Rig()
        rig.pair()
        val next = rig.restart()
        next.provider.add(sms(11, "while-down"))
        next.link.deferOpen = true
        next.engine.boot()
        assertEquals(QueryPlan.BATCH, next.provider.lastLimit)
        val ids = next.signedFrames()
            .map { it.getJSONObject("payload") }
            .filter { it.optString("type") == "messages.event" }
            .map { it.getString("provider_id") }
        assertEquals(listOf("11"), ids)
    }

    @Test
    fun verifiedConnectScansAboveTheCursor() {
        val rig = Rig()
        rig.pair()
        rig.link.close("peer-closed")
        rig.provider.add(sms(11, "while-down"))
        val before = rig.link.sent.size
        rig.engine.onAlarm(IdleSample(deepDoze = false, interactive = true, charging = false, lightDoze = false))
        val ids = rig.frames().drop(before)
            .map { it.getJSONObject("payload") }
            .filter { it.optString("type") == "messages.event" }
            .map { it.getString("provider_id") }
        assertEquals(listOf("11"), ids)
        assertEquals(QueryPlan.BATCH, rig.provider.lastLimit)
    }

    @Test
    fun serviceStartBeforeAcksStillDeliversTheWindow() {
        val now = 1_700_000_000_000L
        val rig = Rig(now - 2 * DeliveryBook.WINDOW_MS)
        rig.provider.maxSms = 0
        rig.engine.boot()
        rig.clock.now = now
        rig.provider.maxSms = 8
        repeat(8) { index ->
            rig.provider.add(sms(index + 1L, "win", date = now - 3_600_000L))
        }
        rig.pair()
        rig.engine.boot()
        val ids = ackNewEvents(rig, rounds = 12)
        assertEquals((1..8).map { it.toString() }.toSet(), ids)
    }

    @Test
    fun coldStartSendsWaitingSlotsThatHaveNoPayload() {
        val rig = Rig()
        rig.pair()
        repeat(4) { rig.provider.add(sms(30L + it, "queued")) }
        rig.engine.onProviderChanged()
        val saved = JSONObject(rig.store.text!!)
        val pcs = saved.getJSONObject("pcs")
        val names = pcs.keys()
        while (names.hasNext()) {
            val slots = pcs.getJSONObject(names.next()).getJSONArray("slots")
            for (index in 0 until slots.length()) slots.getJSONObject(index).put("in_flight", false)
        }
        val next = rig.restart()
        next.store.text = saved.toString()
        next.provider.remove(30L)
        next.engine.boot()
        val sent = next.signedFrames().map { it.getJSONObject("payload") }
        val events = sent.filter { it.optString("type") == "messages.event" }.map { it.getString("provider_id") }.toSet()
        val deleted = sent.filter { it.optString("type") == "messages.deleted" }.map { it.getString("provider_id") }.toSet()
        assertEquals(setOf("31", "32", "33"), events)
        assertEquals(setOf("30"), deleted)
    }

    @Test
    fun pingSendsWaitingSlotsWhenNoAckIsPending() {
        val rig = Rig()
        rig.pair()
        rig.signer.fail = true
        repeat(3) { rig.provider.add(sms(40L + it, "held")) }
        rig.engine.onProviderChanged()
        assertTrue(rig.signedFrames().none { it.getJSONObject("payload").optString("type") == "messages.event" })
        rig.signer.fail = false
        rig.replySigned("keepalive.ping", emptyMap())
        val ids = rig.signedFrames()
            .map { it.getJSONObject("payload") }
            .filter { it.optString("type") == "messages.event" }
            .map { it.getString("provider_id") }
            .toSet()
        assertEquals(setOf("40", "41", "42"), ids)
    }

    @Test
    fun asynchronousAcksInterleaveWithAlarmsAndAProviderChange() {
        val rig = Rig()
        rig.pair()
        val worker = Executors.newSingleThreadExecutor()
        val finished = AtomicBoolean(false)
        val expected = (1..12).map { (300L + it).toString() }.toSet()
        val acker = Thread {
            var delivered = emptySet<String>()
            var attempts = 0
            while (attempts < 40 && (!finished.get() || delivered.size < expected.size)) {
                delivered = worker.submit<Set<String>> {
                    rig.engine.onAlarm(IdleSample(false, true, false))
                    ackNewEvents(rig, rounds = 1)
                    rig.signedFrames()
                        .map { it.getJSONObject("payload") }
                        .filter { it.optString("type") == "messages.event" }
                        .map { it.getString("provider_id") }
                        .toSet()
                }.get()
                attempts += 1
            }
        }
        worker.submit {
            repeat(8) { rig.provider.add(sms(301L + it, "a$it")) }
            rig.engine.onProviderChanged()
            rig.engine.boot()
        }.get()
        acker.start()
        worker.submit {
            repeat(4) { rig.provider.add(sms(309L + it, "b$it")) }
            rig.engine.onProviderChanged()
            rig.engine.onAlarm(IdleSample(false, false, true))
        }.get()
        finished.set(true)
        acker.join(10_000)
        worker.shutdown()
        assertTrue(worker.awaitTermination(5, TimeUnit.SECONDS))
        val ids = rig.signedFrames()
            .map { it.getJSONObject("payload") }
            .filter { it.optString("type") == "messages.event" }
            .map { it.getString("provider_id") }
            .toSet()
        assertEquals(expected, ids)
    }

    @Test
    fun connectingIgnoresASecondOpen() {
        val rig = Rig()
        rig.pair()
        rig.link.open = false
        rig.link.deferOpen = true
        val before = rig.link.opens
        rig.engine.onAlarm(IdleSample(false, false, true))
        rig.engine.onNetworkUp()
        assertEquals(before + 1, rig.link.opens)
    }

    @Test
    fun blankFieldsDoNotHandOff() {
        assertFalse(Setup.canHandOff("100.102.206.71:47822", ""))
        assertFalse(Setup.canHandOff(" ", "12345678"))
        assertTrue(Setup.canHandOff(" 100.102.206.71:47822 ", "12345678"))
    }

    @Test
    fun alreadyPairedScreenKeepsDigitsUntilPairIsTapped() {
        assertFalse(Setup.clearTypedCode(handedOff = false, paired = true, hasText = true))
        assertTrue(Setup.clearTypedCode(handedOff = true, paired = true, hasText = true))
        assertFalse(Setup.clearTypedCode(handedOff = true, paired = false, hasText = true))
        assertFalse(Setup.clearTypedCode(handedOff = false, paired = false, hasText = true))
    }

    @Test
    fun typedCodeWhileConnectedStartsANewPairing() {
        val rig = Rig()
        rig.pair()
        assertEquals("connected", CompanionStatus.state)
        val opens = rig.link.opens
        val sent = rig.link.sent.size
        rig.engine.handoff("100.102.206.71:47822", "87654321")
        assertTrue(rig.link.opens > opens)
        val fresh = rig.link.sent.drop(sent).map { String(it, Charsets.UTF_8) }
        assertTrue(fresh.any { it.contains("phone_open") })
        assertFalse(fresh.any { it.contains("\"hello\"") })
        assertEquals("pairing", CompanionStatus.state)
        rig.clock.now += 30_000
        rig.engine.tick()
        assertEquals("pairing-failed", CompanionStatus.state)
        val afterFail = rig.link.opens
        rig.engine.onAlarm(IdleSample(false, false, false))
        assertEquals(afterFail, rig.link.opens)
        assertEquals("pairing-failed", CompanionStatus.state)
    }

    @Test
    fun freshCodeReopensALiveUnpairedSocket() {
        val rig = Rig()
        rig.engine.boot()
        rig.engine.handoff("100.102.206.71", "11111111")
        val before = rig.link.sent.count { String(it, Charsets.UTF_8).contains("phone_open") }
        rig.engine.handoff("100.102.206.71:47822", "22222222")
        val after = rig.link.sent.count { String(it, Charsets.UTF_8).contains("phone_open") }
        assertEquals(2, rig.link.opens)
        assertEquals(before + 1, after)
        assertEquals("pairing", CompanionStatus.state)
    }

    @Test
    fun freshCodeConnectsWhileThePreviousAttemptIsStillConnecting() {
        val rig = Rig()
        rig.engine.boot()
        rig.link.deferOpen = true
        rig.engine.handoff("100.102.206.71", "11111111")
        rig.engine.handoff("100.102.206.71:47822", "22222222")
        assertEquals(2, rig.link.opens)
    }

    @Test
    fun closedSocketLogsASectionNineReasonAndWho() {
        val rig = Rig()
        rig.engine.boot()
        rig.engine.handoff("100.102.206.71", "12345678")
        rig.link.close("peer-closed")
        assertTrue(rig.log.text().contains("disconnect reason=peer-closed who=phone"))
    }

    @Test
    fun pairingTimeoutClosesAndLogsTheDisconnect() {
        val rig = Rig()
        rig.engine.boot()
        rig.engine.handoff("100.102.206.71", "12345678")
        rig.clock.now += 30_000
        rig.engine.tick()
        assertFalse(rig.link.isOpen())
        val text = rig.log.text()
        assertTrue(text.contains("pairing result=failed reason=timeout"))
        assertTrue(text.contains("disconnect reason=failure who=phone"))
    }

    @Test
    fun pairingFrameLogsItsTypeAndAnIgnoredFrameSaysWhy() {
        val rig = Rig()
        rig.engine.boot()
        rig.engine.handoff("100.102.206.71", "12345678")
        rig.replyPairing("pc_later", emptyMap())
        rig.replyPairing("pc_bind", emptyMap())
        val text = rig.log.text()
        assertTrue(text.contains("pairing type=pc_later result=received"))
        assertTrue(text.contains("pairing type=pc_later result=ignored reason=unexpected"))
        assertTrue(text.contains("pairing type=pc_bind result=ignored reason=missing"))
        assertFalse(text.contains("12345678"))
        assertEquals("pairing", CompanionStatus.state)
    }

    @Test
    fun diagnosticCountsRejectionAndLag() {
        val rig = Rig()
        rig.pair()
        rig.provider.maxSms = 40
        rig.provider.add(sms(11, "x"))
        rig.engine.onProviderChanged()
        rig.replySigned("messages.ack", mapOf("provider_id" to "11", "kind" to "sms", "revision" to 1, "result" to "rejected"))
        rig.replySigned("diagnostic_read", mapOf("request_id" to "d1", "deadline_ms" to rig.clock.now))
        val payload = rig.signedFrames().last { it.getJSONObject("payload").optString("type") == "diagnostic_read.result" }
            .getJSONObject("payload")
        assertTrue(payload.getInt("rejected") >= 1)
        assertTrue(payload.getInt("cursor_lag") > 0)
        assertTrue(payload.has("rows_since_baseline"))
        assertTrue(payload.getInt("rows_since_baseline") >= 1)
    }

    @Test
    fun logHashesProviderIdsAndKeepsRequestIds() {
        val rig = Rig()
        rig.pair()
        rig.provider.add(sms(424242, "plain"))
        rig.engine.onProviderChanged()
        val text = rig.log.text()
        assertFalse(text.contains("424242"))
        val hashes = Regex("id=([0-9a-f]{16})").findAll(text).map { it.groupValues[1] }.toSet()
        assertEquals(1, hashes.size)
        rig.replySigned(
            "history.read.request",
            mapOf("request_id" to "req-keep-77", "selector" to "5551234567", "max_messages" to 1, "max_characters" to 100, "deadline_ms" to rig.clock.now),
        )
        assertTrue(rig.log.text().contains("req-keep-77"))
    }

    @Test
    fun wrongPairingCodeClearsAndDoesNotRetry() {
        val rig = Rig()
        rig.engine.boot()
        rig.engine.handoff("100.102.206.71", "12345678")
        rig.replyPairing("pc_bind", mapOf("pc_id" to "pc-live", "public_pem" to rig.pcPublic), code = "00000000")
        assertEquals("pairing-failed", CompanionStatus.state)
        assertTrue(rig.log.text().contains("failed"))
        val before = rig.link.sent.size
        rig.link.open = false
        rig.engine.onAlarm(IdleSample(false, false, true))
        assertEquals(before, rig.link.sent.size)
    }

    @Test
    fun logLinesCarryMillisAndTheFirstSightIsOnce() {
        val dir = File("build/log-millis-${System.nanoTime()}").apply { mkdirs() }
        val stamped = PhoneLogFile(dir) { 1_700_000_000_123L }
        stamped.note("scan", emptyMap())
        assertEquals("1700000000123 zola.companion scan", stamped.text().trim())

        val rig = Rig()
        rig.pair()
        rig.provider.add(sms(81, "plain"))
        rig.engine.onProviderChanged()
        val first = rig.log.text().lines().filter { it.isNotBlank() }
        assertTrue(first.all { Regex("""\d{13} zola\.companion .*""").matches(it) })
        assertEquals(1, first.count { " zola.companion scan" in it })
        assertFalse(first.first { " zola.companion scan" in it }.contains("id="))
        val seen = first.filter { " zola.companion seen " in it }
        assertEquals(1, seen.size)
        assertTrue(seen[0].contains("completeness=complete"))
        rig.engine.onProviderChanged()
        assertEquals(1, rig.log.text().lines().count { " zola.companion seen " in it })

        rig.provider.add(mms(82, ""))
        rig.engine.onProviderChanged()
        val incomplete = rig.log.text().lines().filter { " zola.companion seen " in it && "completeness=incomplete" in it }
        assertEquals(1, incomplete.size)
        rig.provider.replace(mms(82, "now complete"))
        rig.engine.onProviderChanged()
        assertEquals(2, rig.log.text().lines().count { " zola.companion seen " in it })
    }

    @Test
    fun aPingRecordsDeepLightScreenAndCharging() {
        val rig = Rig()
        rig.idleSample = IdleSample(deepDoze = true, interactive = false, charging = false, lightDoze = true)
        rig.pair()
        rig.replySigned("keepalive.ping", emptyMap())
        val lines = rig.log.text().lines().filter { " zola.companion idle " in it }
        assertEquals(1, lines.size)
        assertTrue(lines[0].contains("deep=true"))
        assertTrue(lines[0].contains("light=true"))
        assertTrue(lines[0].contains("interactive=false"))
        assertTrue(lines[0].contains("charging=false"))
        rig.replySigned("keepalive.ping", emptyMap())
        assertEquals(2, rig.log.text().lines().count { " zola.companion idle " in it })
    }

    private fun ackNewEvents(rig: Rig, rounds: Int = 8): Set<String> {
        val seen = linkedSetOf<String>()
        repeat(rounds) {
            val fresh = rig.signedFrames()
                .map { it.getJSONObject("payload") }
                .filter { it.optString("type") == "messages.event" && it.optString("provider_id") !in seen }
            if (fresh.isEmpty()) return seen
            fresh.forEach { payload ->
                val id = payload.getString("provider_id")
                seen.add(id)
                rig.replySigned(
                    "messages.ack",
                    mapOf(
                        "provider_id" to id,
                        "kind" to payload.optString("kind", "sms"),
                        "revision" to payload.optInt("revision", 1),
                        "result" to "stored",
                    ),
                )
            }
        }
        return seen
    }

    private fun standalone(store: EngineStore): CompanionEngine {
        val link = FakeLink()
        val log = PhoneLogFile(File("build/engine-log-${System.nanoTime()}").apply { mkdirs() })
        val provider = FakeProvider()
        return CompanionEngine(
            { 1_700_000_000_000L },
            provider,
            link,
            FakeAlarms(),
            FakeWakes(),
            TestSigner(),
            store,
            log,
            FrameWriter { },
        ) { true }
    }

    private fun sms(id: Long, body: String, date: Long = id, sender: String = "+15551234567") = TextRecord(
        kind = "sms",
        providerId = id,
        dateMs = date,
        dateSentMs = date,
        senderRaw = sender,
        body = body,
        direction = "in",
        threadId = "t",
        participants = listOf(sender),
        creator = "com.google.android.apps.messaging",
        sendable = true,
        present = true,
        containsOtp = false,
        contentTypes = emptyList(),
        attachmentCount = 0,
        attachmentKind = null,
        partsMissing = false,
    )

    private fun mms(
        id: Long,
        body: String,
        sender: String = "+15551234567",
        participants: List<String> = listOf(sender),
        attachmentCount: Int = 0,
        attachmentKind: String? = null,
        contentTypes: List<String> = emptyList(),
    ) = TextRecord(
        kind = "mms",
        providerId = id,
        dateMs = id,
        dateSentMs = id,
        senderRaw = sender,
        body = body,
        direction = "in",
        threadId = "t",
        participants = participants,
        creator = "com.google.android.apps.messaging",
        sendable = true,
        present = true,
        containsOtp = false,
        contentTypes = contentTypes,
        attachmentCount = attachmentCount,
        attachmentKind = attachmentKind,
        partsMissing = false,
    )
}

private class Rig(start: Long = 1_700_000_000_000L) {
    val clock = MovingClock(start)
    val provider = FakeProvider()
    val link = FakeLink()
    val alarms = FakeAlarms()
    val wakes = FakeWakes()
    val signer = TestSigner()
    val store = MemoryStore()
    val log = PhoneLogFile(File("build/engine-log-${System.nanoTime()}").apply { mkdirs() })
    var idleSample = IdleSample(deepDoze = false, interactive = false, charging = false, lightDoze = false)
    val writer = FrameWriter { frame -> link.sent.add(frame) }
    var pc = KeyPairGenerator.getInstance("EC").apply { initialize(ECGenParameterSpec("secp256r1")) }.generateKeyPair()
    var pcPublic: String = ""
    var pcSeq = 0L
    val engine: CompanionEngine

    init {
        pcPublic = pem(pc.public.encoded)
        engine = CompanionEngine(
            { clock.now() },
            provider,
            link,
            alarms,
            wakes,
            signer,
            store,
            log,
            writer,
            canExactAlarm = { true },
            idle = { idleSample },
        )
    }

    fun pair() {
        engine.boot()
        engine.handoff("100.102.206.71", "12345678")
        replyPairing("pc_bind", mapOf("pc_id" to "pc-live", "public_pem" to pcPublic))
        replyPairing("pc_ok", emptyMap())
    }

    fun restart(): Rig {
        val next = Rig(clock.now)
        next.store.text = store.text
        next.provider.rows.addAll(provider.rows)
        next.provider.maxSms = provider.maxSms
        next.provider.maxMms = provider.maxMms
        next.pc = pc
        next.pcPublic = pcPublic
        next.pcSeq = pcSeq
        next.signer.pair = signer.pair
        return next
    }

    fun frames() = link.sent.map { JSONObject(it.toString(Charsets.UTF_8).trim()) }

    fun signedFrames() = frames().filter { it.getString("kind") == "signed" }

    fun verify(frame: JSONObject): Boolean {
        val payload = toMap(frame.getJSONObject("payload"))
        return Intake.verifySignature(signer.publicPem(), payload, frame.getString("signature"))
    }

    fun replyPairing(type: String, extra: Map<String, Any?>, code: String = "12345678") {
        pcSeq += 1
        val payload = linkedMapOf<String, Any?>(
            "type" to type,
            "device_id" to engine.deviceId(),
            "seq" to pcSeq,
            "sent_at_ms" to clock.now,
            "contract_version" to 3,
        )
        extra.forEach { payload[it.key] = it.value }
        val mac = Intake.mac(code, payload)
        link.listener.onMessage(frame("pairing", payload, mac))
    }

    fun replySigned(type: String, extra: Map<String, Any?>, seq: Long? = null) {
        if (seq == null) pcSeq += 1
        val payload = linkedMapOf<String, Any?>(
            "type" to type,
            "device_id" to engine.deviceId(),
            "seq" to (seq ?: pcSeq),
            "sent_at_ms" to clock.now,
            "contract_version" to 3,
        )
        extra.forEach { payload[it.key] = it.value }
        val signature = sign(pc.private, payload)
        link.listener.onMessage(frame("signed", payload, signature))
    }

    fun backoffIndex(): Int = alarms.armed.size

    private fun frame(kind: String, payload: Map<String, Any?>, signature: String): String {
        return Frames.build(payload, kind, signature)!!.toString(Charsets.UTF_8).trim()
    }

    private fun sign(key: java.security.PrivateKey, payload: Map<String, Any?>): String {
        val signature = Signature.getInstance("SHA256withECDSA")
        signature.initSign(key)
        signature.update(Canonical.bytes(payload))
        return Base64.getEncoder().encodeToString(signature.sign())
    }

    private fun pem(encoded: ByteArray): String {
        val body = Base64.getMimeEncoder(64, byteArrayOf('\n'.code.toByte())).encodeToString(encoded)
        return "-----BEGIN PUBLIC KEY-----\n$body\n-----END PUBLIC KEY-----\n"
    }
}

private class MovingClock(var now: Long) {
    fun now(): Long {
        now += 1
        return now
    }
}

private class FakeProvider : TextProvider {
    val rows = mutableListOf<TextRecord>()
    var maxSms = 10L
    var maxMms = 10L
    override var queries = 0
    override var rowsRead = 0
    var lastLimit = 0

    fun add(row: TextRecord) {
        rows.add(row)
    }

    fun replace(row: TextRecord) {
        rows.removeAll { it.kind == row.kind && it.providerId == row.providerId }
        rows.add(row)
    }

    fun remove(id: Long) {
        val index = rows.indexOfFirst { it.providerId == id }
        if (index >= 0) rows[index] = rows[index].copy(present = false)
    }

    override fun maxId(kind: String): Long {
        queries += 1
        return if (kind == "sms") maxSms else maxMms
    }

    override fun batch(kind: String, above: Long, also: Set<Long>, limit: Int): List<TextRecord> {
        queries += 1
        lastLimit = limit
        val found = rows.filter { it.kind == kind && (it.providerId > above || it.providerId in also) }.take(limit)
        rowsRead += found.size
        return found
    }

    override fun recent(kind: String, floorMs: Long, limit: Int, afterId: Long): List<TextRecord> {
        queries += 1
        lastLimit = limit
        val found = rows.filter { it.kind == kind && it.dateMs >= floorMs && it.present && it.providerId > afterId }
            .sortedBy { it.providerId }
            .take(limit)
        rowsRead += found.size
        return found
    }

    override fun history(selector: String, limit: Int): List<TextRecord> {
        queries += 1
        val found = rows.filter { row ->
            row.present && (DigitKey.same(selector, row.senderRaw) || row.participants.any { DigitKey.same(selector, it) } || row.threadId == selector)
        }.take(limit)
        rowsRead += found.size
        return found
    }

    override fun one(kind: String, id: Long): TextRecord? {
        queries += 1
        val found = rows.firstOrNull { it.kind == kind && it.providerId == id && it.present }
        if (found != null) rowsRead += 1
        return found
    }
}

private class FakeLink : LinkPort {
    override var listener: LinkListener = object : LinkListener {
        override fun onOpen() {}
        override fun onMessage(text: String) {}
        override fun onClosing() {}
        override fun onClosed(reason: String) {}
        override fun onFailure(reason: String) {}
    }
    var opens = 0
    var open = false
    var failNext = false
    var deferOpen = false
    val sent = mutableListOf<ByteArray>()
    override fun connect(url: String) {
        opens += 1
        if (failNext) {
            failNext = false
            listener.onFailure("failure")
            return
        }
        if (deferOpen) return
        open = true
        listener.onOpen()
    }

    override fun close(reason: String) {
        open = false
        listener.onClosed(reason)
    }

    override fun isOpen(): Boolean = open
}

private class FakeAlarms : AlarmPort {
    val armed = mutableListOf<Long>()
    var asked = false
    override fun schedule(atMs: Long) {
        armed.add(atMs)
    }

    override fun askGrant() {
        asked = true
    }
}

private class FakeWakes : WakePort {
    val held = mutableListOf<String>()
    override fun acquire(tag: String, timeoutMs: Long) {
        held.add(tag)
    }

    override fun release(tag: String) {
        held.remove(tag)
    }
}

private class TestSigner : SignerPort {
    var pair = KeyPairGenerator.getInstance("EC").apply { initialize(ECGenParameterSpec("secp256r1")) }.generateKeyPair()
    var fail = false
    override fun sign(payload: Map<String, Any?>): String? {
        if (fail) return null
        val signature = Signature.getInstance("SHA256withECDSA")
        signature.initSign(pair.private)
        signature.update(Canonical.bytes(payload))
        return Base64.getEncoder().encodeToString(signature.sign())
    }

    override fun publicPem(): String {
        val body = Base64.getMimeEncoder(64, byteArrayOf('\n'.code.toByte())).encodeToString(pair.public.encoded)
        return "-----BEGIN PUBLIC KEY-----\n$body\n-----END PUBLIC KEY-----\n"
    }
}

private class MemoryStore : EngineStore {
    var text: String? = null
    override fun load(): String? = text
    override fun save(body: String) {
        text = body
    }
}
