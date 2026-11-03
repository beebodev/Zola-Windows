package com.beebo.zola.companion

// P10-NOTIFY: bench auto-allowlists shell; no prune while installed — N5–N8 / N11–N12

object NoticeAutoAllowlist {
    const val SHELL = "com.android.shell"
    val PACKAGES: Set<String> = setOf(SHELL)

    fun prune(allowlist: MutableSet<String>, baselined: MutableSet<String>): Boolean = false
}
