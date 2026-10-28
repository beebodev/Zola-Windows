package com.beebo.zola.companion

import android.app.AlarmManager
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.database.ContentObserver
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import android.net.Uri
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.PowerManager
import android.provider.Telephony
import android.util.Log
import androidx.core.app.NotificationCompat
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.InputStream
import java.io.OutputStream
import java.net.InetSocketAddress
import java.net.Socket
import java.net.URI
import java.nio.file.AtomicMoveNotSupportedException
import java.nio.file.Files
import java.nio.file.StandardCopyOption
import java.security.MessageDigest
import java.security.SecureRandom
import java.util.Base64
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.locks.ReentrantLock

// P10-COMPANION: the service is the shell; the engine owns the link — Phase 5

class CompanionService : Service() {
    private val worker = Executors.newSingleThreadExecutor()
    private val timer = Executors.newSingleThreadScheduledExecutor()
    private val power by lazy { getSystemService(PowerManager::class.java) }
    private val alarms by lazy { ExactAlarms(this) }
    private val wakes by lazy { PowerWakes(power) }
    private val link = OkHttpLink(worker)
    private val store by lazy { FileStore(File(filesDir, "companion-state.json")) }
    private val phoneLog by lazy { PhoneLogFile(filesDir) }
    private val provider by lazy { Inbox(contentResolver) }
    private val writer by lazy { FrameWriter { frame -> link.send(frame) } }
    private val engine by lazy {
        phoneLog.mirror = { line -> Log.i(TAG, line) }
        CompanionEngine(
            { System.currentTimeMillis() },
            provider,
            link,
            alarms,
            wakes,
            KeystorePort(KeystoreSigner()),
            store,
            phoneLog,
            writer,
            idle = { idleSample() },
        ) { getSystemService(AlarmManager::class.java).canScheduleExactAlarms() }
    }
    private var observing = false
    private var networkRegistered = false

    private val observer = object : ContentObserver(Handler(Looper.getMainLooper())) {
        override fun onChange(selfChange: Boolean) {
            worker.execute { engine.onProviderChanged() }
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startInForeground()
        registerObservers()
        registerNetwork()
        val sample = idleSample()
        val reconnect = intent?.action == ACTION_RECONNECT
        worker.execute {
            noteDevice()
            val code = Handoff.takeCode()
            val address = Handoff.takeAddress()
            if (!address.isNullOrEmpty() && !code.isNullOrEmpty()) engine.handoff(address, code)
            else engine.boot()
            if (reconnect) engine.onAlarm(sample)
            rememberInstall()
        }
        return START_STICKY
    }

    override fun onDestroy() {
        if (observing) contentResolver.unregisterContentObserver(observer)
        worker.execute {
            link.close("phone-shutdown")
            wakes.release("zola:event")
            wakes.release("zola:read")
        }
        timer.shutdown()
        super.onDestroy()
    }

    private var ticking = false

    private fun startInForeground() {
        val manager = getSystemService(NotificationManager::class.java)
        val channel = NotificationChannel(CHANNEL, "Companion", NotificationManager.IMPORTANCE_LOW)
        manager.createNotificationChannel(channel)
        val notification: Notification = NotificationCompat.Builder(this, CHANNEL)
            .setSmallIcon(android.R.drawable.stat_notify_sync)
            .setContentTitle("Zola companion")
            .setContentText("Link")
            .setOngoing(true)
            .build()
        startForeground(NOTICE_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_REMOTE_MESSAGING)
        if (!ticking) {
            ticking = true
            timer.scheduleWithFixedDelay({ worker.execute { engine.tick() } }, 60, 60, TimeUnit.SECONDS)
        }
    }

    private fun registerObservers() {
        if (observing) return
        if (checkSelfPermission(android.Manifest.permission.READ_SMS) != PackageManager.PERMISSION_GRANTED) return
        contentResolver.registerContentObserver(Telephony.Sms.CONTENT_URI, true, observer)
        contentResolver.registerContentObserver(Telephony.Mms.CONTENT_URI, true, observer)
        observing = true
    }

    private fun registerNetwork() {
        if (networkRegistered) return
        val connectivity = getSystemService(ConnectivityManager::class.java)
        val request = NetworkRequest.Builder().addTransportType(NetworkCapabilities.TRANSPORT_VPN).build()
        connectivity.registerNetworkCallback(
            request,
            object : ConnectivityManager.NetworkCallback() {
                override fun onAvailable(network: Network) {
                    worker.execute { engine.onNetworkUp() }
                }
            },
        )
        networkRegistered = true
    }

    private fun noteDevice() {
        var held = 0
        if (checkSelfPermission(android.Manifest.permission.READ_SMS) == PackageManager.PERMISSION_GRANTED) held += 1
        if (checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED) held += 1
        val battery = power.isIgnoringBatteryOptimizations(packageName)
        engine.noteDevice(held, battery)
    }

    private fun rememberInstall() {
        val file = InstallFile(filesDir)
        if (file.read() != null) return
        file.writeOnce(engine.deviceId(), provider.maxId("sms"), provider.maxId("mms"), System.currentTimeMillis())
    }

    private fun idleSample(): IdleSample {
        val battery = getSystemService(android.os.BatteryManager::class.java)
        return IdleSample(
            deepDoze = power.isDeviceIdleMode,
            lightDoze = power.isDeviceLightIdleMode,
            interactive = power.isInteractive,
            charging = battery.isCharging,
        )
    }

    companion object {
        const val CHANNEL = "companion"
        const val NOTICE_ID = 41
        const val EXTRA_ADDRESS = "address"
        const val ACTION_RECONNECT = "com.beebo.zola.companion.RECONNECT"
        const val TAG = "zola.companion"

        fun linkUrl(address: String, port: Int = 47821): String {
            val host = address.trim()
            if (host.startsWith("ws://") || host.startsWith("wss://")) return host
            if (host.substringAfterLast(':').all { it.isDigit() } && host.contains(':')) return "ws://$host"
            return "ws://$host:$port"
        }
    }
}

private class OkHttpLink(private val worker: java.util.concurrent.Executor) : LinkPort {
    override var listener: LinkListener = object : LinkListener {
        override fun onOpen() {}
        override fun onMessage(text: String) {}
        override fun onClosing() {}
        override fun onClosed(reason: String) {}
        override fun onFailure(reason: String) {}
    }
    private val random = SecureRandom()
    private val lock = ReentrantLock()
    private val open = AtomicBoolean(false)
    private val generation = AtomicInteger()
    private var socket: Socket? = null
    private var output: OutputStream? = null

    override fun connect(url: String) {
        val target = URI(url)
        val host = target.host ?: throw IllegalArgumentException("bad-address")
        val port = if (target.port == -1) 80 else target.port
        val path = target.rawPath.ifEmpty { "/" }
        val gen = generation.incrementAndGet()
        Thread {
            var opened: Socket? = null
            try {
                val sock = Socket()
                opened = sock
                sock.tcpNoDelay = true
                sock.connect(InetSocketAddress(host, port), 10_000)
                if (gen != generation.get()) {
                    sock.close()
                    return@Thread
                }
                handshake(sock, host, port, path)
                lock.lock()
                try {
                    if (gen != generation.get()) {
                        sock.close()
                        return@Thread
                    }
                    socket = sock
                    output = sock.getOutputStream()
                    open.set(true)
                } finally {
                    lock.unlock()
                }
                val sent = java.util.concurrent.CountDownLatch(1)
                worker.execute {
                    try {
                        listener.onOpen()
                    } finally {
                        sent.countDown()
                    }
                }
                sent.await(5, TimeUnit.SECONDS)
                readLoop(sock, gen)
            } catch (error: Exception) {
                try {
                    opened?.close()
                } catch (_: Exception) {
                }
                if (gen == generation.get()) {
                    open.set(false)
                    worker.execute { listener.onFailure("failure " + error.javaClass.simpleName) }
                }
            }
        }.start()
    }

    fun send(frame: ByteArray) {
        lock.lock()
        try {
            val current = output
            if (current == null) {
                Log.i(CompanionService.TAG, "zola.companion send result=dropped")
                return
            }
            writeFrame(current, 0x1, frame)
            Log.i(CompanionService.TAG, "zola.companion send result=wrote bytes=" + frame.size)
        } catch (error: Exception) {
            Log.i(CompanionService.TAG, "zola.companion send result=failed error=" + error.javaClass.simpleName)
        } finally {
            lock.unlock()
        }
    }

    override fun close(reason: String) {
        generation.incrementAndGet()
        open.set(false)
        lock.lock()
        val current = socket
        output = null
        socket = null
        lock.unlock()
        try {
            current?.close()
        } catch (_: Exception) {
        }
    }

    override fun isOpen(): Boolean = open.get()

    private fun handshake(sock: Socket, host: String, port: Int, path: String) {
        val key = ByteArray(16)
        random.nextBytes(key)
        val encoded = Base64.getEncoder().encodeToString(key)
        val out = sock.getOutputStream()
        val request = "GET $path HTTP/1.1\r\n" +
            "Host: $host:$port\r\n" +
            "Upgrade: websocket\r\n" +
            "Connection: Upgrade\r\n" +
            "Sec-WebSocket-Key: $encoded\r\n" +
            "Sec-WebSocket-Version: 13\r\n\r\n"
        out.write(request.toByteArray(Charsets.US_ASCII))
        out.flush()
        val response = readHeaders(sock.getInputStream())
        val expected = Base64.getEncoder().encodeToString(
            MessageDigest.getInstance("SHA-1").digest(
                (encoded + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").toByteArray(Charsets.US_ASCII),
            ),
        )
        val accept = response.lineSequence().firstOrNull {
            it.startsWith("Sec-WebSocket-Accept:", ignoreCase = true)
        }?.substringAfter(":")?.trim()
        if (!response.startsWith("HTTP/1.1 101") || accept != expected) {
            throw java.io.IOException("upgrade")
        }
    }

    private fun readLoop(sock: Socket, gen: Int) {
        val input = sock.getInputStream()
        val text = ByteArrayOutputStream()
        try {
            while (gen == generation.get()) {
                val first = input.read()
                if (first < 0) break
                val second = input.read()
                if (second < 0) break
                val opcode = first and 0x0f
                val fin = first and 0x80 != 0
                val marker = second and 0x7f
                val length = when (marker) {
                    126 -> readExact(input, 2).let { ((it[0].toInt() and 0xff) shl 8) or (it[1].toInt() and 0xff) }
                    127 -> {
                        val wide = readExact(input, 8)
                        var value = 0L
                        wide.forEach { value = (value shl 8) or (it.toLong() and 0xff) }
                        if (value > Int.MAX_VALUE) throw java.io.IOException("large")
                        value.toInt()
                    }
                    else -> marker
                }
                val mask = if (second and 0x80 != 0) readExact(input, 4) else null
                val payload = readExact(input, length)
                if (mask != null) {
                    for (index in payload.indices) {
                        payload[index] = (payload[index].toInt() xor mask[index % 4].toInt()).toByte()
                    }
                }
                when (opcode) {
                    0x1, 0x2, 0x0 -> {
                        text.write(payload)
                        if (fin) {
                            val message = text.toString(Charsets.UTF_8)
                            text.reset()
                            worker.execute { if (gen == generation.get()) listener.onMessage(message) }
                        }
                    }
                    0x8 -> break
                    0x9 -> {
                        lock.lock()
                        try {
                            output?.let { writeFrame(it, 0xA, payload) }
                        } finally {
                            lock.unlock()
                        }
                    }
                }
            }
        } catch (_: Exception) {
        } finally {
            if (gen == generation.get()) {
                open.set(false)
                worker.execute { listener.onClosed("peer-closed") }
            }
        }
    }

    private fun writeFrame(out: OutputStream, opcode: Int, payload: ByteArray) {
        val header = ByteArrayOutputStream()
        header.write(0x80 or opcode)
        when {
            payload.size < 126 -> header.write(0x80 or payload.size)
            payload.size <= 65535 -> {
                header.write(0x80 or 126)
                header.write(payload.size shr 8)
                header.write(payload.size and 0xff)
            }
            else -> {
                header.write(0x80 or 127)
                var size = payload.size.toLong()
                val wide = ByteArray(8)
                for (index in 7 downTo 0) {
                    wide[index] = (size and 0xff).toByte()
                    size = size shr 8
                }
                header.write(wide)
            }
        }
        val mask = ByteArray(4)
        random.nextBytes(mask)
        header.write(mask)
        out.write(header.toByteArray())
        val masked = ByteArray(payload.size)
        for (index in payload.indices) {
            masked[index] = (payload[index].toInt() xor mask[index % 4].toInt()).toByte()
        }
        out.write(masked)
        out.flush()
    }

    private fun readHeaders(input: InputStream): String {
        val body = ByteArrayOutputStream()
        var seen = 0
        while (seen < 8192) {
            val next = input.read()
            if (next < 0) break
            body.write(next)
            seen += 1
            val text = body.toString(Charsets.US_ASCII)
            if (text.endsWith("\r\n\r\n")) return text
        }
        return body.toString(Charsets.US_ASCII)
    }

    private fun readExact(input: InputStream, count: Int): ByteArray {
        val bytes = ByteArray(count)
        var offset = 0
        while (offset < count) {
            val read = input.read(bytes, offset, count - offset)
            if (read < 0) throw java.io.IOException("closed")
            offset += read
        }
        return bytes
    }
}

private class ExactAlarms(private val service: Service) : AlarmPort {
    override fun schedule(atMs: Long) {
        val alarm = service.getSystemService(AlarmManager::class.java)
        val pending = PendingIntent.getBroadcast(
            service,
            CompanionService.NOTICE_ID,
            Intent(service, ReconnectReceiver::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        alarm.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, atMs, pending)
    }

    override fun askGrant() = Unit
}

private class PowerWakes(private val power: PowerManager) : WakePort {
    private val locks = linkedMapOf<String, PowerManager.WakeLock>()

    override fun acquire(tag: String, timeoutMs: Long) {
        val lock = locks.getOrPut(tag) { power.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, tag) }
        lock.acquire(timeoutMs)
    }

    override fun release(tag: String) {
        val lock = locks[tag] ?: return
        if (lock.isHeld) lock.release()
    }
}

private class KeystorePort(private val signer: KeystoreSigner) : SignerPort {
    override fun sign(payload: Map<String, Any?>): String? = try {
        signer.sign(payload)
    } catch (_: Exception) {
        null
    }

    override fun publicPem(): String = signer.publicPem()
}

open class FileStore(private val file: File) : EngineStore {
    private val install = File(file.parentFile, "install.json")

    override fun load(): String? = if (file.isFile) file.readText(Charsets.UTF_8) else null

    override fun readInstall(): String? = if (install.isFile) install.readText(Charsets.UTF_8) else null

    override fun writeInstall(body: String) {
        if (install.exists()) return
        replace(install, body)
    }

    override fun save(body: String) {
        replace(file, body)
    }

    private fun replace(target: File, body: String) {
        val tmp = File(target.parentFile, target.name + ".tmp")
        tmp.writeText(body, Charsets.UTF_8)
        val from = tmp.toPath()
        val to = target.toPath()
        try {
            Files.move(from, to, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING)
        } catch (_: AtomicMoveNotSupportedException) {
            Files.move(from, to, StandardCopyOption.REPLACE_EXISTING)
        }
    }
}
