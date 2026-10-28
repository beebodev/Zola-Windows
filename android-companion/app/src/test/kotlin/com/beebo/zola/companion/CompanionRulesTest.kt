package com.beebo.zola.companion

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors

class CompanionRulesTest {
    @Test
    fun pairingMacMatchesTheSharedVector() {
        val payload = linkedMapOf<String, Any?>(
            "type" to "phone_open",
            "device_id" to "zp10-device-test",
            "seq" to 1,
            "sent_at_ms" to 1700000000000L,
            "contract_version" to 3,
        )
        assertEquals(
            "DAikJf15pD8/g4gmfzops6dySUhzWnJ3u2rSmv4rSyU=",
            Intake.mac("00000000", payload),
        )
        val withKey = linkedMapOf<String, Any?>()
        withKey.putAll(payload)
        withKey["public_pem"] = "-----BEGIN PUBLIC KEY-----\n" + "A".repeat(64) + "\n" + "B".repeat(10) + "\n-----END PUBLIC KEY-----\n"
        assertEquals(
            "kGrHmFQzmeEYkH3h3lO94HW5CyM5ow5ECreBBC6g0Bg=",
            Intake.mac("00000000", withKey),
        )
    }

    @Test
    fun maskSamples() {
        masked.forEachIndexed { index, text ->
            assertFalse("M$index stayed plain: $text", Mask.kind(text) == "none")
        }
        ordinary.forEachIndexed { index, text ->
            assertEquals("O$index", "none", Mask.kind(text))
        }
        assertEquals("verification_code", Mask.kind("The gate code is 1948"))
        assertEquals("verification_code", Mask.kind("Building PIN 1948"))
        assertEquals("verification_code", Mask.kind("Your order code is AB12CD"))
        assertEquals("verification_code", Mask.kind("Reference 482913 is the invoice", containsOtp = true))
        assertEquals("reset_link", Mask.kind("verify your device at https://files.example/a"))
        assertEquals("none", Mask.kind("See you at 48 29 13"))
    }

    @Test
    fun maskBeforeTruncate() {
        val body = "x".repeat(16001) + " code 482913"
        val prepared = Mask.prepare(body)
        assertEquals("verification_code", prepared.maskKind)
        assertEquals("", prepared.body)
        val plain = "y".repeat(16001)
        val cut = Mask.prepare(plain)
        assertTrue(cut.truncated)
        assertEquals(16000, cut.body.length)
    }

    @Test
    fun canonicalBytesMatchPython() {
        val root = vectors()
        val canonical = root.getJSONArray("canonical")
        val byName = (0 until canonical.length()).associate { index ->
            val item = canonical.getJSONObject(index)
            item.getString("name") to item.getString("utf8")
        }
        assertEquals(byName.getValue("nested"), Canonical.json(mapOf("b" to 1, "a" to mapOf("d" to 2, "c" to 3))))
        assertEquals(byName.getValue("escapes"), Canonical.json(mapOf("text" to "say \"hi\" \\ end \u001f")))
        assertEquals(byName.getValue("non_ascii"), Canonical.json(mapOf("text" to "café")))
        assertEquals(byName.getValue("emoji"), Canonical.json(mapOf("text" to "😀")))
        assertEquals(byName.getValue("large_int"), Canonical.json(mapOf("n" to 9007199254740993L)))
        assertEquals(byName.getValue("surrogate"), Canonical.json(mapOf("text" to "\uD800")))
    }

    @Test
    fun contractConstantsMatchTheFile() {
        val protocol = JSONObject(contractFile("phone_protocol.json").readText())
        assertEquals(3, protocol.getInt("contract_version"))
        assertEquals(604800000L, protocol.getJSONObject("delivery").getLong("new_pc_window_ms"))
        assertEquals(172800000L, protocol.getJSONObject("restore").getLong("suspected_restored_ms"))
        assertEquals(DeliveryBook.WINDOW_MS, protocol.getJSONObject("delivery").getLong("new_pc_window_ms"))
        assertEquals(DeliveryBook.SUSPECTED_MS, protocol.getJSONObject("restore").getLong("suspected_restored_ms"))
        assertEquals("com.sec.android.easyMover", protocol.getJSONObject("restore").getJSONArray("creators").getString(0))
    }

    @Test
    fun newPcGetsSevenDaysAndNothingOlder() {
        val now = 1_700_000_000_000L
        val baseline = now - 2 * DeliveryBook.WINDOW_MS
        val rows = listOf(
            row("old", now - DeliveryBook.WINDOW_MS - 1),
            row("edge", now - DeliveryBook.WINDOW_MS),
            row("week", now - 6 * 86_400_000L),
            row("before-baseline", baseline - 1),
        )
        val book = DeliveryBook(baseline, now, rows, mapOf("sms" to 9))
        val state = book.open("live")
        assertEquals(setOf("sms:edge", "sms:week"), state.pending)
        assertFalse(state.pending.contains("sms:old"))
        assertFalse(state.pending.contains("sms:before-baseline"))
        assertEquals(9L, state.cursors.getValue("sms"))
    }

    @Test
    fun newPcDoesNotLookBehindTheBaseline() {
        val now = 1_700_000_000_000L
        val baseline = now - 86_400_000L
        val rows = listOf(row("yesterday", now - 2 * 86_400_000L), row("today", now - 3_600_000L))
        val state = DeliveryBook(baseline, now, rows, mapOf("sms" to 4)).open("live")
        assertEquals(setOf("sms:today"), state.pending)
    }

    @Test
    fun keyRotationKeepsTheSameState() {
        val now = 1_700_000_000_000L
        val book = DeliveryBook(now - DeliveryBook.WINDOW_MS, now, listOf(row("a", now - 1000)), mapOf("sms" to 3))
        val first = book.open("pc-1")
        first.acknowledged.add("sms:a")
        first.pending.clear()
        val again = book.open("pc-1")
        assertTrue(again === first)
        assertTrue(again.acknowledged.contains("sms:a"))
        assertTrue(again.pending.isEmpty())
        val other = book.open("pc-2")
        assertEquals(setOf("sms:a"), other.pending)
    }

    @Test
    fun restoreCreatorAndSuspectedRowsStayUnsent() {
        val now = 1_700_000_000_000L
        val rows = listOf(
            row("mover", now - 1000, creator = "com.sec.android.easyMover"),
            row("live", now - 1000),
        )
        val book = DeliveryBook(0, now, rows, mapOf("sms" to 8))
        val state = book.open("pc")
        assertEquals(setOf("sms:live"), state.pending)
        assertTrue(book.restored.contains("sms:mover"))
        book.noteDelivered("sms", now)
        book.noteDelivered("sms", now - 10_000)
        assertEquals(now, book.watermark.getValue("sms"))
        val late = row("late", now - DeliveryBook.SUSPECTED_MS - 1)
        assertEquals("suspected_restored", book.classify(late))
        book.suspected.add("sms:late")
        assertTrue(book.suspected.contains("sms:late"))
        val cursor = state.cursors.getValue("sms")
        book.providerReset("sms")
        assertEquals(cursor, state.cursors.getValue("sms"))
        assertTrue(book.stopped.contains("sms"))
    }

    @Test
    fun deletedNoticeStaysUntilAck() {
        val now = 1_700_000_000_000L
        val gone = row("gone", now - 1000, present = false)
        val book = DeliveryBook(0, now, listOf(row("gone", now - 1000)), mapOf("sms" to 2))
        val state = book.open("pc")
        book.deletedBeforeAck("pc", gone)
        assertTrue(state.deleted.contains("sms:gone"))
        assertFalse(state.pending.contains("sms:gone"))
        book.acknowledgeDeleted("pc", gone)
        assertTrue(state.deleted.isEmpty())
    }

    @Test
    fun oneWriterDoesNotInterleaveFrames() {
        val frames = mutableListOf<ByteArray>()
        val writer = FrameWriter { frame -> frames.add(frame) }
        val pool = Executors.newFixedThreadPool(4)
        val start = CountDownLatch(1)
        val done = CountDownLatch(40)
        repeat(40) { index ->
            pool.submit {
                start.await()
                writer.send("{\"n\":$index}\n".toByteArray())
                done.countDown()
            }
        }
        start.countDown()
        done.await()
        pool.shutdown()
        frames.forEach { frame ->
            val text = frame.toString(Charsets.UTF_8)
            assertTrue(text.endsWith("\n"))
            JSONObject(text.trim())
        }
        assertEquals(40, frames.size)
    }

    @Test
    fun digitKeyMatchesTheSharedVectors() {
        val protocol = JSONObject(contractFile("phone_protocol.json").readText())
        val cases = protocol.getJSONArray("digit_key_vectors")
        for (index in 0 until cases.length()) {
            val case = cases.getJSONObject(index)
            val got = DigitKey.canonical(case.getString("raw"))
            if (case.isNull("e164")) assertNull(got) else assertEquals(case.getString("e164"), got)
        }
    }

    private fun row(id: String, dateMs: Long, creator: String = "com.google.android.apps.messaging", present: Boolean = true) =
        TextRow(id, "sms", dateMs, creator, 1, sendable = true, present = present)

    private fun vectors(): JSONObject = JSONObject(contractFile("phone_vectors.json").readText())

    private fun contractFile(name: String): File {
        var dir: File? = File("").absoluteFile
        repeat(8) {
            val here = dir ?: return@repeat
            val candidate = File(here, "hermes-plugins/zola_workspace/contracts/$name")
            if (candidate.isFile) return candidate
            dir = here.parentFile
        }
        error("missing $name from ${File("").absolutePath}")
    }

    private val masked = listOf(
        "Your verification code is 482913",
        "G-482913 is your Google verification code",
        "OTP 482913",
        "Your OTP is 482913. It expires in 10 minutes.",
        "PIN 4829",
        "passcode 482913",
        "one-time password 482913",
        "Use code 482913 to sign in",
        "code: AB12CD",
        "Enter 482913 to verify your device",
        "Msg: 482913 is your code",
        "WhatsApp code 482-913",
        "Apple ID code 482913",
        "Microsoft account security code 482913",
        "Amazon: 482913",
        "verification code 482913 do not share",
        "Your temporary PIN is 4829",
        "passcode: 48-29-13",
        "Login code 482913",
        "https://accounts.example/reset?token=aaaaaaaaaaaaaaaaaaaa",
        "https://id.example/verify/email",
        "https://id.example/login",
        "https://id.example/sign-in",
        "https://id.example/signin/continue",
        "https://id.example/magic/aaaaaaaaaaaaaaaaaaaa",
        "https://id.example/auth/callback",
        "https://id.example/continue?token=abcDEF1234567890abcd",
        "click to reset your password https://id.example/reset",
        "482913",
        "AB12CD",
        "code\n482913",
        "OTP\n482913",
        "Your code is 482913.",
        "verification code 482913",
        "PIN is 482913 for the transfer",
        "passcode 482913 expires today",
        "https://example.test/path/token/aaaaaaaaaaaaaaaaaaaa",
        "Use 482913 as the verification code for order discussion",
        "one-time code 482913",
        "security code 482913",
        "confirmation code 482913",
    )

    private val ordinary = listOf(
        "See you at 6:30",
        "It was $19.99",
        "Call 555-0100",
        "1600 Amphitheatre Parkway",
        "Zip 94043",
        "Order 100045",
        "Tracking 1Z999AA10123456784",
        "Score was 6 to 3",
        "Meet on 2026-10-21",
        "https://video.example/watch?v=abc",
        "https://news.example/story/12",
        "https://maps.example/place/1",
        "Table for 2 at 7",
        "Room 1204",
        "Gate B12",
        "The total is 48.29",
        "Reference 482913 is the invoice",
        "https://carrier.example/track/1Z999",
        "Birthday 04/19",
        "Extension 2048",
    )
}
