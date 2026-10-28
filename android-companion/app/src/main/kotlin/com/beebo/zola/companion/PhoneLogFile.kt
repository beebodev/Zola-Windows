package com.beebo.zola.companion

import java.io.File

// P10-COMPANION: metadata only, one megabyte, three backups — CP-G12

class PhoneLogFile(
    private val dir: File,
    private val clock: () -> Long = { System.currentTimeMillis() },
) {
    var mirror: ((String) -> Unit)? = null

    fun note(event: String, fields: Map<String, String>) {
        val safe = fields.filterKeys { it !in FORBIDDEN }
        val body = safe.entries.joinToString(" ") { it.key + "=" + it.value }
        val line = buildString {
            append(clock())
            append(" zola.companion ")
            append(event)
            if (body.isNotEmpty()) {
                append(' ')
                append(body)
            }
        }
        mirror?.invoke(line)
        dir.mkdirs()
        val file = File(dir, "companion.log")
        val bytes = (line + "\n").toByteArray(Charsets.UTF_8)
        if (file.exists() && file.length() + bytes.size > LIMIT) rotate(file)
        file.appendBytes(bytes)
    }

    fun text(): String {
        val file = File(dir, "companion.log")
        if (!file.isFile) return ""
        return file.readText(Charsets.UTF_8)
    }

    private fun rotate(file: File) {
        val third = File(dir, "companion.log.3")
        if (third.exists()) third.delete()
        val second = File(dir, "companion.log.2")
        if (second.exists()) second.renameTo(third)
        val first = File(dir, "companion.log.1")
        if (first.exists()) first.renameTo(second)
        file.renameTo(first)
    }

    companion object {
        const val LIMIT = 1_000_000
        val FORBIDDEN = setOf("body", "address", "sender_raw", "code", "url", "selector", "http")
    }
}
