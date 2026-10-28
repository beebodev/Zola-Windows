package com.beebo.zola.companion

// P10-COMPANION: four pairing frames, then the code is dropped — P10-D12

class PairingSession {
    var deviceId: String = ""
        private set
    var seq: Long = 0
        private set
    var pcId: String = ""
        private set
    var pcKey: String = ""
        private set
    var lastPcSeq: Long = 0
        private set
    var code: String? = null
        private set
    var paired: Boolean = false
        private set
    var deliveryKept: Boolean = false
        private set

    fun begin(deviceId: String, seq: Long, code: String) {
        this.deviceId = deviceId
        this.seq = seq
        this.code = code
        paired = false
    }

    fun phoneOpen(sentAtMs: Long, publicPem: String): Map<String, Any?> {
        seq += 1
        return envelope("phone_open", sentAtMs) + mapOf("public_pem" to publicPem)
    }

    fun acceptPcBind(payload: Map<String, Any?>, macOk: Boolean): Boolean {
        if (!macOk) return false
        if (payload["type"] != "pc_bind") return false
        val id = payload["pc_id"]?.toString().orEmpty()
        val key = payload["public_pem"]?.toString().orEmpty()
        if (id.isEmpty() || key.isEmpty()) return false
        deliveryKept = pcId.isNotEmpty() && pcId == id
        if (pcKey.isNotEmpty() && pcKey != key) lastPcSeq = 0
        pcId = id
        pcKey = key
        return true
    }

    fun phoneBind(sentAtMs: Long, publicPem: String): Map<String, Any?> {
        seq += 1
        return envelope("phone_bind", sentAtMs) + mapOf("public_pem" to publicPem)
    }

    fun acceptPcOk(payload: Map<String, Any?>): Boolean {
        if (payload["type"] != "pc_ok") return false
        code = null
        paired = true
        return true
    }

    private fun envelope(type: String, sentAtMs: Long): Map<String, Any?> = mapOf(
        "type" to type,
        "device_id" to deviceId,
        "seq" to seq,
        "sent_at_ms" to sentAtMs,
        "contract_version" to 3,
    )
}
