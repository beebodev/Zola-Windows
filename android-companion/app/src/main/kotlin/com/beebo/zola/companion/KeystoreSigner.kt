package com.beebo.zola.companion

import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import java.security.KeyPairGenerator
import java.security.KeyStore
import java.security.PrivateKey
import java.security.Signature
import java.security.spec.ECGenParameterSpec
import java.util.Base64

// P10-COMPANION: the phone key is generated in StrongBox or TEE, never a test key — P10-D12

class KeystoreSigner(private val alias: String = "zola-companion") {
    fun ensure() {
        val store = keyStore()
        if (store.containsAlias(alias)) return
        val generator = KeyPairGenerator.getInstance(KeyProperties.KEY_ALGORITHM_EC, "AndroidKeyStore")
        try {
            generator.initialize(spec(true))
            generator.generateKeyPair()
        } catch (_: Exception) {
            generator.initialize(spec(false))
            generator.generateKeyPair()
        }
    }

    fun publicPem(): String {
        ensure()
        val encoded = keyStore().getCertificate(alias).publicKey.encoded
        val body = Base64.getMimeEncoder(64, byteArrayOf('\n'.code.toByte())).encodeToString(encoded)
        return "-----BEGIN PUBLIC KEY-----\n$body\n-----END PUBLIC KEY-----\n"
    }

    fun sign(payload: Map<String, Any?>): String {
        ensure()
        val key = keyStore().getKey(alias, null) as PrivateKey
        val signature = Signature.getInstance("SHA256withECDSA")
        signature.initSign(key)
        signature.update(Canonical.bytes(payload))
        return Base64.getEncoder().encodeToString(signature.sign())
    }

    private fun spec(strongBox: Boolean): KeyGenParameterSpec {
        return KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_SIGN)
            .setAlgorithmParameterSpec(ECGenParameterSpec("secp256r1"))
            .setDigests(KeyProperties.DIGEST_SHA256)
            .setIsStrongBoxBacked(strongBox)
            .build()
    }

    private fun keyStore(): KeyStore = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
}
