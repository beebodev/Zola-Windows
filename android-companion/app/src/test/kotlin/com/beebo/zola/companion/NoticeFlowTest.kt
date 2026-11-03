package com.beebo.zola.companion

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean

// P10-NOTIFY: engine-level notification rules — Phase 4

class NoticeFlowTest {
    @Test
    fun chatIdentityUsesTheNewestMessageTimestamp() {
        val rig = ready()
        rig.engine.onPosted(chat(text = "one", stamp = 100, whenMs = 50))
        rig.engine.onPosted(chat(text = "two", stamp = 200, whenMs = 50))
        val stamps = events(rig).map { it.getString("newest_message_timestamp") }
        assertEquals(listOf("100", "200"), stamps)
        rig.engine.onPosted(chat(text = "two", stamp = 200, whenMs = 90))
        rig.engine.onPosted(chat(text = "two", stamp = 200, whenMs = 90))
        assertEquals(2, events(rig).size)
    }

    @Test
    fun plainIdentityUsesWhen() {
        val rig = ready()
        rig.engine.onPosted(plain(key = "place", whenMs = 10, title = "Arrived", text = "home"))
        rig.engine.onPosted(plain(key = "place", whenMs = 11, title = "Left", text = "home"))
        rig.engine.onPosted(plain(key = "place", whenMs = 11, title = "Left", text = "home"))
        assertEquals(listOf("10", "11"), events(rig).map { it.getString("newest_message_timestamp") })
        val payload = events(rig).first()
        assertEquals("Arrived\nhome", payload.getString("text"))
        assertFalse(payload.has("sender_display_name"))
        assertFalse(payload.has("conversation_title"))
    }

    @Test
    fun plainMessengerPostingWithTitleAndTextIsFiltered() {
        val rig = ready()
        val before = health(rig).getInt("notification_filtered")
        rig.engine.onPosted(
            PostedNotice(
                packageName = NoticePackages.MESSENGER,
                key = "orca-slot",
                template = "other",
                category = null,
                channelId = "messages",
                flagNames = listOf("AUTO_CANCEL"),
                extrasKeys = listOf("android.title", "android.text"),
                messages = emptyList(),
                title = "Ada Person",
                text = "hello there",
                bigText = "",
                conversationTitle = "",
                groupConversation = false,
                whenMs = 100,
                postMs = 100,
                groupSummary = false,
                ongoing = false,
                foregroundService = false,
                media = false,
            ),
        )
        assertTrue(events(rig).isEmpty())
        assertTrue(health(rig).getInt("notification_filtered") > before)
    }

    @Test
    fun messageOnlyFilterFailsClosed() {
        val rig = ready()
        rig.engine.onPosted(chat(template = "BigTextStyle", category = "social", text = "liked"))
        rig.engine.onPosted(chat(fromUser = true, text = "mine"))
        rig.engine.onPosted(chat(text = "kept"))
        assertEquals(listOf("kept"), events(rig).map { it.optString("text") })
        val health = health(rig)
        assertTrue(health.getInt("notification_filtered") >= 2)
    }

    @Test
    fun exclusionsAndAnEmptyAllowlistProduceNothing() {
        val rig = Rig()
        rig.pair()
        rig.engine.onPosted(chat())
        assertTrue(events(rig).isEmpty())
        rig.engine.setAllowlist(
            setOf(NoticePackages.MESSENGER, NoticePackages.MESSAGES.first(), NoticePackages.COMPANION),
        )
        rig.engine.onListenerConnected(emptyList(), true)
        rig.engine.onPosted(chat(summary = true))
        rig.engine.onPosted(chat(ongoing = true))
        rig.engine.onPosted(chat(foreground = true))
        rig.engine.onPosted(chat(media = true))
        rig.engine.onPosted(chat(pkg = NoticePackages.MESSAGES.first()))
        rig.engine.onPosted(chat(pkg = NoticePackages.COMPANION))
        assertTrue(events(rig).isEmpty())
        val names = health(rig).getJSONArray("allowlist_packages")
        assertEquals(1, names.length())
        assertEquals(NoticePackages.MESSENGER, names.getString(0))
    }

    @Test
    fun groupSenderIsTheNewestPerson() {
        val rig = ready()
        val notice = chat(group = true, title = "Family", sender = "Ada", text = "hi")
        rig.engine.onPosted(notice)
        val payload = events(rig).single()
        assertEquals("Ada", payload.getString("sender_display_name"))
        assertEquals("Family", payload.getString("conversation_title"))
        assertEquals(1, payload.getInt("is_group"))
        assertEquals("hi", payload.getString("text"))
    }

    @Test
    fun aTitleOnlyCodeIsMaskedOnTheEventAndTheRead() {
        val code = "482913"
        val rig = ready()
        val chatNotice = chat(text = "hello there", title = "code is $code", sender = "Ada Person")
        rig.engine.onPosted(chatNotice)
        val event = events(rig).single()
        assertFalse(event.has("text"))
        assertFalse(event.has("conversation_title"))
        assertEquals("Ada Person", event.getString("sender_display_name"))
        assertEquals("verification_code", event.getString("mask_kind"))
        assertAbsent(rig, code)
        val queue = rig.store.queue
        rig.engine.activeNotices = { listOf(chatNotice) }
        rig.replySigned("notifications.read.request", mapOf("request_id" to "r1", "max_items" to 10, "max_characters" to 1000))
        val read = rig.signedFrames().last { it.getJSONObject("payload").getString("type") == "notifications.read.result" }
        val item = read.getJSONObject("payload").getJSONArray("items").getJSONObject(0)
        assertFalse(item.has("text"))
        assertFalse(item.has("conversation_title"))
        assertEquals("Ada Person", item.getString("sender_display_name"))
        assertEquals(queue, rig.store.queue)
        assertAbsent(rig, code)

        val plainNotice = plain(title = "code is $code", text = "arrived")
        rig.engine.onPosted(plainNotice)
        val plainEvent = events(rig).last()
        assertFalse(plainEvent.has("text"))
        assertFalse(plainEvent.has("sender_display_name"))
        assertFalse(plainEvent.has("conversation_title"))
        rig.engine.activeNotices = { listOf(plainNotice) }
        rig.replySigned("notifications.read.request", mapOf("request_id" to "r2", "max_items" to 10, "max_characters" to 1000))
        val plainRead = rig.signedFrames().last { it.getJSONObject("payload").getString("type") == "notifications.read.result" }
        val plainItem = plainRead.getJSONObject("payload").getJSONArray("items").getJSONObject(0)
        assertFalse(plainItem.has("text"))
        assertFalse(plainItem.has("sender_display_name"))
        assertAbsent(rig, code)
    }

    @Test
    fun aCodePastTheLimitStillMasks() {
        val rig = ready()
        val code = "482913"
        rig.engine.onPosted(chat(text = "x".repeat(4001) + " code $code", title = "chat"))
        val payload = events(rig).single()
        assertFalse(payload.has("text"))
        assertEquals("verification_code", payload.getString("mask_kind"))
        assertAbsent(rig, code)
    }

    @Test
    fun queueSurvivesRestartAndAcksDelete() {
        val rig = ready()
        rig.engine.onPosted(chat(text = "queued"))
        assertEquals(1, events(rig).size)
        val next = rig.restart()
        next.engine.boot()
        assertEquals(1, events(next).count { it.optString("text") == "queued" })
        for (word in listOf("stored", "updated", "duplicate", "suppressed", "rejected")) {
            val one = ready()
            one.engine.onPosted(chat(key = word, text = word))
            ack(one, events(one).single(), word)
            assertFalse(one.store.queue!!.contains("\"items\":[{"))
        }
    }

    @Test
    fun overflowAgeAndDuplicateAreCounted() {
        val rig = ready()
        rig.engine.noticeItemCap = 1
        rig.engine.onPosted(chat(key = "a", text = "old"))
        rig.engine.onPosted(chat(key = "b", text = "new"))
        assertTrue(health(rig).getInt("notification_queue_drops") >= 1)
        assertTrue(rig.store.queue!!.contains("new"))
        assertFalse(rig.store.queue!!.contains("\"text\":\"old\""))

        val aged = ready()
        aged.engine.onPosted(chat(postMs = aged.clock.now, text = "stale"))
        aged.clock.now += NoticeBook.WINDOW_MS + 5
        aged.engine.tick()
        assertTrue(health(aged).getInt("notification_age_drops") >= 1)
    }

    @Test
    fun anUnackedNoticeDoesNotStallTheNextOrAText() {
        val rig = ready()
        repeat(5) { rig.engine.onPosted(chat(key = "k$it", stamp = 1000L + it, text = "m$it")) }
        ack(rig, events(rig).first(), "stored")
        assertEquals(5, events(rig).size)
        rig.provider.add(sms(90, "a text"))
        rig.engine.onProviderChanged()
        assertTrue(rig.signedFrames().any { it.getJSONObject("payload").optString("type") == "messages.event" && it.getJSONObject("payload").optString("provider_id") == "90" })
    }

    @Test
    fun cancelAfterQueueStillDeliversAndEveryShowingAckIsNotQueuedAgain() {
        val rig = ready()
        val notice = chat(text = "stay")
        rig.engine.onPosted(notice)
        rig.engine.onRemoved(notice.key)
        assertEquals(1, events(rig).size)
        ack(rig, events(rig).single(), "stored")
        rig.engine.activeNotices = { listOf(notice) }
        rig.engine.onListenerConnected(listOf(notice), true)
        assertEquals(1, events(rig).size)
    }

    @Test
    fun removingAnAppRetiresAnInFlightItemAndALateAckIsIgnored() {
        val rig = ready()
        rig.engine.onPosted(chat(text = "retire-me"))
        val sent = events(rig).single()
        rig.engine.setAllowlist(emptySet())
        assertTrue(health(rig).getInt("allowlist_removed") >= 1)
        assertFalse(rig.store.queue!!.contains("retire-me"))
        val before = rig.link.sent.count {
            JSONObject(it.toString(Charsets.UTF_8)).getJSONObject("payload").optString("text") == "retire-me"
        }
        rig.engine.onFailure("failure")
        rig.link.open = true
        rig.engine.onOpen()
        val after = rig.link.sent.count {
            JSONObject(it.toString(Charsets.UTF_8)).getJSONObject("payload").optString("text") == "retire-me"
        }
        assertEquals(before, after)
        ack(rig, sent, "stored")
        assertFalse(rig.store.queue!!.contains("retire-me"))
        assertEquals(1, health(rig).getInt("allowlist_removed"))
    }

    @Test
    fun baselineOnFirstBindAndOnAddSendsNothingAlreadyShowing() {
        val rig = Rig()
        rig.pair()
        val old = chat(text = "already")
        rig.engine.setAllowlist(setOf(NoticePackages.MESSENGER))
        rig.engine.onListenerConnected(listOf(old), true)
        assertTrue(events(rig).isEmpty())
        rig.engine.onPosted(chat(text = "fresh", stamp = 9))
        assertEquals("fresh", events(rig).single().getString("text"))

        val added = ready()
        val showing = chat(key = "old", text = "showing", stamp = 4)
        added.engine.activeNotices = { listOf(showing) }
        added.engine.setAllowlist(setOf(NoticePackages.INSTAGRAM))
        added.engine.onPosted(showing)
        assertTrue(events(added).isEmpty())
        added.engine.onPosted(chat(pkg = NoticePackages.INSTAGRAM, key = "new", text = "now", stamp = 8))
        assertEquals("now", events(added).single().getString("text"))
    }

    @Test
    fun addingAnAppBaselinesWhatActiveNoticesReportsWithoutCallerPassingShowing() {
        // F3: PairingActivity calls setAllowlist(packages) only; engine must read currentNotices()
        val rig = Rig()
        rig.pair()
        rig.engine.onListenerConnected(emptyList(), true)
        val showing = chat(pkg = NoticePackages.INSTAGRAM, key = "old", text = "showing", stamp = 4)
        rig.engine.activeNotices = { listOf(showing) }
        rig.engine.setAllowlist(setOf(NoticePackages.INSTAGRAM))
        assertTrue(events(rig).isEmpty())
        rig.engine.onPosted(showing)
        assertTrue(events(rig).isEmpty())
        rig.engine.onListenerConnected(listOf(showing), true)
        assertTrue(events(rig).isEmpty())
        rig.engine.onPosted(chat(pkg = NoticePackages.INSTAGRAM, key = "new", text = "now", stamp = 8))
        assertEquals("now", events(rig).single().getString("text"))
    }

    @Test
    fun listenerPermissionFollowsAccessGrantAndOpensAGap() {
        // F4
        val rig = ready()
        val before = health(rig).getInt("listener_gap_count")
        rig.engine.onAccessChanged(false)
        val revoked = health(rig)
        assertEquals(0, revoked.getInt("listener_permission"))
        rig.engine.onAccessChanged(true)
        val granted = health(rig)
        assertEquals(1, granted.getInt("listener_permission"))
        assertEquals(0, granted.getInt("last_gap_inferred"))
        assertTrue(granted.getInt("listener_gap_count") > before)
    }

    @Test
    fun plainSameKeyIdenticalOutgoingContentIsADuplicateEvenWhenWhenChanges() {
        // F5
        val rig = ready()
        rig.engine.onPosted(plain(key = "place", whenMs = 10, title = "Arrived", text = "home"))
        rig.engine.onPosted(plain(key = "place", whenMs = 11, title = "Arrived", text = "home"))
        assertEquals(1, events(rig).size)
        assertTrue(rig.log.text().contains("result=duplicate"))
        rig.engine.onPosted(plain(key = "place", whenMs = 12, title = "Left", text = "work"))
        assertEquals(2, events(rig).size)
        rig.engine.onPosted(plain(key = "vm", pkg = NoticePackages.VOICEMAIL, whenMs = 20, title = "Voicemail", text = "code 111111"))
        rig.engine.onPosted(plain(key = "vm", pkg = NoticePackages.VOICEMAIL, whenMs = 21, title = "Voicemail", text = "code 222222"))
        assertEquals(2, events(rig).count { it.optString("package") == NoticePackages.VOICEMAIL })
        assertTrue(events(rig).filter { it.optString("package") == NoticePackages.VOICEMAIL }.all { it.getString("mask_kind") == "verification_code" })
    }

    @Test
    fun defaultBuildNeverTreatsShellAsAPlainAppOrAutoAllowlistsIt() {
        // P10-NOTIFY: debug/release unit variant — shell is bench/n9 only
        assertFalse(NoticeAutoAllowlist.SHELL in NoticePackages.PLAIN)
        assertTrue(NoticeAutoAllowlist.PACKAGES.isEmpty())
        assertEquals(
            "filtered",
            NoticeRules.classify(
                plain(
                    key = "shell-slot",
                    pkg = NoticeAutoAllowlist.SHELL,
                    whenMs = 10,
                    title = "Bench",
                    text = "ZP10-shell",
                ),
            ),
        )
        val allow = linkedSetOf(NoticeAutoAllowlist.SHELL, NoticePackages.LIFE360)
        val baselined = linkedSetOf(NoticeAutoAllowlist.SHELL)
        assertTrue(NoticeAutoAllowlist.prune(allow, baselined))
        assertFalse(NoticeAutoAllowlist.SHELL in allow)
        assertFalse(NoticeAutoAllowlist.SHELL in baselined)
        assertTrue(NoticePackages.LIFE360 in allow)
        val rig = Rig()
        rig.pair()
        rig.engine.onListenerConnected(emptyList(), true)
        rig.engine.boot()
        rig.engine.setAllowlist(setOf(NoticeAutoAllowlist.SHELL))
        val names = health(rig).optJSONArray("allowlist_packages")
        val listed = (0 until (names?.length() ?: 0)).map { names!!.getString(it) }
        assertFalse(listed.contains(NoticeAutoAllowlist.SHELL))
    }

    @Test
    fun emptyAllowlistDoesNotOpenAGapOnUnbindOrRestart() {
        // F6
        val rig = Rig()
        rig.pair()
        rig.engine.onListenerConnected(emptyList(), true)
        assertEquals(0, health(rig).getInt("listener_gap_count"))
        rig.engine.onListenerDisconnected()
        assertEquals(0, health(rig).getInt("listener_gap_count"))
        val next = rig.restart()
        next.engine.boot()
        val body = next.signedFrames().last { it.getJSONObject("payload").getString("type") == "device.health" }.getJSONObject("payload")
        assertEquals(0, body.getInt("listener_gap_count"))
    }

    @Test
    fun retiredIsPrunedWithTheSeenCapAndALateAckStaysIgnored() {
        // F7
        val rig = ready()
        rig.engine.noticeSeenCap = 2
        val all = setOf(
            NoticePackages.MESSENGER,
            NoticePackages.INSTAGRAM,
            NoticePackages.LIFE360,
            NoticePackages.VOICEMAIL,
        )
        val withoutMessenger = setOf(
            NoticePackages.INSTAGRAM,
            NoticePackages.LIFE360,
            NoticePackages.VOICEMAIL,
        )
        fun bounce(key: String, text: String, stamp: Long): JSONObject {
            rig.engine.onPosted(chat(key = key, text = text, stamp = stamp))
            val event = events(rig).last { it.optString("text") == text }
            rig.engine.setAllowlist(withoutMessenger)
            assertFalse(rig.store.queue.orEmpty().contains("\"text\":\"$text\""))
            rig.engine.setAllowlist(all)
            return event
        }
        val first = bounce("a", "retire-a", 1)
        bounce("b", "retire-b", 2)
        bounce("c", "retire-c", 3)
        ack(rig, first, "stored")
        assertFalse(rig.store.queue.orEmpty().contains("\"text\":\"retire-a\""))
        rig.engine.onPosted(chat(key = "a", text = "retire-a", stamp = 1))
        assertEquals(2, events(rig).count { it.optString("text") == "retire-a" })
    }

    @Test
    fun readTruncatesTheFirstItemWhenMaxCharactersIsSmaller() {
        // F8
        val rig = ready()
        val long = plain(key = "a", postMs = 30, title = "Title", text = "abcdefghij")
        rig.engine.activeNotices = { listOf(long) }
        rig.engine.onListenerConnected(listOf(long), true)
        rig.replySigned(
            "notifications.read.request",
            mapOf("request_id" to "u-small", "max_items" to 5, "max_characters" to 8, "package" to NoticePackages.LIFE360),
        )
        val body = lastRead(rig)
        assertEquals("ok", body.getString("status"))
        assertEquals(1, body.getJSONArray("items").length())
        val item = body.getJSONArray("items").getJSONObject(0)
        assertEquals(8, item.getString("text").length)
        assertEquals(1, item.getInt("truncated"))
    }

    @Test
    fun readsAreLiveMaskedAndBounded() {
        val rig = ready()
        rig.replySigned("notifications.read.request", mapOf("request_id" to "u1"))
        assertEquals("listener_unbound", lastRead(rig).getString("status"))
        assertEquals(0, rig.wakes.held.count { it == "zola:read" })
        val first = plain(key = "a", postMs = 20, title = "A", text = "one")
        val second = plain(key = "b", postMs = 30, title = "B", text = "two")
        val like = chat(template = "BigTextStyle", category = "social", text = "like")
        rig.engine.activeNotices = { listOf(first, second, like) }
        val before = rig.store.queue
        rig.replySigned(
            "notifications.read.request",
            mapOf("request_id" to "u2", "max_items" to 1, "max_characters" to 1000, "package" to NoticePackages.LIFE360),
        )
        val body = lastRead(rig)
        assertEquals("ok", body.getString("status"))
        assertEquals(1, body.getInt("capped"))
        assertEquals(1, body.getJSONArray("items").length())
        assertEquals("B\ntwo", body.getJSONArray("items").getJSONObject(0).getString("text"))
        assertEquals(before, rig.store.queue)
        assertFalse(rig.store.text!!.contains("two"))
    }

    @Test
    fun crashBoundariesKeepSeenWithTheQueueOrAnAck() {
        val rig = ready()
        rig.engine.noticeFault = "before-write"
        assertTrue(throwsHalt { rig.engine.onPosted(chat(text = "missed")) })
        assertFalse(rig.store.queue!!.contains("missed"))
        rig.engine.noticeFault = null
        rig.engine.onPosted(chat(text = "missed"))
        assertEquals(1, events(rig).size)

        val wrote = ready()
        wrote.engine.noticeFault = "after-write"
        assertTrue(throwsHalt { wrote.engine.onPosted(chat(text = "held")) })
        val restarted = wrote.restart()
        restarted.engine.boot()
        assertEquals(1, events(restarted).count { it.optString("text") == "held" })

        val acked = ready()
        acked.engine.onPosted(chat(text = "late"))
        acked.engine.noticeFault = "before-delete"
        assertTrue(throwsHalt { ack(acked, events(acked).single(), "stored") })
        val again = acked.restart()
        again.engine.boot()
        ack(again, events(again).last { it.optString("text") == "late" }, "duplicate")
        assertFalse(again.store.queue!!.contains("late"))
    }

    @Test
    fun evictedSeenIsAdmittedAgainAndThePcDuplicateDeletesIt() {
        val rig = ready()
        rig.engine.noticeSeenCap = 1
        rig.engine.onPosted(chat(key = "a", text = "first"))
        ack(rig, events(rig).single(), "stored")
        rig.engine.onPosted(chat(key = "b", stamp = 2, text = "second"))
        ack(rig, events(rig).last(), "stored")
        rig.engine.onPosted(chat(key = "a", text = "first"))
        assertEquals(2, events(rig).count { it.optString("text") == "first" })
        ack(rig, events(rig).last(), "duplicate")
        assertFalse(rig.store.queue!!.contains("first"))
    }

    @Test
    fun gapsAndHealthCarryPackageNamesOnly() {
        val rig = ready()
        rig.engine.onListenerDisconnected()
        rig.engine.onListenerConnected(emptyList(), true)
        val body = health(rig)
        assertEquals(1, body.getInt("listener_bound"))
        assertEquals(1, body.getInt("listener_permission"))
        assertTrue(body.getInt("listener_gap_count") >= 1)
        assertEquals(0, body.getInt("last_gap_inferred"))
        assertEquals(NoticePackages.MESSENGER, body.getJSONArray("allowlist_packages").getString(0))
        rig.engine.onPosted(chat(text = "hidden-body"))
        assertFalse(health(rig).toString().contains("hidden-body"))
        val dead = rig.restart()
        dead.engine.boot()
        val inferred = dead.signedFrames().last { it.getJSONObject("payload").getString("type") == "device.health" }.getJSONObject("payload")
        assertEquals(1, inferred.getInt("last_gap_inferred"))
        assertTrue(inferred.getInt("listener_gap_count") >= 1)
    }

    @Test
    fun shapeLinesCarryNoAppSuppliedString() {
        val rig = ready()
        rig.engine.onPosted(
            chat(
                text = "secret-body",
                title = "secret-title",
                sender = "secret-sender",
                channel = "secret-channel",
                extras = listOf("android.text", "com.example.secret"),
            ),
        )
        val line = rig.log.text().lineSequence().last { "shape " in it }
        assertTrue(line.contains("channel_id="))
        assertFalse(line.contains("secret-channel"))
        assertFalse(line.contains("secret-body"))
        assertFalse(line.contains("secret-title"))
        assertFalse(line.contains("secret-sender"))
        assertFalse(line.contains("com.example.secret"))
        assertTrue(line.contains("extras=android.text"))
        assertTrue(line.contains("extras_other=1"))
        assertTrue(line.contains("result=admitted"))
    }

    @Test
    fun extraStateKeysStillRestoreTextsAndNoticesStayInTheirFile() {
        val rig = Rig()
        rig.pair()
        val saved = JSONObject(rig.store.text)
        saved.put("notification_extra", 1)
        rig.store.text = saved.toString()
        val next = rig.restart()
        next.engine.boot()
        next.provider.add(sms(81, "still-there"))
        next.engine.onProviderChanged()
        assertTrue(next.signedFrames().any { it.getJSONObject("payload").optString("provider_id") == "81" })
        next.engine.setAllowlist(setOf(NoticePackages.MESSENGER))
        next.engine.onListenerConnected(emptyList(), true)
        next.engine.onPosted(chat(text = "queue-only"))
        assertTrue(next.store.queue!!.contains("queue-only"))
        assertFalse(next.store.text!!.contains("queue-only"))
    }

    @Test
    fun textsThatArriveWhileConnectsFailRemainPendingForTheOldPc() {
        val rig = Rig()
        rig.pair()
        rig.link.open = false
        rig.engine.onFailure("failure")
        rig.provider.add(sms(70, "while-down", date = rig.clock.now))
        rig.engine.onProviderChanged()
        assertEquals(1, providerEvents(rig, "70"))
        rig.engine.handoff("100.102.206.71", "12345678")
        rig.replyPairing("pc_bind", mapOf("pc_id" to "pc-new", "public_pem" to rig.pcPublic))
        rig.replyPairing("pc_ok", emptyMap())
        assertEquals(2, providerEvents(rig, "70"))
        rig.engine.handoff("100.102.206.71", "12345678")
        rig.replyPairing("pc_bind", mapOf("pc_id" to "pc-live", "public_pem" to rig.pcPublic))
        rig.replyPairing("pc_ok", emptyMap())
        assertEquals(3, providerEvents(rig, "70"))
    }

    @Test
    fun acksFromAnotherThreadDeliverEachNoticeOnce() {
        val rig = ready()
        val worker = Executors.newSingleThreadExecutor()
        val finished = AtomicBoolean(false)
        val acker = Thread {
            var seen = 0
            var attempts = 0
            while (attempts < 40 && (!finished.get() || seen < 4)) {
                seen = worker.submit<Int> {
                    rig.engine.onAlarm(IdleSample(false, true, false))
                    rig.engine.onListenerDisconnected()
                    rig.engine.onListenerConnected(emptyList(), true)
                    events(rig).forEach { ack(rig, it, "stored") }
                    events(rig).size
                }.get()
                attempts += 1
            }
        }
        acker.start()
        worker.submit {
            repeat(4) { rig.engine.onPosted(chat(key = "n$it", stamp = 3000L + it, text = "n$it")) }
        }.get()
        finished.set(true)
        acker.join(10_000)
        worker.shutdown()
        assertTrue(worker.awaitTermination(5, TimeUnit.SECONDS))
        assertEquals(4, events(rig).map { it.getString("text") }.toSet().size)
    }

    @Test
    fun readCodeDoesNotReturnANotificationCode() {
        val rig = ready()
        val code = "482913"
        rig.engine.onPosted(chat(title = "code is $code", text = "hello"))
        rig.replySigned("code.read.request", mapOf("request_id" to "c-notice", "provider_id" to "1", "kind" to "notif"))
        val result = rig.signedFrames().last { it.getJSONObject("payload").getString("type") == "code.read.result" }.getJSONObject("payload")
        assertEquals("not_text", result.getString("status"))
        assertFalse(result.has("value"))
        assertAbsent(rig, code)
    }

    private fun ready(): Rig {
        val rig = Rig()
        rig.pair()
        rig.engine.setAllowlist(
            setOf(
                NoticePackages.MESSENGER,
                NoticePackages.INSTAGRAM,
                NoticePackages.LIFE360,
                NoticePackages.VOICEMAIL,
            ),
        )
        rig.engine.onListenerConnected(emptyList(), true)
        return rig
    }

    private fun events(rig: Rig): List<JSONObject> {
        return rig.signedFrames().map { it.getJSONObject("payload") }.filter { it.optString("type") == "notifications.event" }
    }

    private fun health(rig: Rig): JSONObject {
        return rig.signedFrames().last { it.getJSONObject("payload").getString("type") == "device.health" }.getJSONObject("payload")
    }

    private fun lastRead(rig: Rig): JSONObject {
        return rig.signedFrames().last { it.getJSONObject("payload").getString("type") == "notifications.read.result" }.getJSONObject("payload")
    }

    private fun providerEvents(rig: Rig, id: String): Int {
        return rig.signedFrames().count {
            val payload = it.getJSONObject("payload")
            payload.optString("type") == "messages.event" && payload.optString("provider_id") == id
        }
    }

    private fun ack(rig: Rig, payload: JSONObject, word: String) {
        rig.replySigned(
            "notifications.ack",
            mapOf(
                "package" to payload.getString("package"),
                "notification_key" to payload.getString("notification_key"),
                "newest_message_timestamp" to payload.getString("newest_message_timestamp"),
                "revision" to payload.getInt("revision"),
                "result" to word,
            ),
        )
    }

    private fun assertAbsent(rig: Rig, code: String) {
        val frames = rig.link.sent.joinToString("\n") { it.toString(Charsets.UTF_8) }
        assertFalse(frames.contains(code))
        assertFalse(rig.log.text().contains(code))
        assertFalse(rig.store.text.orEmpty().contains(code))
        assertFalse(rig.store.queue.orEmpty().contains(code))
    }

    private fun throwsHalt(block: () -> Unit): Boolean {
        return try {
            block()
            false
        } catch (_: NoticeHalt) {
            true
        }
    }

    private fun chat(
        key: String = "conv",
        pkg: String = NoticePackages.MESSENGER,
        whenMs: Long = 1_700_000_000_000L,
        postMs: Long = 1_700_000_000_000L,
        sender: String = "Ada",
        text: String = "hello",
        stamp: Long = 70,
        fromUser: Boolean = false,
        category: String? = "msg",
        template: String = "MessagingStyle",
        title: String = "Ada",
        group: Boolean = false,
        summary: Boolean = false,
        ongoing: Boolean = false,
        foreground: Boolean = false,
        media: Boolean = false,
        channel: String? = "messages",
        extras: List<String> = listOf("android.text", "android.messages"),
    ) = PostedNotice(
        packageName = pkg,
        key = key,
        template = template,
        category = category,
        channelId = channel,
        flagNames = listOf("AUTO_CANCEL"),
        extrasKeys = extras,
        messages = listOf(NoticeMessage(sender, text, stamp, fromUser)),
        title = title,
        text = text,
        bigText = "",
        conversationTitle = title,
        groupConversation = group,
        whenMs = whenMs,
        postMs = postMs,
        groupSummary = summary,
        ongoing = ongoing,
        foregroundService = foreground,
        media = media,
    )

    private fun plain(
        key: String = "life",
        pkg: String = NoticePackages.LIFE360,
        whenMs: Long = 1_700_000_000_000L,
        postMs: Long = 1_700_000_000_000L,
        title: String = "Arrived",
        text: String = "home",
    ) = PostedNotice(
        packageName = pkg,
        key = key,
        template = "MessagingStyle",
        category = "msg",
        channelId = "Place",
        flagNames = listOf("AUTO_CANCEL"),
        extrasKeys = listOf("android.title", "android.text", "android.messages"),
        messages = listOf(NoticeMessage("circle", text, whenMs, false)),
        title = title,
        text = text,
        bigText = "",
        conversationTitle = "circle",
        groupConversation = false,
        whenMs = whenMs,
        postMs = postMs,
        groupSummary = false,
        ongoing = false,
        foregroundService = false,
        media = false,
    )

    private fun sms(id: Long, body: String, date: Long = id) = TextRecord(
        kind = "sms",
        providerId = id,
        dateMs = date,
        dateSentMs = date,
        senderRaw = "+15551234567",
        body = body,
        direction = "in",
        threadId = "1",
        participants = listOf("+15551234567"),
        creator = "com.google.android.apps.messaging",
        sendable = true,
        present = true,
        containsOtp = false,
        contentTypes = emptyList(),
        attachmentCount = 0,
        attachmentKind = null,
        partsMissing = false,
    )
}
