package com.beebo.zola.companion

// P10-NOTIFY: n9 auto-allowlists shell; no prune while installed — N9

object NoticeAutoAllowlist {
    const val SHELL = "com.android.shell"
    val PACKAGES: Set<String> = setOf(SHELL)

    fun prune(allowlist: MutableSet<String>, baselined: MutableSet<String>): Boolean = false
}
