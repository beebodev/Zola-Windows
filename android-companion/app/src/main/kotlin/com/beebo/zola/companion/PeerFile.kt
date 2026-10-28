package com.beebo.zola.companion

import java.io.File

// P10-COMPANION: the pairing code is not written — P10-D12

class PeerFile(private val dir: File) {
    fun write(deviceId: String, pcId: String, address: String, lastPcSeq: Long, phoneSeq: Long) {
        val body = Canonical.json(
            mapOf(
                "device_id" to deviceId,
                "pc_id" to pcId,
                "address" to address,
                "last_pc_seq" to lastPcSeq,
                "phone_seq" to phoneSeq,
            ),
        )
        val target = File(dir, "peer.json")
        val tmp = File(dir, "peer.json.tmp")
        tmp.writeText(body, Charsets.UTF_8)
        if (!tmp.renameTo(target) && target.exists()) tmp.delete()
    }

    fun read(): String? {
        val target = File(dir, "peer.json")
        if (!target.isFile) return null
        return target.readText(Charsets.UTF_8)
    }
}
