package com.beebo.zola.companion

// P10-NOTIFY: no auto-allowlist on the normal build; strip bench leftovers on load — teardown

object NoticeAutoAllowlist {
    const val SHELL = "com.android.shell"
    val PACKAGES: Set<String> = emptySet()

    fun prune(allowlist: MutableSet<String>, baselined: MutableSet<String>): Boolean {
        val removed = allowlist.remove(SHELL)
        baselined.remove(SHELL)
        return removed
    }
}
