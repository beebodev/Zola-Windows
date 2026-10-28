package com.beebo.zola.companion

// P10-COMPANION: the same canonical bytes Python signs — P10-D12

object Canonical {
    fun json(value: Any?): String = encode(plain(value))

    fun bytes(value: Any?): ByteArray = json(value).toByteArray(Charsets.UTF_8)

    private fun plain(value: Any?): Any? = when (value) {
        is String -> plainString(value)
        is Map<*, *> -> value.mapKeys { plain(it.key) }.mapValues { plain(it.value) }
        is List<*> -> value.map { plain(it) }
        else -> value
    }

    private fun plainString(value: String): String = buildString(value.length) {
        var index = 0
        while (index < value.length) {
            val ch = value[index]
            if (Character.isHighSurrogate(ch) && index + 1 < value.length && Character.isLowSurrogate(value[index + 1])) {
                append(ch)
                append(value[index + 1])
                index += 2
            } else if (Character.isHighSurrogate(ch) || Character.isLowSurrogate(ch)) {
                append('\uFFFD')
                index += 1
            } else {
                append(ch)
                index += 1
            }
        }
    }

    private fun encode(value: Any?): String = when (value) {
        null -> "null"
        is Boolean -> if (value) "true" else "false"
        is Int -> value.toString()
        is Long -> value.toString()
        is Map<*, *> -> value.entries
            .sortedBy { it.key.toString() }
            .joinToString(prefix = "{", postfix = "}", separator = ",") {
                encode(it.key.toString()) + ":" + encode(it.value)
            }
        is List<*> -> value.joinToString(prefix = "[", postfix = "]", separator = ",") { encode(it) }
        is String -> encodeString(value)
        else -> encodeString(value.toString())
    }

    private fun encodeString(text: String): String = buildString {
        append('"')
        text.forEach { ch ->
            when {
                ch == '"' -> append("\\\"")
                ch == '\\' -> append("\\\\")
                ch == '\b' -> append("\\b")
                ch == '\u000C' -> append("\\f")
                ch == '\n' -> append("\\n")
                ch == '\r' -> append("\\r")
                ch == '\t' -> append("\\t")
                ch.code < 0x20 -> append("\\u%04x".format(ch.code))
                else -> append(ch)
            }
        }
        append('"')
    }
}
