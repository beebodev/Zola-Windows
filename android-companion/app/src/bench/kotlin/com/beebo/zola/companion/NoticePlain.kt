package com.beebo.zola.companion

// P10-NOTIFY: bench is test-only; shell is plain for cmd notification post — N5–N8 / N11–N12

object NoticePlain {
    val PACKAGES = setOf(
        NoticePackages.LIFE360,
        NoticePackages.VOICEMAIL,
        NoticeAutoAllowlist.SHELL,
    )
}
