package com.beebo.zola.companion

import java.io.File

// P10-COMPANION: install id, cursors, and baseline land in one rename — P10-D03

class InstallFile(private val dir: File) {
    fun writeOnce(deviceId: String, smsCursor: Long, mmsCursor: Long, baselineMs: Long): Boolean {
        val target = File(dir, "install.json")
        if (target.exists()) return false
        val body = Canonical.json(
            mapOf(
                "device_id" to deviceId,
                "sms_cursor" to smsCursor,
                "mms_cursor" to mmsCursor,
                "baseline_ms" to baselineMs,
            ),
        )
        val tmp = File(dir, "install.json.tmp")
        tmp.writeText(body, Charsets.UTF_8)
        if (!tmp.renameTo(target)) {
            tmp.delete()
            return false
        }
        return true
    }

    fun read(): String? {
        val target = File(dir, "install.json")
        if (!target.isFile) return null
        return target.readText(Charsets.UTF_8)
    }

    fun stringField(name: String): String? {
        val text = read() ?: return null
        val marker = "\"$name\":\""
        val start = text.indexOf(marker)
        if (start < 0) return null
        val from = start + marker.length
        val end = text.indexOf('"', from)
        if (end < 0) return null
        return text.substring(from, end)
    }

    fun longField(name: String): Long? {
        val text = read() ?: return null
        val marker = "\"$name\":"
        val start = text.indexOf(marker)
        if (start < 0) return null
        val from = start + marker.length
        val endComma = text.indexOf(',', from)
        val endBrace = text.indexOf('}', from)
        val end = when {
            endComma < 0 -> endBrace
            endBrace < 0 -> endComma
            else -> minOf(endComma, endBrace)
        }
        if (end < 0) return null
        return text.substring(from, end).toLongOrNull()
    }
}
