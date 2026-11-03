package com.beebo.zola.companion

// P10-NOTIFY: row text is a pure function of the stored allowlist

data class AllowlistRow(
    val pkg: String,
    val label: String,
    val checked: Boolean,
    val enabled: Boolean,
    val reason: String,
)

data class AllowlistLists(
    val visible: List<AllowlistRow>,
    val hidden: List<AllowlistRow>,
    val never: List<AllowlistRow>,
)

object AllowlistRows {
    const val TEXTS_REASON = "Texts already come from the message store"

    fun lists(apps: List<Pair<String, String>>, stored: Set<String>): AllowlistLists {
        val visible = mutableListOf<AllowlistRow>()
        val hidden = mutableListOf<AllowlistRow>()
        val never = mutableListOf<AllowlistRow>()
        for ((pkg, appLabel) in apps) {
            if (!NoticePackages.selectable(pkg)) {
                val name = appLabel.ifBlank { "Messages" }
                never.add(AllowlistRow(pkg, name, checked = false, enabled = false, reason = TEXTS_REASON))
            } else if (pkg in stored) {
                visible.add(AllowlistRow(pkg, appLabel, checked = true, enabled = true, reason = ""))
            } else {
                hidden.add(AllowlistRow(pkg, appLabel, checked = false, enabled = true, reason = ""))
            }
        }
        val order = compareBy<AllowlistRow>({ it.label.lowercase() }, { it.pkg })
        return AllowlistLists(visible.sortedWith(order), hidden.sortedWith(order), never.sortedWith(order))
    }

    fun toggle(stored: Set<String>, pkg: String): Set<String> {
        if (!NoticePackages.selectable(pkg)) return stored
        val now = stored.toMutableSet()
        if (!now.add(pkg)) now.remove(pkg)
        return now
    }

    fun label(pkg: String, appLabel: String, stored: Set<String>): String {
        if (pkg in NoticePackages.MESSAGES) {
            val name = appLabel.ifBlank { "Messages" }
            return "$name\n$TEXTS_REASON"
        }
        val state = if (pkg in stored) "selected" else "not selected"
        return "$pkg $state"
    }
}
