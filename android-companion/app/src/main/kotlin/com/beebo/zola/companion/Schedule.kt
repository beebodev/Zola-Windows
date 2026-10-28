package com.beebo.zola.companion

// P10-COMPANION: reconnect is an exact alarm; a ping is never armed — P10-D07

class WakeGate {
    var held: String? = null
        private set
    var releases: Int = 0
        private set

    fun <T> hold(tag: String, block: () -> T): T {
        held = tag
        try {
            return block()
        } finally {
            held = null
            releases += 1
        }
    }

    fun acquire(tag: String) {
        held = tag
    }

    fun release() {
        if (held != null) {
            held = null
            releases += 1
        }
    }
}

class Backoff(private val clock: () -> Long) {
    private val steps = longArrayOf(10_000, 30_000, 60_000)
    private var index = 0
    val armed = mutableListOf<String>()

    fun scheduleReconnect(): Long {
        val delay = steps[index.coerceAtMost(steps.lastIndex)]
        if (index < steps.lastIndex) index += 1
        armed.add("reconnect")
        return clock() + delay
    }

    fun reset() {
        index = 0
    }
}

data class IdleSample(
    val deepDoze: Boolean,
    val interactive: Boolean,
    val charging: Boolean,
    val lightDoze: Boolean = false,
)

class ReconnectLog {
    val samples = mutableListOf<IdleSample>()

    fun reconnect(sample: IdleSample) {
        samples.add(sample)
    }
}

object AlarmPlan {
    fun decide(canScheduleExact: Boolean): String = if (canScheduleExact) "exact" else "ask"
}

class Debounce(private val updateMs: Long = 1000, private val maxMs: Long = 5000) {
    private var first: Long? = null

    fun delay(now: Long): Long {
        val start = first ?: now.also { first = it }
        return if (now - start >= maxMs) 0 else updateMs
    }

    fun reset() {
        first = null
    }
}
