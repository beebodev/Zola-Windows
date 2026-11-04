package com.beebo.zola.companion

// P10-COMPANION: mask the whole text before any truncation — P10-D04

object Mask {
    // Short keyword-less bodies (≤40) whose meaningful content is one 4–8 digit run
    // (optionally with a single ≤8 alnum tag) mask as verification_code. Fail closed P10-D04.
    private const val SHORT_BODY_CHARS = 40

    private val keywords = Regex(
        """\b(?:code|otp|pin|passcode|verification|verify|one-time|login|sign-in|signin)\b|\blog\s+in\b|\bsign\s+in\b""",
        RegexOption.IGNORE_CASE,
    )
    private val plainDigits = Regex("""(?<!\d)(\d{4,8})(?!\d)""")
    private val alnum = Regex(
        """(?<![A-Za-z0-9])((?=[A-Za-z0-9]*[A-Za-z])(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{5,8})(?![A-Za-z0-9])""",
    )
    private val split = Regex("""(?<!\d)((?:\d{1,6}[ -])+\d{1,6})(?!\d)""")
    private val colon = Regex("""(?m)(?:^|\n)\s*[A-Za-z][A-Za-z .'\-]{0,40}:\s*(\d{4,8})(?!\d)""")
    private val url = Regex("""https?://\S+""", RegexOption.IGNORE_CASE)
    private val pathOrName = Regex(
        """(?:^|[/?&=])(reset|verify|login|sign-in|signin|token|magic|auth)(?:$|[/?&=])""",
        RegexOption.IGNORE_CASE,
    )
    private val urlWords = Regex(
        """\b(?:reset|password|verify|login|sign-in|signin)\b|\bsign\s+in\b|\blog\s+in\b""",
        RegexOption.IGNORE_CASE,
    )
    private val onlyDigits = Regex("""\d{4,8}""")
    private val onlyAlnum = Regex("""(?=[A-Za-z0-9]*[A-Za-z])(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{6}""")
    private val onlySplit = Regex("""(?:\d{1,6}[ -])+\d{1,6}""")
    private val shortTag = Regex("""[A-Za-z0-9]{1,8}""")

    fun kind(text: String, containsOtp: Boolean = false): String {
        if (containsOtp) return "verification_code"
        if (link(text)) return "reset_link"
        val spans = mutableListOf<IntRange>()
        plainDigits.findAll(text).forEach { spans.add(it.groups[1]!!.range) }
        alnum.findAll(text).forEach { spans.add(it.groups[1]!!.range) }
        split.findAll(text).forEach { match ->
            val token = match.groupValues[1]
            val count = token.count { it.isDigit() }
            if (count in 4..8 && (token.contains('-') || token.contains(' '))) {
                spans.add(match.groups[1]!!.range)
            }
        }
        if (spans.any { near(text, it) }) return "verification_code"
        if (colon.containsMatchIn(text)) return "verification_code"
        val stripped = text.trim()
        if (onlyDigits.matches(stripped) || onlyAlnum.matches(stripped)) return "unsure"
        if (onlySplit.matches(stripped)) {
            val count = stripped.count { it.isDigit() }
            if (count in 4..8) return "unsure"
        }
        shortBody(stripped)?.let { return it }
        return "none"
    }

    /** Returns verification_code when the trimmed body is a short tag + one 4–8 digit run; else null. */
    private fun shortBody(stripped: String): String? {
        if (stripped.length > SHORT_BODY_CHARS) return null
        val matches = plainDigits.findAll(stripped).toList()
        if (matches.size != 1) return null
        val match = matches[0]
        val digitLen = match.groupValues[1].length
        val remainder = (stripped.removeRange(match.range)).trim()
        if (remainder.isEmpty()) return null // digits-only already returned unsure above
        if (!shortTag.matches(remainder)) return null
        val lettersOnly = remainder.all { it.isLetter() }
        val allCaps = remainder.all { it.isUpperCase() }
        return when {
            remainder.any { it.isDigit() } -> "verification_code" // e.g. ZP10 / AB12 + 4–8 digits
            lettersOnly && allCaps && digitLen in 6..8 -> "verification_code" // e.g. APP / AMZN
            else -> null // Title-case Zip/Order/Room + digits, or ALL-CAPS + 4–5 digits → none
        }
    }

    fun extract(text: String, maskKind: String): String? {
        if (maskKind == "reset_link") return url.find(text)?.value
        if (maskKind != "verification_code") return null
        plainDigits.find(text)?.let { return it.groupValues[1] }
        alnum.find(text)?.let { return it.groupValues[1] }
        split.find(text)?.let { match ->
            val token = match.groupValues[1]
            val count = token.count { it.isDigit() }
            if (count in 4..8) return token
        }
        colon.find(text)?.let { return it.groupValues[1] }
        return null
    }

    fun prepare(text: String, containsOtp: Boolean = false, limit: Int = 16000): Prepared {
        val mask = kind(text, containsOtp)
        if (mask != "none") return Prepared(body = "", maskKind = mask, truncated = false)
        if (text.length <= limit) return Prepared(body = text, maskKind = "none", truncated = false)
        return Prepared(body = text.substring(0, limit), maskKind = "none", truncated = true)
    }

    private fun near(text: String, range: IntRange): Boolean {
        val start = (range.first - 40).coerceAtLeast(0)
        val end = (range.last + 1 + 40).coerceAtMost(text.length)
        return keywords.containsMatchIn(text.substring(start, end))
    }

    private fun link(text: String): Boolean {
        for (match in url.findAll(text)) {
            val target = match.value
            if (pathOrName.containsMatchIn(target)) return true
            val query = target.substringAfter("?", "")
            if (query.split('&', '=', ';').any { it.matches(Regex("""[A-Za-z0-9]{20,}""")) }) return true
            if (urlWords.containsMatchIn(text)) return true
        }
        return false
    }
}

data class Prepared(val body: String, val maskKind: String, val truncated: Boolean)
