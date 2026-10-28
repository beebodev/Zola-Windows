package com.beebo.zola.companion

import android.content.ContentResolver
import android.database.Cursor
import android.net.Uri
import android.os.Bundle
import android.provider.Telephony

// P10-COMPANION: a change reads the next ids, not the whole inbox — Phase 5

class Inbox(private val resolver: ContentResolver) : TextProvider {
    override var queries: Int = 0
    override var rowsRead: Int = 0

    override fun maxId(kind: String): Long {
        queries += 1
        val args = Bundle()
        args.putInt(ContentResolver.QUERY_ARG_LIMIT, 1)
        args.putString(ContentResolver.QUERY_ARG_SQL_SORT_ORDER, "_id DESC")
        resolver.query(uri(kind), arrayOf("_id"), args, null)?.use { cursor ->
            if (cursor.moveToFirst()) return long(cursor, "_id")
        }
        return 0
    }

    override fun batch(kind: String, above: Long, also: Set<Long>, limit: Int): List<TextRecord> {
        val plan = QueryPlan.above(above, also)
        return read(kind, plan.first, plan.second, limit)
    }

    override fun recent(kind: String, floorMs: Long, limit: Int, afterId: Long): List<TextRecord> {
        val seconds = floorMs / 1000
        return read(
            kind,
            "_id>? AND (date>=? OR (date>0 AND date<1000000000000 AND date>=?))",
            listOf(afterId.toString(), floorMs.toString(), seconds.toString()),
            limit,
            "_id ASC",
        )
    }

    override fun history(selector: String, limit: Int): List<TextRecord> {
        val variants = AddressNeedles.of(selector)
        val sms = read(
            "sms",
            "thread_id=? OR address IN (${variants.joinToString(",") { "?" }})",
            listOf(selector) + variants,
            limit,
            "date DESC",
        )
        val ids = messageIds(variants, limit)
        val mms = if (ids.isEmpty()) {
            emptyList()
        } else {
            read("mms", "_id IN (${ids.joinToString(",") { "?" }})", ids, limit, "date DESC")
        }
        return (sms + mms).sortedByDescending { it.dateMs }.take(limit)
    }

    override fun one(kind: String, id: Long): TextRecord? {
        return read(kind, "_id=?", listOf(id.toString()), 1).firstOrNull()
    }

    private fun read(kind: String, selection: String, args: List<String>, limit: Int, sort: String = "_id ASC"): List<TextRecord> {
        queries += 1
        val bundle = Bundle()
        bundle.putString(ContentResolver.QUERY_ARG_SQL_SELECTION, selection)
        bundle.putStringArray(ContentResolver.QUERY_ARG_SQL_SELECTION_ARGS, args.toTypedArray())
        bundle.putString(ContentResolver.QUERY_ARG_SQL_SORT_ORDER, sort)
        bundle.putInt(ContentResolver.QUERY_ARG_LIMIT, limit)
        val rows = mutableListOf<TextRecord>()
        resolver.query(uri(kind), if (kind == "sms") SMS else MMS, bundle, null)?.use { cursor ->
            while (cursor.moveToNext() && rows.size < limit) {
                rows.add(if (kind == "sms") smsRow(cursor) else mmsRow(cursor))
                rowsRead += 1
            }
        }
        return rows
    }

    private fun smsRow(cursor: Cursor): TextRecord {
        val address = text(cursor, "address")
        val body = text(cursor, "body")
        val type = int(cursor, "type")
        return TextRecord(
            kind = "sms",
            providerId = long(cursor, "_id"),
            dateMs = CaptureRules.receivedAtMs(long(cursor, "date")),
            dateSentMs = CaptureRules.receivedAtMs(long(cursor, "date_sent")),
            senderRaw = address,
            body = body,
            direction = CaptureRules.smsDirection(type),
            threadId = text(cursor, "thread_id"),
            participants = if (address.isEmpty()) emptyList() else listOf(address),
            creator = text(cursor, "creator"),
            sendable = CaptureRules.sendable(int(cursor, "spam_report"), int(cursor, "spam_type"), text(cursor, "block_filtered_status")),
            present = true,
            containsOtp = int(cursor, "contains_otp") != 0,
            contentTypes = emptyList(),
            attachmentCount = 0,
            attachmentKind = null,
            partsMissing = false,
        )
    }

    private fun mmsRow(cursor: Cursor): TextRecord {
        val id = long(cursor, "_id")
        val loaded = parts(id)
        val parts = loaded ?: emptyList()
        val people = addresses(id)
        val sender = people.firstOrNull { it.second == 137 }?.first.orEmpty()
        val names = people.map { it.first }.filter { it.isNotEmpty() }.distinct()
        val types = listOf(text(cursor, "ct_t")) + parts.map { it.first }
        val body = parts.filter { it.first.startsWith("text/plain") }.joinToString("") { it.second }
        val attachments = parts.filter { !it.first.startsWith("text/") && it.first.isNotEmpty() }
        return TextRecord(
            kind = "mms",
            providerId = id,
            dateMs = CaptureRules.receivedAtMs(long(cursor, "date")),
            dateSentMs = CaptureRules.receivedAtMs(long(cursor, "date_sent")),
            senderRaw = sender,
            body = body,
            direction = CaptureRules.mmsDirection(int(cursor, "msg_box")),
            threadId = text(cursor, "thread_id"),
            participants = names,
            creator = text(cursor, "creator"),
            sendable = CaptureRules.sendable(int(cursor, "spam_report"), int(cursor, "spam_type"), text(cursor, "block_filtered_status")),
            present = true,
            containsOtp = false,
            contentTypes = types.filter { it.isNotEmpty() },
            attachmentCount = attachments.size,
            attachmentKind = attachments.firstOrNull()?.let { CaptureRules.attachmentKind(it.first) },
            partsMissing = loaded == null,
        )
    }

    private fun parts(id: Long): List<Pair<String, String>>? {
        val out = mutableListOf<Pair<String, String>>()
        val cursor = resolver.query(Uri.parse("content://mms/part"), arrayOf("ct", "text"), "mid=?", arrayOf(id.toString()), null)
            ?: return null
        cursor.use {
            while (it.moveToNext()) out.add(text(it, "ct") to text(it, "text"))
        }
        return out
    }

    private fun addresses(id: Long): List<Pair<String, Int>> {
        val out = mutableListOf<Pair<String, Int>>()
        resolver.query(Uri.parse("content://mms/$id/addr"), arrayOf("address", "type"), null, null, null)?.use { cursor ->
            while (cursor.moveToNext()) out.add(text(cursor, "address") to int(cursor, "type"))
        }
        return out
    }

    private fun messageIds(variants: List<String>, limit: Int): List<String> {
        queries += 1
        val ids = linkedSetOf<String>()
        resolver.query(
            Uri.parse("content://mms/addr"),
            arrayOf("msg_id"),
            "address IN (${variants.joinToString(",") { "?" }})",
            variants.toTypedArray(),
            "msg_id DESC",
        )?.use { cursor ->
            while (cursor.moveToNext() && ids.size < limit) {
                val id = text(cursor, "msg_id")
                if (id.isNotEmpty()) ids.add(id)
            }
        }
        return ids.toList()
    }

    private fun uri(kind: String): Uri = if (kind == "sms") Telephony.Sms.CONTENT_URI else Telephony.Mms.CONTENT_URI

    private fun text(cursor: Cursor, column: String): String {
        val index = cursor.getColumnIndex(column)
        if (index < 0 || cursor.isNull(index)) return ""
        return cursor.getString(index) ?: ""
    }

    private fun long(cursor: Cursor, column: String): Long {
        val index = cursor.getColumnIndex(column)
        if (index < 0 || cursor.isNull(index)) return 0
        return cursor.getLong(index)
    }

    private fun int(cursor: Cursor, column: String): Int = long(cursor, column).toInt()

    companion object {
        private val SMS = arrayOf(
            "_id", "type", "date", "date_sent", "address", "body", "thread_id", "creator",
            "spam_report", "spam_type", "block_filtered_status", "contains_otp",
        )
        private val MMS = arrayOf(
            "_id", "msg_box", "date", "date_sent", "ct_t", "thread_id", "creator",
            "spam_report", "spam_type", "block_filtered_status",
        )
    }
}
