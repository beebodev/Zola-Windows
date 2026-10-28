package com.beebo.zola.companion

import java.io.File

// P10-COMPANION: acknowledged ids stay with the PC identity — P10-D03

class AckFile(private val dir: File) {
    fun load(pcId: String): Set<String> {
        val file = File(dir, fileName(pcId))
        if (!file.isFile) return emptySet()
        return file.readLines().map { it.trim() }.filter { it.isNotEmpty() }.toSet()
    }

    fun add(pcId: String, key: String) {
        val file = File(dir, fileName(pcId))
        val current = load(pcId).toMutableSet()
        if (!current.add(key)) return
        val tmp = File(dir, file.name + ".tmp")
        tmp.writeText(current.joinToString("\n"), Charsets.UTF_8)
        if (!tmp.renameTo(file) && file.exists()) tmp.delete()
    }

    private fun fileName(pcId: String): String {
        val safe = pcId.filter { it.isLetterOrDigit() }
        return "acks-$safe.txt"
    }
}
