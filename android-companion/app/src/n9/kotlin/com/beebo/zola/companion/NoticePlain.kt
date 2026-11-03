package com.beebo.zola.companion

// P10-NOTIFY: n9 is test-only; shell is plain so N9 can use cmd notification post — N9

object NoticePlain {
    val PACKAGES = setOf(
        NoticePackages.LIFE360,
        NoticePackages.VOICEMAIL,
        NoticeAutoAllowlist.SHELL,
    )
}
