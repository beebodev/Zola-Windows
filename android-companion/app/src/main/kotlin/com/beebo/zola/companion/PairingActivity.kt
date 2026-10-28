package com.beebo.zola.companion

import android.Manifest
import android.app.AlarmManager
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.text.InputType
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import org.json.JSONObject
import java.io.File

// P10-COMPANION: the screen asks, and the code stays in this process — Phase 5

class PairingActivity : AppCompatActivity() {
    private lateinit var address: EditText
    private lateinit var code: EditText
    private lateinit var status: TextView
    private var submitted = false
    private var handed = false
    private val refresh = object : Runnable {
        override fun run() {
            render()
            status.postDelayed(this, 500)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        address = EditText(this)
        address.hint = "PC address"
        address.imeOptions = EditorInfo.IME_ACTION_NEXT
        address.setText(savedAddress())
        val codeField = EditText(this)
        code = codeField
        code.hint = "Pairing code"
        code.inputType = InputType.TYPE_CLASS_NUMBER
        code.imeOptions = EditorInfo.IME_ACTION_DONE
        status = TextView(this)
        val pair = Button(this)
        pair.text = "Pair"
        pair.isAllCaps = false
        val battery = Button(this)
        battery.text = "Battery"
        val alarms = Button(this)
        alarms.text = "Alarms & reminders"
        battery.setOnClickListener {
            val power = getSystemService(android.os.PowerManager::class.java)
            if (!power.isIgnoringBatteryOptimizations(packageName)) {
                startActivity(
                    Intent(
                        Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
                        Uri.parse("package:$packageName"),
                    ),
                )
            }
        }
        alarms.setOnClickListener {
            val grant = Setup.exactAlarmIntent(packageName)
            startActivity(Intent(grant.action, Uri.parse(grant.data)))
        }
        val submit = {
            val host = address.text?.toString()?.trim().orEmpty()
            val typed = code.text?.toString()?.filter { it in '0'..'9' }.orEmpty()
            if (host.isEmpty()) {
                status.text = "Enter the PC address"
            } else if (typed.length != 8) {
                status.text = "Enter all 8 digits"
            } else {
                Handoff.address = host
                Handoff.code = typed
                submitted = true
                handed = true
                status.text = "Pairing"
                getSystemService(InputMethodManager::class.java).hideSoftInputFromWindow(code.windowToken, 0)
                startForegroundService(Intent(this, CompanionService::class.java))
            }
        }
        pair.setOnClickListener { submit() }
        code.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_DONE) submit()
            actionId == EditorInfo.IME_ACTION_DONE
        }
        val column = LinearLayout(this)
        column.orientation = LinearLayout.VERTICAL
        column.addView(status)
        column.addView(address)
        column.addView(code)
        column.addView(pair)
        column.addView(battery)
        column.addView(alarms)
        val scroll = ScrollView(this)
        scroll.addView(column)
        setContentView(scroll)
        requestPermissions(arrayOf(Manifest.permission.READ_SMS, Manifest.permission.POST_NOTIFICATIONS), 41)
    }

    override fun onResume() {
        super.onResume()
        status.removeCallbacks(refresh)
        status.post(refresh)
    }

    override fun onPause() {
        status.removeCallbacks(refresh)
        super.onPause()
    }

    private fun render() {
        if (Setup.clearTypedCode(handed, CompanionStatus.paired, code.text?.isNotEmpty() == true)) {
            code.setText("")
            handed = false
        }
        val notice = if (submitted && CompanionStatus.state == "stopped") "Pairing" else Setup.notice(CompanionStatus.state)
        if (CompanionStatus.state != "stopped") submitted = false
        val sms = checkSelfPermission(Manifest.permission.READ_SMS) == PackageManager.PERMISSION_GRANTED
        val notifications = checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED
        val exact = getSystemService(AlarmManager::class.java).canScheduleExactAlarms()
        val missing = Setup.prompts(sms, notifications, exact)
        status.text = listOf(notice, missing.joinToString(", ")).filter { it.isNotEmpty() }.joinToString("\n")
    }

    private fun savedAddress(): String {
        if (CompanionStatus.address.isNotEmpty()) return CompanionStatus.address
        val file = File(filesDir, "companion-state.json")
        if (!file.isFile) return ""
        return try {
            JSONObject(file.readText()).optString("address")
        } catch (_: Exception) {
            ""
        }
    }
}
