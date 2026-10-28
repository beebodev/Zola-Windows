package com.beebo.zola.companion

import java.io.File

// P10-COMPANION: one lock, then the socket write — Phase 5

class FrameWriter(private val sink: (ByteArray) -> Unit) {
    private val lock = java.util.concurrent.locks.ReentrantLock()

    fun send(frame: ByteArray) {
        lock.lock()
        try {
            sink(frame.copyOf())
        } finally {
            lock.unlock()
        }
    }
}
