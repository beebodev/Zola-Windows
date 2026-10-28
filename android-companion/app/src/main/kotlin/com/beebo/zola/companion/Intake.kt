package com.beebo.zola.companion

import org.json.JSONArray
import org.json.JSONObject
import java.security.KeyFactory
import java.security.MessageDigest
import java.security.Signature
import java.security.spec.X509EncodedKeySpec
import java.util.Base64
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

// P10-COMPANION: the phone checks PC frames in the contract order — P10-D12

data class VerifyContext(
    val pairedPublic: String = "",
    val rejectedPublics: List<String> = emptyList(),
    val pairedDeviceId: String = "",
    val lastSeq: Long = 0,
    val nowMs: Long = 0,
    val pairingCode: String = "",
    val frameLimit: Int = 262144,
    val textLimit: Int = 16000,
    val notificationLimit: Int = 4000,
    val staleWindow: Long = 120000,
    val supportedVersions: Set<Int> = setOf(3),
    val magic: String = "ZPC1",
    val frameKinds: Set<String> = setOf("signed", "pairing"),
    val separator: String = "\u001f",
)

object Intake {
    fun mac(code: String, payload: Map<String, Any?>): String {
        val hmac = Mac.getInstance("HmacSHA256")
        hmac.init(SecretKeySpec(code.toByteArray(Charsets.UTF_8), "HmacSHA256"))
        return Base64.getEncoder().encodeToString(hmac.doFinal(Canonical.bytes(payload)))
    }

    fun macMatches(code: String, payload: Map<String, Any?>, signature: String): Boolean {
        if (signature.isEmpty() || code.isEmpty()) return false
        val expected = mac(code, payload).toByteArray(Charsets.UTF_8)
        val actual = signature.toByteArray(Charsets.UTF_8)
        return MessageDigest.isEqual(expected, actual)
    }

    fun verifySignature(publicPem: String, payload: Map<String, Any?>, signature: String): Boolean {
        if (signature.isEmpty() || publicPem.isEmpty()) return false
        return try {
            val key = publicKey(publicPem)
            val verifier = Signature.getInstance("SHA256withECDSA")
            verifier.initVerify(key)
            verifier.update(Canonical.bytes(payload))
            verifier.verify(Base64.getDecoder().decode(signature))
        } catch (_: Exception) {
            false
        }
    }

    fun classify(raw: ByteArray, ctx: VerifyContext): String {
        if (raw.size > ctx.frameLimit) return "too-large"
        val parsed = try {
            JSONObject(raw.toString(Charsets.UTF_8))
        } catch (_: Exception) {
            return "malformed"
        }
        if (parsed.optString("magic") != ctx.magic) return "malformed"
        val kind = parsed.optString("kind")
        if (kind !in ctx.frameKinds) return "malformed"
        val payloadJson = parsed.optJSONObject("payload") ?: return "malformed"
        val payload = toMap(payloadJson)
        for (field in listOf("type", "device_id", "seq", "sent_at_ms", "contract_version")) {
            if (!payload.containsKey(field)) return "malformed"
        }
        for (field in listOf("device_id", "provider_id", "kind", "package", "notification_key", "newest_message_timestamp")) {
            if (ctx.separator in (payload[field]?.toString() ?: "")) return "malformed"
        }
        val signature = parsed.optString("signature")
        if (signature.isEmpty()) return "unsigned"
        if (kind == "pairing") {
            if (!macMatches(ctx.pairingCode, payload, signature)) return "bad-signature"
        } else if (ctx.pairedPublic.isNotEmpty() && verifySignature(ctx.pairedPublic, payload, signature)) {
            // paired key
        } else if (ctx.rejectedPublics.any { it.isNotEmpty() && verifySignature(it, payload, signature) }) {
            return "unknown-key"
        } else {
            return "bad-signature"
        }
        if (kind != "pairing" && ctx.pairedDeviceId.isNotEmpty() && payload["device_id"] != ctx.pairedDeviceId) {
            return "wrong-device"
        }
        val seq = asLong(payload["seq"]) ?: return "malformed"
        val sent = asLong(payload["sent_at_ms"]) ?: return "malformed"
        val version = asLong(payload["contract_version"]) ?: return "malformed"
        val newDevice = kind == "pairing" && ctx.pairedDeviceId.isNotEmpty() && payload["device_id"] != ctx.pairedDeviceId
        if (!newDevice && seq <= ctx.lastSeq) return "replay"
        if (kotlin.math.abs(sent - ctx.nowMs) > ctx.staleWindow) return "stale"
        if (version.toInt() !in ctx.supportedVersions) return "version"
        if (Canonical.bytes(payload).size > ctx.frameLimit) return "too-large"
        val type = payload["type"]?.toString() ?: ""
        if (type == "notifications.event" && (payload["text"]?.toString()?.length ?: 0) > ctx.notificationLimit) {
            return "too-large"
        }
        val body = payload["body"]
        if (body is String && body.length > ctx.textLimit) return "too-large"
        return "accept"
    }

    fun decide(case: JSONObject, keys: JSONObject, vectors: JSONObject): String {
        if (case.has("raw_bytes")) {
            return classify(ByteArray(case.getInt("raw_bytes")) { 'x'.code.toByte() }, VerifyContext())
        }
        if (case.has("payload_raw") && !case.has("payload")) {
            val parsed = try {
                JSONObject(case.getString("payload_raw"))
            } catch (_: Exception) {
                return "malformed"
            }
            val wrapped = JSONObject()
                .put("magic", "ZPC1")
                .put("kind", "signed")
                .put("signature", "x")
                .put("payload", parsed)
            val pubs = keys.getJSONObject("keys")
            return classify(
                wrapped.toString().toByteArray(Charsets.UTF_8),
                context(case, pubs, vectors, pubs.getJSONObject("paired").getString("public_pem")),
            )
        }
        val payload = toMap(case.getJSONObject("payload")).toMutableMap()
        if (case.has("pad_bytes")) payload["pad"] = "x".repeat(case.getInt("pad_bytes"))
        val kind = if (case.optString("kind") == "pairing") "pairing" else "signed"
        val signature = case.optString("signature")
        val frame = "{\"magic\":\"ZPC1\",\"kind\":${Canonical.json(kind)},\"signature\":${Canonical.json(signature)},\"payload\":${Canonical.json(payload)}}"
        val pubs = keys.getJSONObject("keys")
        val pinned = if (case.optString("signed_by") == "pc" && pubs.has("pc")) {
            pubs.getJSONObject("pc").getString("public_pem")
        } else {
            pubs.getJSONObject("paired").getString("public_pem")
        }
        val pairedId = when {
            case.optString("name") == "wrong-device" -> keys.optString("paired_device_id", vectors.optString("paired_device_id"))
            case.has("device_id") -> case.getString("device_id")
            else -> keys.optString("paired_device_id", vectors.optString("paired_device_id"))
        }
        val ctx = context(case, pubs, vectors, pinned).copy(
            pairedDeviceId = pairedId,
        )
        return classify(frame.toByteArray(Charsets.UTF_8), ctx)
    }

    private fun context(case: JSONObject, pubs: JSONObject, vectors: JSONObject, pairedPublic: String): VerifyContext {
        return VerifyContext(
            pairedPublic = pairedPublic,
            rejectedPublics = listOf(
                pubs.getJSONObject("old").getString("public_pem"),
                pubs.getJSONObject("unauthorized").getString("public_pem"),
            ),
            lastSeq = if (case.has("last_accepted_seq")) case.getLong("last_accepted_seq") else vectors.getLong("last_accepted_seq"),
            nowMs = if (case.has("now_ms")) case.getLong("now_ms") else vectors.getLong("now_ms"),
            pairingCode = case.optString("pairing_code", vectors.optString("pairing_code")),
        )
    }

    private fun publicKey(pem: String): java.security.PublicKey {
        val body = pem
            .replace("-----BEGIN PUBLIC KEY-----", "")
            .replace("-----END PUBLIC KEY-----", "")
            .replace("\\s".toRegex(), "")
        val bytes = Base64.getDecoder().decode(body)
        return KeyFactory.getInstance("EC").generatePublic(X509EncodedKeySpec(bytes))
    }

    private fun asLong(value: Any?): Long? = when (value) {
        is Int -> value.toLong()
        is Long -> value
        is Number -> value.toLong()
        else -> null
    }
}

internal fun toMap(value: JSONObject): Map<String, Any?> {
    val out = linkedMapOf<String, Any?>()
    val keys = value.keys()
    while (keys.hasNext()) {
        val key = keys.next()
        out[key] = toKotlin(value.get(key))
    }
    return out
}

private fun toKotlin(value: Any?): Any? = when (value) {
    null, JSONObject.NULL -> null
    is JSONObject -> toMap(value)
    is JSONArray -> List(value.length()) { index -> toKotlin(value.get(index)) }
    else -> value
}
