package com.beebo.zola.companion

// P10-COMPANION: a frame over the contract limit is not built — P10-D12

object Frames {
    const val LIMIT = 262144

    fun build(payload: Map<String, Any?>, kind: String, signature: String): ByteArray? {
        val json = "{\"magic\":\"ZPC1\",\"kind\":${Canonical.json(kind)},\"signature\":${Canonical.json(signature)},\"payload\":${Canonical.json(payload)}}\n"
        val bytes = json.toByteArray(Charsets.UTF_8)
        if (bytes.size > LIMIT) return null
        return bytes
    }
}
