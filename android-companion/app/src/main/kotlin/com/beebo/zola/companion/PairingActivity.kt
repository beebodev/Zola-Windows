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
import android.widget.CheckBox
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
    private val launchPackages = mutableListOf<String>()
    private lateinit var visibleList: LinearLayout
    private lateinit var hiddenList: LinearLayout
    private lateinit var neverList: LinearLayout
    private lateinit var noticeLine: TextView
    private var drawingAllowlist = false
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
        column.addView(notificationSection())
        val scroll = ScrollView(this)
        scroll.addView(column)
        setContentView(scroll)
        requestPermissions(arrayOf(Manifest.permission.READ_SMS, Manifest.permission.POST_NOTIFICATIONS), 41)
    }

    override fun onResume() {
        super.onResume()
        showAllowlist(currentAllowlist())
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

    private fun notificationSection(): LinearLayout {
        val box = LinearLayout(this)
        box.orientation = LinearLayout.VERTICAL
        val access = Button(this)
        access.text = "Notification access"
        access.isAllCaps = false
        access.setOnClickListener {
            val name = android.content.ComponentName(this, NotificationListener::class.java).flattenToString()
            val detail = Intent(Settings.ACTION_NOTIFICATION_LISTENER_DETAIL_SETTINGS)
            detail.putExtra(Settings.EXTRA_NOTIFICATION_LISTENER_COMPONENT_NAME, name)
            try {
                startActivity(detail)
            } catch (_: Exception) {
                startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
            }
        }
        noticeLine = TextView(this)
        noticeLine.text = noticeSummary()
        box.addView(access)
        box.addView(noticeLine)
        visibleList = section(box, "Zola can see")
        hiddenList = section(box, "Not shared")
        neverList = section(box, "Never shared")
        val launch = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
        launchPackages.clear()
        launchPackages.addAll(
            packageManager.queryIntentActivities(launch, 0)
                .map { it.activityInfo.packageName }
                .distinct()
                .filter { it != packageName }
                .sorted(),
        )
        showAllowlist(currentAllowlist())
        return box
    }

    private fun section(box: LinearLayout, title: String): LinearLayout {
        val heading = TextView(this)
        heading.text = title
        val list = LinearLayout(this)
        list.orientation = LinearLayout.VERTICAL
        box.addView(heading)
        box.addView(list)
        return list
    }

    private fun showAllowlist(stored: Set<String>) {
        drawingAllowlist = true
        try {
            visibleList.removeAllViews()
            hiddenList.removeAllViews()
            neverList.removeAllViews()
            val apps = launchPackages.map { it to appLabel(it) }
            val lists = AllowlistRows.lists(apps, stored)
            fill(visibleList, lists.visible, stored)
            fill(hiddenList, lists.hidden, stored)
            fill(neverList, lists.never, stored)
        } finally {
            drawingAllowlist = false
        }
    }

    private fun fill(box: LinearLayout, rows: List<AllowlistRow>, stored: Set<String>) {
        for (row in rows) {
            val check = CheckBox(this)
            check.text = if (row.reason.isEmpty()) row.label else row.label + "\n" + row.reason
            check.isAllCaps = false
            check.isEnabled = row.enabled
            check.isChecked = row.checked
            check.setOnCheckedChangeListener { _, checked ->
                if (drawingAllowlist || !row.enabled || checked == row.checked) return@setOnCheckedChangeListener
                val now = AllowlistRows.toggle(stored, row.pkg)
                showAllowlist(now)
                startForegroundService(Intent(this, CompanionService::class.java))
                CompanionBridge.submit { engine -> engine.setAllowlist(now) }
                noticeLine.text = noticeSummary()
            }
            box.addView(check)
        }
    }

    private fun appLabel(pkg: String): String {
        return try {
            packageManager.getApplicationLabel(packageManager.getApplicationInfo(pkg, 0)).toString()
        } catch (_: Exception) {
            "Messages"
        }
    }

    private fun currentAllowlist(): Set<String> {
        val file = File(filesDir, "notification-queue.json")
        if (!file.isFile) return emptySet()
        return try {
            val array = JSONObject(file.readText()).optJSONArray("allowlist") ?: return emptySet()
            (0 until array.length()).map { array.getString(it) }.toSet()
        } catch (_: Exception) {
            emptySet()
        }
    }

    private fun noticeSummary(): String {
        val file = File(filesDir, "notification-queue.json")
        if (!file.isFile) return "Notifications off"
        return try {
            val root = JSONObject(file.readText())
            val depth = root.optJSONArray("items")?.length() ?: 0
            val bound = root.optInt("listener_bound")
            val granted = root.optInt("listener_permission")
            "listener " + granted + "/" + bound + " queue " + depth + " filtered " + root.optInt("notification_filtered")
        } catch (_: Exception) {
            "Notifications off"
        }
    }
}
