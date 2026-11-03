package com.beebo.zola.companion

import org.json.JSONArray
import org.json.JSONObject
import java.security.MessageDigest

// P10-NOTIFY: one queue file, masked before it is written — G-MASK-BEFORE-QUEUE

data class NoticeMessage(
    val sender: String,
    val text: String,
    val timestampMs: Long,
    val fromUser: Boolean,
)

data class PostedNotice(
    val packageName: String,
    val key: String,
    val template: String,
    val category: String?,
    val channelId: String?,
    val flagNames: List<String>,
    val extrasKeys: List<String>,
    val messages: List<NoticeMessage>,
    val title: String,
    val text: String,
    val bigText: String,
    val conversationTitle: String,
    val groupConversation: Boolean,
    val whenMs: Long,
    val postMs: Long,
    val groupSummary: Boolean,
    val ongoing: Boolean,
    val foregroundService: Boolean,
    val media: Boolean,
)

class NoticeHalt : RuntimeException()

object NoticePackages {
    const val MESSENGER = "com.facebook.orca"
    const val INSTAGRAM = "com.instagram.android"
    const val LIFE360 = "com.life360.android.safetymapd"
    const val VOICEMAIL = "com.tmobile.vvm.application"
    const val COMPANION = "com.beebo.zola.companion"
    val MESSAGES = setOf("com.google.android.apps.messaging", "com.samsung.android.messaging")
    val CHAT = setOf(MESSENGER, INSTAGRAM)
    // P10-NOTIFY: PLAIN comes from the build type source set (bench adds shell) — N5–N9
    val PLAIN: Set<String> get() = NoticePlain.PACKAGES

    fun selectable(packageName: String): Boolean {
        if (packageName == COMPANION) return false
        if (packageName in MESSAGES) return false
        return packageName.isNotEmpty()
    }
}

object NoticeHash {
    fun full(material: String): String = digest(material).joinToString("") { "%02x".format(it) }

    fun prefix(material: String): String = full(material).take(16)

    private fun digest(material: String): ByteArray {
        return MessageDigest.getInstance("SHA-256").digest(material.toByteArray(Charsets.UTF_8))
    }
}

object NoticeRules {
    const val TEXT_LIMIT = 4000
    private val templates = setOf(
        "MessagingStyle",
        "MediaStyle",
        "BigTextStyle",
        "BigPictureStyle",
        "InboxStyle",
        "CallStyle",
        "DecoratedCustomViewStyle",
        "DecoratedMediaCustomViewStyle",
    )
    private val categories = setOf(
        "alarm", "call", "email", "err", "event", "msg", "navigation", "progress", "promo",
        "recommendation", "reminder", "service", "social", "status", "sys", "transport",
        "workout", "missed_call", "voicemail", "stopwatch", "location_sharing",
    )
    private val flags = setOf(
        "AUTO_CANCEL", "ONGOING_EVENT", "NO_CLEAR", "FOREGROUND_SERVICE", "GROUP_SUMMARY",
        "LOCAL_ONLY", "ONLY_ALERT_ONCE", "HIGH_PRIORITY", "BUBBLE", "INSISTENT", "NO_LIGHTS",
    )
    val extras = setOf(
        "android.title", "android.title.big", "android.text", "android.subText", "android.infoText",
        "android.summaryText", "android.bigText", "android.textLines", "android.messages",
        "android.messages.historic", "android.conversationTitle", "android.hiddenConversationTitle",
        "android.isGroupConversation", "android.messagingStyleUser", "android.selfDisplayName",
        "android.people", "android.people.list", "android.largeIcon", "android.picture",
        "android.template", "android.showWhen", "android.showChronometer", "android.chronometerCountDown",
        "android.progress", "android.progressMax", "android.progressIndeterminate",
        "android.remoteInputHistory", "android.mediaSession", "android.compactActions",
        "android.backgroundImageUri", "android.verificationIcon", "android.verificationText",
        "android.answer", "android.call", "android.hangUp", "android.colorized", "android.reduced.images",
        "android.callType", "android.callPerson", "android.callIsVideo",
    )

    fun templateToken(template: String): String {
        val name = template.substringAfterLast('.')
        if (name.isEmpty()) return "none"
        if (name in templates) return name
        return "other"
    }

    fun categoryToken(category: String?): String {
        if (category.isNullOrEmpty()) return "none"
        if (category in categories) return category
        return "other"
    }

    fun flagToken(names: List<String>): String {
        val known = names.filter { it in flags }
        if (known.isEmpty()) return "none"
        return known.joinToString(",")
    }

    fun extraToken(keys: List<String>): String {
        val known = keys.filter { it in extras }
        if (known.isEmpty()) return "none"
        return known.joinToString(",")
    }

    fun extraOther(keys: List<String>): Int = keys.count { it !in extras }

    fun excluded(notice: PostedNotice): Boolean {
        if (notice.packageName == NoticePackages.COMPANION) return true
        if (notice.packageName in NoticePackages.MESSAGES) return true
        if (notice.groupSummary || notice.ongoing || notice.foregroundService || notice.media) return true
        return false
    }

    fun newest(notice: PostedNotice): NoticeMessage? = notice.messages.maxWithOrNull(compareBy({ it.timestampMs }, { it.text }))

    fun stamp(notice: PostedNotice): String? {
        if (notice.packageName in NoticePackages.CHAT) {
            val message = newest(notice) ?: return null
            return message.timestampMs.toString()
        }
        return notice.whenMs.toString()
    }

    fun keyOf(notice: PostedNotice): String = NoticeHash.full(notice.key)

    fun identity(notice: PostedNotice): String? {
        val stamp = stamp(notice) ?: return null
        return notice.packageName + "|" + keyOf(notice) + "|" + stamp
    }

    fun postedAt(notice: PostedNotice): Long = if (notice.postMs != 0L) notice.postMs else notice.whenMs

    fun classify(notice: PostedNotice): String {
        if (excluded(notice)) return "excluded"
        if (notice.packageName in NoticePackages.CHAT) {
            val messaging = templateToken(notice.template) == "MessagingStyle"
            val messageCategory = categoryToken(notice.category) == "msg"
            if (!messaging || !messageCategory) return "filtered"
            val message = newest(notice) ?: return "filtered"
            if (message.fromUser || message.sender.isEmpty()) return "own"
            return "admitted"
        }
        if (notice.packageName in NoticePackages.PLAIN) return "admitted"
        return "filtered"
    }

    fun fields(notice: PostedNotice): Map<String, Any?>? {
        if (classify(notice) != "admitted") return null
        val posted = postedAt(notice)
        val key = keyOf(notice)
        val stamp = stamp(notice) ?: return null
        val payload = linkedMapOf<String, Any?>(
            "package" to notice.packageName,
            "notification_key" to key,
            "newest_message_timestamp" to stamp,
            "revision" to 1,
            "completeness" to "complete",
            "posted_at_ms" to posted,
            "truncated" to 0,
            "is_group" to 0,
        )
        if (notice.packageName in NoticePackages.CHAT) {
            val message = newest(notice) ?: return null
            payload["is_group"] = if (notice.groupConversation) 1 else 0
            payload["sender_display_name"] = message.sender
            applyMask(payload, message.text, notice.conversationTitle, keepTitle = true)
        } else {
            val body = if (notice.bigText.isNotEmpty()) notice.bigText else notice.text
            applyMask(payload, notice.title + "\n" + body, "", keepTitle = false)
        }
        return payload
    }

    private fun applyMask(payload: MutableMap<String, Any?>, text: String, title: String, keepTitle: Boolean) {
        val prepared = Mask.prepare(text + "\n" + title, limit = TEXT_LIMIT)
        if (prepared.maskKind != "none") {
            payload["mask_kind"] = prepared.maskKind
            payload["truncated"] = 0
            return
        }
        val shown = if (text.length <= TEXT_LIMIT) text else text.substring(0, TEXT_LIMIT)
        payload["text"] = shown
        payload["truncated"] = if (text.length > TEXT_LIMIT) 1 else 0
        if (keepTitle) payload["conversation_title"] = title
    }
}

class NoticeBook(
    private val clock: () -> Long,
    private val log: PhoneLogFile,
    private val read: () -> String?,
    private val write: (String) -> Unit,
) {
    var fault: String? = null
    var itemCap: Int = NoticeLimits.QUEUE_ITEMS
    var seenCap: Int = 2000
    private val allowlist = linkedSetOf<String>()
    private val baselined = linkedSetOf<String>()
    private val items = mutableListOf<NoticeItem>()
    private val seen = linkedMapOf<String, Long>()
    private val acked = linkedSetOf<String>()
    private val retired = linkedSetOf<String>()
    private val contentByKey = linkedMapOf<String, String>()
    private var baselineDone = false
    private var permission = 0
    private var bound = 0
    private var drops = 0
    private var ageDrops = 0
    private var filtered = 0
    private var removed = 0
    private var rejected = 0
    private var gapCount = 0
    private var gapMs = 0L
    private var gapOpen = false
    private var gapStart = 0L
    private var gapInferred = false
    private var lastGapStart = 0L
    private var lastGapEnd = 0L
    private var lastGapInferred = 0
    private var lastAlive = 0L
    private var loaded = false

    fun load() {
        if (loaded) return
        loaded = true
        val text = read() ?: return
        val root = JSONObject(text)
        copyStrings(root.optJSONArray("allowlist"), allowlist)
        allowlist.removeAll { !NoticePackages.selectable(it) }
        copyStrings(root.optJSONArray("baselined"), baselined)
        // P10-NOTIFY: normal builds drop a leftover shell allowlist entry on load — teardown
        NoticeAutoAllowlist.prune(allowlist, baselined)
        copyStrings(root.optJSONArray("acked"), acked)
        copyStrings(root.optJSONArray("retired"), retired)
        val seenJson = root.optJSONArray("seen")
        if (seenJson != null) {
            for (index in 0 until seenJson.length()) {
                val entry = seenJson.getJSONObject(index)
                seen[entry.getString("id")] = entry.getLong("at")
            }
        }
        val contentJson = root.optJSONArray("content_by_key")
        if (contentJson != null) {
            for (index in 0 until contentJson.length()) {
                val entry = contentJson.getJSONObject(index)
                contentByKey[entry.getString("key")] = entry.getString("hash")
            }
        }
        val array = root.optJSONArray("items")
        if (array != null) {
            for (index in 0 until array.length()) items.add(NoticeItem.from(array.getJSONObject(index)))
        }
        baselineDone = root.optBoolean("baseline_done")
        permission = root.optInt("listener_permission")
        bound = root.optInt("listener_bound")
        drops = root.optInt("notification_queue_drops")
        ageDrops = root.optInt("notification_age_drops")
        filtered = root.optInt("notification_filtered")
        removed = root.optInt("allowlist_removed")
        rejected = root.optInt("notification_rejected")
        gapCount = root.optInt("listener_gap_count")
        gapMs = root.optLong("listener_gap_ms_total")
        gapOpen = root.optBoolean("gap_open")
        gapStart = root.optLong("gap_start_ms")
        gapInferred = root.optBoolean("gap_inferred")
        lastGapStart = root.optLong("last_gap_start_ms")
        lastGapEnd = root.optLong("last_gap_end_ms")
        lastGapInferred = root.optInt("last_gap_inferred")
        lastAlive = root.optLong("last_alive_ms")
    }

    fun onProcessStart() {
        load()
        if (allowlist.isNotEmpty() && (bound == 1 || gapOpen)) {
            lastGapStart = if (gapOpen) gapStart else lastAlive
            lastGapEnd = clock()
            gapMs += (lastGapEnd - lastGapStart).coerceAtLeast(0L)
            gapCount += 1
            lastGapInferred = 1
            gapOpen = false
            gapInferred = false
        }
        bound = 0
        lastAlive = clock()
        save()
    }

    fun depth(): Int = items.size

    fun bound(): Int = bound

    fun health(): Map<String, Any?> {
        val oldest = items.minOfOrNull { it.postedAt } ?: 0L
        val age = if (items.isEmpty()) 0L else (clock() - oldest).coerceAtLeast(0L)
        return linkedMapOf(
            "listener_permission" to permission,
            "listener_bound" to bound,
            "allowlist_packages" to allowlist.toList(),
            "notification_queue_depth" to items.size,
            "notification_queue_oldest_age_ms" to age,
            "notification_queue_drops" to drops,
            "notification_age_drops" to ageDrops,
            "notification_filtered" to filtered,
            "allowlist_removed" to removed,
            "notification_rejected" to rejected,
            "listener_gap_count" to gapCount,
            "listener_gap_ms_total" to gapMs,
            "last_gap_start_ms" to lastGapStart,
            "last_gap_end_ms" to lastGapEnd,
            "last_gap_inferred" to lastGapInferred,
        )
    }

    fun setAllowlist(requested: Set<String>, showing: List<PostedNotice>) {
        load()
        val next = requested.filter { NoticePackages.selectable(it) }.toCollection(linkedSetOf())
        next.addAll(NoticeAutoAllowlist.PACKAGES)
        val dropped = allowlist - next
        allowlist.clear()
        allowlist.addAll(next)
        for (packageName in dropped) retire(packageName)
        for (packageName in next) {
            if (packageName in baselined) continue
            showing.filter { it.packageName == packageName }.forEach { baseline(it) }
            baselined.add(packageName)
        }
        if (allowlist.isEmpty() && gapOpen) closeGap()
        save()
    }

    // P10-NOTIFY: bench/n9 force shell onto the allowlist without a harness write — N5–N9
    fun ensureAutoAllowlist(showing: List<PostedNotice>): Boolean {
        load()
        var changed = NoticeAutoAllowlist.prune(allowlist, baselined)
        for (packageName in NoticeAutoAllowlist.PACKAGES) {
            if (allowlist.add(packageName)) changed = true
            if (packageName !in baselined) {
                showing.filter { it.packageName == packageName }.forEach { baseline(it) }
                baselined.add(packageName)
                changed = true
            }
        }
        if (changed) save()
        return changed
    }

    fun onConnected(active: List<PostedNotice>, granted: Boolean) {
        load()
        permission = if (granted) 1 else 0
        if (!granted) {
            bound = 0
            if (allowlist.isNotEmpty()) openGap(inferred = false)
            save()
            return
        }
        bound = 1
        closeGap()
        if (!baselineDone) {
            active.filter { it.packageName in allowlist }.forEach { baseline(it) }
            baselined.addAll(allowlist)
            baselineDone = true
            save()
            return
        }
        active.forEach { consider(it) }
        save()
    }

    fun onDisconnected() {
        load()
        bound = 0
        if (allowlist.isNotEmpty()) openGap(inferred = false)
        save()
    }

    fun onAccess(granted: Boolean) {
        // P10-NOTIFY: F4 refresh before every health must not rewrite the queue when nothing changed
        load()
        val next = if (granted) 1 else 0
        var changed = next != permission
        permission = next
        if (!granted && allowlist.isNotEmpty()) {
            if (!gapOpen) {
                openGap(inferred = false)
                changed = true
            }
        } else if (granted && bound == 1 && gapOpen) {
            closeGap()
            changed = true
        }
        if (changed) save()
    }

    fun onPosted(notice: PostedNotice): Boolean {
        load()
        if (notice.packageName !in baselined) {
            if (notice.packageName in allowlist) shape(notice, "baseline")
            return false
        }
        return consider(notice)
    }

    fun onAck(packageName: String, key: String, stamp: String, revision: Int, word: String): Boolean {
        load()
        if (word !in CursorMachine.ACKS) return false
        if (fault == "before-delete") throw NoticeHalt()
        val identity = "$packageName|$key|$stamp"
        if (identity in retired) return false
        val item = items.firstOrNull {
            it.packageName == packageName && it.notificationKey == key && it.stamp == stamp && it.revision == revision
        } ?: return false
        items.remove(item)
        acked.add(identity)
        if (word == "rejected") rejected += 1
        save()
        return true
    }

    fun flying(): List<NoticeItem> = items.filter { it.inFlight }

    fun waiting(): List<NoticeItem> = items.filter { !it.inFlight }

    fun markInFlight(identity: String) {
        items.firstOrNull { it.identity == identity }?.inFlight = true
        save()
    }

    fun clearInFlight(identity: String) {
        items.firstOrNull { it.identity == identity }?.inFlight = false
        save()
    }

    fun inFlightCount(): Int = items.count { it.inFlight }

    fun expire(): Boolean {
        load()
        val before = items.size
        val cutoff = clock() - WINDOW_MS
        val aged = items.filter { it.postedAt < cutoff }
        if (aged.isNotEmpty()) {
            aged.forEach { item ->
                items.remove(item)
                seen[item.identity] = clock()
                acked.add(item.identity)
            }
            ageDrops += aged.size
        }
        if (items.size != before) {
            save()
            return true
        }
        return false
    }

    fun read(active: List<PostedNotice>?, packageFilter: String?, maxItems: Int, maxChars: Int): Map<String, Any?> {
        if (bound == 0 || active == null) return linkedMapOf("status" to "listener_unbound")
        val mapped = active.mapNotNull { notice ->
            if (notice.packageName !in allowlist) return@mapNotNull null
            if (packageFilter != null && notice.packageName != packageFilter) return@mapNotNull null
            NoticeRules.fields(notice)
        }.sortedByDescending { (it["posted_at_ms"] as? Number)?.toLong() ?: 0L }
        val kept = mutableListOf<Map<String, Any?>>()
        var used = 0
        var capped = 0
        for (item in mapped) {
            if (kept.size >= maxItems) {
                capped = 1
                break
            }
            val text = item["text"]?.toString().orEmpty()
            if (kept.isEmpty() && text.length > maxChars) {
                // P10-NOTIFY: first item still respects max_characters — truncate
                val copy = item.toMutableMap()
                copy["text"] = text.take(maxChars)
                copy["truncated"] = 1
                kept.add(copy)
                used = maxChars
                capped = 1
                break
            }
            if (used > 0 && used + text.length > maxChars) {
                capped = 1
                break
            }
            kept.add(item)
            used += text.length
        }
        return linkedMapOf("status" to "ok", "items" to kept, "capped" to capped)
    }

    private fun consider(notice: PostedNotice): Boolean {
        if (notice.packageName !in allowlist) return false
        val decision = NoticeRules.classify(notice)
        if (decision != "admitted") {
            if (decision == "filtered" || decision == "own") filtered += 1
            shape(notice, decision)
            save()
            return false
        }
        val identity = NoticeRules.identity(notice) ?: return false
        if (identity in seen) {
            shape(notice, "duplicate")
            save()
            return false
        }
        val fields = NoticeRules.fields(notice) ?: return false
        if (notice.packageName in NoticePackages.PLAIN && !fields.containsKey("mask_kind")) {
            // P10-NOTIFY: plain same-key identical outgoing text is a duplicate even when when changes — F5
            val noteKey = fields.getValue("notification_key").toString()
            val hash = NoticeHash.full(fields["text"]?.toString().orEmpty())
            if (contentByKey[noteKey] == hash) {
                seen[identity] = clock()
                pruneSeen()
                shape(notice, "duplicate")
                save()
                return false
            }
            contentByKey.remove(noteKey)
            contentByKey[noteKey] = hash
        }
        if (fault == "before-write") throw NoticeHalt()
        expire()
        while (items.size >= itemCap) {
            val oldest = items.minByOrNull { it.admittedMs } ?: break
            items.remove(oldest)
            seen[oldest.identity] = clock()
            acked.add(oldest.identity)
            drops += 1
        }
        val item = NoticeItem(
            identity = identity,
            packageName = notice.packageName,
            notificationKey = fields.getValue("notification_key").toString(),
            stamp = fields.getValue("newest_message_timestamp").toString(),
            revision = 1,
            postedAt = (fields.getValue("posted_at_ms") as Number).toLong(),
            admittedMs = clock(),
            inFlight = false,
            fields = fields,
        )
        items.add(item)
        seen[identity] = clock()
        pruneSeen()
        shape(notice, "admitted")
        save()
        if (fault == "after-write") throw NoticeHalt()
        return true
    }

    private fun baseline(notice: PostedNotice) {
        val identity = NoticeRules.identity(notice) ?: return
        seen[identity] = clock()
        acked.add(identity)
        shape(notice, "baseline")
    }

    private fun retire(packageName: String) {
        val gone = items.filter { it.packageName == packageName }
        removed += gone.size
        gone.forEach { item ->
            items.remove(item)
            retired.add(item.identity)
            seen[item.identity] = clock()
        }
        baselined.remove(packageName)
    }

    private fun openGap(inferred: Boolean) {
        if (gapOpen) return
        gapOpen = true
        gapStart = clock()
        gapInferred = inferred
    }

    private fun closeGap() {
        if (!gapOpen) return
        val end = clock()
        lastGapStart = gapStart
        lastGapEnd = end
        gapMs += (end - gapStart).coerceAtLeast(0L)
        gapCount += 1
        lastGapInferred = if (gapInferred) 1 else 0
        gapOpen = false
        gapInferred = false
    }

    private fun pruneSeen() {
        if (seen.size > seenCap) {
            val ordered = seen.entries.sortedBy { it.value }
            val extra = seen.size - seenCap
            ordered.take(extra).forEach { entry ->
                seen.remove(entry.key)
                acked.remove(entry.key)
                retired.remove(entry.key)
            }
        }
        while (retired.size > seenCap) {
            retired.remove(retired.first())
        }
        while (contentByKey.size > seenCap) {
            contentByKey.remove(contentByKey.keys.first())
        }
    }

    private fun shape(notice: PostedNotice, result: String) {
        val newest = NoticeRules.newest(notice)
        log.note(
            "shape",
            mapOf(
                "package" to notice.packageName,
                "key_hash" to NoticeHash.prefix(notice.key),
                "template" to NoticeRules.templateToken(notice.template),
                "category" to NoticeRules.categoryToken(notice.category),
                "channel_id" to if (notice.channelId.isNullOrEmpty()) "none" else NoticeHash.prefix(notice.channelId),
                "flags" to NoticeRules.flagToken(notice.flagNames),
                "extras" to NoticeRules.extraToken(notice.extrasKeys),
                "extras_other" to NoticeRules.extraOther(notice.extrasKeys).toString(),
                "message_count" to notice.messages.size.toString(),
                "newest_is_user" to if (newest?.fromUser == true) "1" else "0",
                "when_ms" to notice.whenMs.toString(),
                "post_ms" to notice.postMs.toString(),
                "title_len" to notice.title.length.toString(),
                "text_len" to notice.text.length.toString(),
                "big_len" to notice.bigText.length.toString(),
                "conversation_len" to notice.conversationTitle.length.toString(),
                "result" to result,
            ),
        )
    }

    private fun save() {
        lastAlive = clock()
        val root = JSONObject()
        root.put("allowlist", JSONArray(allowlist.toList()))
        root.put("baselined", JSONArray(baselined.toList()))
        root.put("acked", JSONArray(acked.toList()))
        root.put("retired", JSONArray(retired.toList()))
        val seenJson = JSONArray()
        seen.forEach { (id, at) ->
            seenJson.put(JSONObject().put("id", id).put("at", at))
        }
        root.put("seen", seenJson)
        val contentJson = JSONArray()
        contentByKey.forEach { (key, hash) ->
            contentJson.put(JSONObject().put("key", key).put("hash", hash))
        }
        root.put("content_by_key", contentJson)
        val array = JSONArray()
        items.forEach { array.put(it.toJson()) }
        root.put("items", array)
        root.put("baseline_done", baselineDone)
        root.put("listener_permission", permission)
        root.put("listener_bound", bound)
        root.put("notification_queue_drops", drops)
        root.put("notification_age_drops", ageDrops)
        root.put("notification_filtered", filtered)
        root.put("allowlist_removed", removed)
        root.put("notification_rejected", rejected)
        root.put("listener_gap_count", gapCount)
        root.put("listener_gap_ms_total", gapMs)
        root.put("gap_open", gapOpen)
        root.put("gap_start_ms", gapStart)
        root.put("gap_inferred", gapInferred)
        root.put("last_gap_start_ms", lastGapStart)
        root.put("last_gap_end_ms", lastGapEnd)
        root.put("last_gap_inferred", lastGapInferred)
        root.put("last_alive_ms", lastAlive)
        write(root.toString())
    }

    private fun copyStrings(array: JSONArray?, into: MutableSet<String>) {
        if (array == null) return
        for (index in 0 until array.length()) into.add(array.getString(index))
    }

    companion object {
        const val WINDOW_MS = 604_800_000L
    }
}

class NoticeItem(
    val identity: String,
    val packageName: String,
    val notificationKey: String,
    val stamp: String,
    val revision: Int,
    val postedAt: Long,
    val admittedMs: Long,
    var inFlight: Boolean,
    val fields: Map<String, Any?>,
) {
    fun eventFields(): Map<String, Any?> {
        val payload = linkedMapOf<String, Any?>("type" to "notifications.event")
        fields.forEach { payload[it.key] = it.value }
        return payload
    }

    fun toJson(): JSONObject {
        val json = JSONObject()
        json.put("identity", identity)
        json.put("package", packageName)
        json.put("notification_key", notificationKey)
        json.put("newest_message_timestamp", stamp)
        json.put("revision", revision)
        json.put("posted_at_ms", postedAt)
        json.put("admitted_ms", admittedMs)
        json.put("in_flight", inFlight)
        json.put("fields", JSONObject(fields))
        return json
    }

    companion object {
        fun from(json: JSONObject): NoticeItem {
            val fieldsJson = json.getJSONObject("fields")
            return NoticeItem(
                identity = json.getString("identity"),
                packageName = json.getString("package"),
                notificationKey = json.getString("notification_key"),
                stamp = json.getString("newest_message_timestamp"),
                revision = json.optInt("revision", 1),
                postedAt = json.getLong("posted_at_ms"),
                admittedMs = json.optLong("admitted_ms"),
                inFlight = json.optBoolean("in_flight"),
                fields = toMap(fieldsJson),
            )
        }
    }
}
