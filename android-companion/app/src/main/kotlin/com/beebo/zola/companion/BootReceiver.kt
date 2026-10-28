package com.beebo.zola.companion

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

// P10-COMPANION: the service starts after unlock, not before — P10-D07

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action ?: return
        if (action != Intent.ACTION_BOOT_COMPLETED && action != Intent.ACTION_MY_PACKAGE_REPLACED) return
        if (!context.isUserUnlockedCompat()) return
        context.startForegroundService(Intent(context, CompanionService::class.java))
    }
}

internal fun Context.isUserUnlockedCompat(): Boolean {
    val manager = getSystemService(android.os.UserManager::class.java)
    return manager.isUserUnlocked
}
