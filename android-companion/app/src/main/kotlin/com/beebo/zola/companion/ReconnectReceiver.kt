package com.beebo.zola.companion

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

// P10-COMPANION: the exact alarm starts the service again; it is not a ping — P10-D07

class ReconnectReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (!context.isUserUnlockedCompat()) return
        val start = Intent(context, CompanionService::class.java).setAction(CompanionService.ACTION_RECONNECT)
        context.startForegroundService(start)
    }
}
