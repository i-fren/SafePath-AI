/**
 * SafePath AI - Zero-Data Emergency Module (Native Android)
 * ==========================================================
 * 
 * Full hardware-level access for:
 * - GPS location (even without Google Play Services)
 * - Direct SMS sending (no user interaction required)
 * - Emergency call dialing
 * 
 * Required Permissions (AndroidManifest.xml):
 *   <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
 *   <uses-permission android:name="android.permission.SEND_SMS" />
 *   <uses-permission android:name="android.permission.CALL_PHONE" />
 *   <uses-permission android:name="android.permission.READ_PHONE_STATE" />
 *   <uses-permission android:name="android.permission.INTERNET" />
 *   <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
 * 
 * Integration: Call ZeroDataEmergency.triggerSOS(context) from any Activity/Fragment
 */

package com.safepath.ai.emergency

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Vibrator
import android.telephony.SmsManager
import android.util.Log
import androidx.core.content.ContextCompat
import java.text.SimpleDateFormat
import java.util.*

/**
 * Main Zero-Data Emergency Handler
 * 
 * Handles SOS alerts with or without internet connectivity.
 * When offline: uses hardware GPS + native SMS + direct call.
 */
object ZeroDataEmergency {

    private const val TAG = "ZeroDataSOS"
    
    // Pakistan emergency service
    private const val EMERGENCY_NUMBER = "1122"
    
    // Pre-saved emergency contacts
    // In production, load from SharedPreferences or local database
    private val emergencyContacts = mutableListOf<EmergencyContact>()

    data class EmergencyContact(val name: String, val phone: String)
    data class SOSResult(
        val mode: String,          // "online" or "offline"
        val locationFound: Boolean,
        val smsSent: Boolean,
        val callInitiated: Boolean,
        val latitude: Double?,
        val longitude: Double?,
        val error: String?
    )

    // ================================================================
    // MAIN ENTRY POINT
    // ================================================================

    /**
     * Trigger SOS Emergency.
     * Automatically detects network status and acts accordingly.
     * 
     * @param context Android Context (Activity or Application)
     * @return SOSResult with details of actions taken
     */
    fun triggerSOS(context: Context): SOSResult {
        Log.w(TAG, "=== SOS TRIGGERED ===")
        
        // Step 1: Get GPS location
        val location = getLocation(context)
        
        // Step 2: Check connectivity
        return if (isOnline(context)) {
            Log.i(TAG, "ONLINE mode - sending to server + SMS backup")
            handleOnline(context, location)
        } else {
            Log.w(TAG, "OFFLINE mode - Zero Data Emergency")
            handleOffline(context, location)
        }
    }

    // ================================================================
    // OFFLINE HANDLER
    // ================================================================

    private fun handleOffline(context: Context, location: Location?): SOSResult {
        var smsSent = false
        var callInitiated = false

        // Send SMS to all emergency contacts
        smsSent = sendDistressSMS(context, location)
        
        // Trigger emergency call
        callInitiated = makeEmergencyCall(context)
        
        // Vibration confirmation (3 bursts)
        vibrateConfirmation(context)
        
        // Store for later sync
        storePendingAlert(context, location)

        return SOSResult(
            mode = "offline",
            locationFound = location != null,
            smsSent = smsSent,
            callInitiated = callInitiated,
            latitude = location?.latitude,
            longitude = location?.longitude,
            error = if (location == null) "GPS unavailable" else null
        )
    }

    // ================================================================
    // ONLINE HANDLER
    // ================================================================

    private fun handleOnline(context: Context, location: Location?): SOSResult {
        // Send to server API
        sendToServerAPI(context, location)
        
        // Also send SMS as backup
        val smsSent = sendDistressSMS(context, location)
        
        return SOSResult(
            mode = "online",
            locationFound = location != null,
            smsSent = smsSent,
            callInitiated = false,
            latitude = location?.latitude,
            longitude = location?.longitude,
            error = null
        )
    }

    // ================================================================
    // GPS LOCATION (Hardware-level, no internet needed)
    // ================================================================

    @SuppressLint("MissingPermission")
    private fun getLocation(context: Context): Location? {
        // Check permission
        if (!hasPermission(context, Manifest.permission.ACCESS_FINE_LOCATION)) {
            Log.e(TAG, "GPS permission not granted!")
            return getCachedLocation(context)
        }

        val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager

        // Check if GPS is enabled
        if (!locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER) &&
            !locationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)) {
            Log.e(TAG, "GPS is disabled! Using cached location.")
            return getCachedLocation(context)
        }

        // Try GPS provider first (most accurate, works offline)
        var location = locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER)
        
        // Fallback to network provider
        if (location == null) {
            location = locationManager.getLastKnownLocation(LocationManager.NETWORK_PROVIDER)
        }
        
        // Fallback to passive provider
        if (location == null) {
            location = locationManager.getLastKnownLocation(LocationManager.PASSIVE_PROVIDER)
        }

        // Cache for future use
        if (location != null) {
            cacheLocation(context, location)
        } else {
            // Try cached location as last resort
            location = getCachedLocation(context)
        }

        if (location != null) {
            Log.i(TAG, "Location found: ${location.latitude}, ${location.longitude} (accuracy: ${location.accuracy}m)")
        } else {
            Log.e(TAG, "No location available from any source!")
        }

        return location
    }

    private fun cacheLocation(context: Context, location: Location) {
        val prefs = context.getSharedPreferences("safepath_sos", Context.MODE_PRIVATE)
        prefs.edit()
            .putFloat("cached_lat", location.latitude.toFloat())
            .putFloat("cached_lng", location.longitude.toFloat())
            .putLong("cached_time", System.currentTimeMillis())
            .apply()
    }

    private fun getCachedLocation(context: Context): Location? {
        val prefs = context.getSharedPreferences("safepath_sos", Context.MODE_PRIVATE)
        val lat = prefs.getFloat("cached_lat", 0f)
        val lng = prefs.getFloat("cached_lng", 0f)
        
        if (lat == 0f && lng == 0f) return null
        
        val location = Location("cached")
        location.latitude = lat.toDouble()
        location.longitude = lng.toDouble()
        return location
    }

    // ================================================================
    // SMS SENDING (Direct hardware SMS - no internet needed)
    // ================================================================

    @SuppressLint("MissingPermission")
    private fun sendDistressSMS(context: Context, location: Location?): Boolean {
        if (!hasPermission(context, Manifest.permission.SEND_SMS)) {
            Log.e(TAG, "SMS permission not granted!")
            return false
        }

        if (emergencyContacts.isEmpty()) {
            Log.w(TAG, "No emergency contacts configured!")
            // Load from SharedPreferences
            loadContacts(context)
            if (emergencyContacts.isEmpty()) return false
        }

        val message = formatDistressMessage(location)
        val smsManager = SmsManager.getDefault()

        var allSent = true
        for (contact in emergencyContacts) {
            try {
                // Split message if too long (SMS limit is 160 chars)
                val parts = smsManager.divideMessage(message)
                smsManager.sendMultipartTextMessage(
                    contact.phone,  // Destination number
                    null,           // Service center (null = default)
                    parts,          // Message parts
                    null,           // Sent intents
                    null            // Delivery intents
                )
                Log.i(TAG, "SMS sent to ${contact.name} (${contact.phone})")
            } catch (e: Exception) {
                Log.e(TAG, "SMS failed for ${contact.name}: ${e.message}")
                allSent = false
            }
        }

        return allSent
    }

    private fun formatDistressMessage(location: Location?): String {
        val sb = StringBuilder()
        sb.append("🚨 SOS EMERGENCY - SafePath AI\n")
        sb.append("I NEED HELP IMMEDIATELY!\n\n")
        
        if (location != null) {
            val mapsUrl = "https://www.google.com/maps?q=${location.latitude},${location.longitude}"
            sb.append("📍 My Location:\n$mapsUrl\n\n")
            sb.append("GPS: ${String.format("%.6f", location.latitude)}, ${String.format("%.6f", location.longitude)}\n")
            sb.append("Accuracy: ±${location.accuracy.toInt()}m\n\n")
        } else {
            sb.append("📍 Location: UNAVAILABLE\n\n")
        }
        
        val timeFormat = SimpleDateFormat("dd/MM/yyyy HH:mm:ss", Locale.getDefault())
        sb.append("⏰ ${timeFormat.format(Date())}\n")
        sb.append("📞 Emergency: 1122 | Police: 15")
        
        return sb.toString()
    }

    // ================================================================
    // EMERGENCY CALL (Direct hardware dial)
    // ================================================================

    private fun makeEmergencyCall(context: Context): Boolean {
        if (!hasPermission(context, Manifest.permission.CALL_PHONE)) {
            // Fallback: open dialer with number pre-filled (no permission needed)
            val intent = Intent(Intent.ACTION_DIAL).apply {
                data = Uri.parse("tel:$EMERGENCY_NUMBER")
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(intent)
            Log.i(TAG, "Opened dialer with $EMERGENCY_NUMBER (CALL_PHONE permission missing)")
            return true
        }

        try {
            // Direct call - no user interaction needed
            val intent = Intent(Intent.ACTION_CALL).apply {
                data = Uri.parse("tel:$EMERGENCY_NUMBER")
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(intent)
            Log.i(TAG, "Emergency call initiated to $EMERGENCY_NUMBER")
            return true
        } catch (e: Exception) {
            Log.e(TAG, "Emergency call failed: ${e.message}")
            return false
        }
    }

    // ================================================================
    // NETWORK CHECK
    // ================================================================

    private fun isOnline(context: Context): Boolean {
        val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val network = cm.activeNetwork ?: return false
            val capabilities = cm.getNetworkCapabilities(network) ?: return false
            return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) &&
                   capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
        } else {
            @Suppress("DEPRECATION")
            val networkInfo = cm.activeNetworkInfo
            return networkInfo?.isConnected == true
        }
    }

    // ================================================================
    // CONTACT MANAGEMENT
    // ================================================================

    fun setContacts(contacts: List<EmergencyContact>) {
        emergencyContacts.clear()
        emergencyContacts.addAll(contacts)
    }

    fun addContact(name: String, phone: String) {
        emergencyContacts.add(EmergencyContact(name, phone))
    }

    private fun loadContacts(context: Context) {
        val prefs = context.getSharedPreferences("safepath_sos", Context.MODE_PRIVATE)
        val contactsJson = prefs.getString("emergency_contacts", null) ?: return
        
        // Simple parsing (in production use Gson/Moshi)
        try {
            val contacts = contactsJson.split("|")
            for (entry in contacts) {
                val parts = entry.split(",")
                if (parts.size == 2) {
                    emergencyContacts.add(EmergencyContact(parts[0], parts[1]))
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to load contacts: ${e.message}")
        }
    }

    fun saveContacts(context: Context) {
        val prefs = context.getSharedPreferences("safepath_sos", Context.MODE_PRIVATE)
        val serialized = emergencyContacts.joinToString("|") { "${it.name},${it.phone}" }
        prefs.edit().putString("emergency_contacts", serialized).apply()
    }

    // ================================================================
    // PENDING ALERTS (Sync when back online)
    // ================================================================

    private fun storePendingAlert(context: Context, location: Location?) {
        val prefs = context.getSharedPreferences("safepath_sos", Context.MODE_PRIVATE)
        val existing = prefs.getString("pending_alerts", "") ?: ""
        val entry = "${System.currentTimeMillis()},${location?.latitude ?: 0},${location?.longitude ?: 0}"
        prefs.edit().putString("pending_alerts", "$existing|$entry").apply()
    }

    private fun sendToServerAPI(context: Context, location: Location?) {
        // In production, use Retrofit/OkHttp to POST to your Django API
        // For hackathon, this is handled by the web layer
        Log.i(TAG, "Would send to server: lat=${location?.latitude}, lng=${location?.longitude}")
    }

    // ================================================================
    // UTILITIES
    // ================================================================

    private fun hasPermission(context: Context, permission: String): Boolean {
        return ContextCompat.checkSelfPermission(context, permission) == PackageManager.PERMISSION_GRANTED
    }

    @Suppress("DEPRECATION")
    private fun vibrateConfirmation(context: Context) {
        val vibrator = context.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
        vibrator?.let {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                it.vibrate(android.os.VibrationEffect.createWaveform(
                    longArrayOf(0, 200, 100, 200, 100, 200), -1
                ))
            } else {
                it.vibrate(longArrayOf(0, 200, 100, 200, 100, 200), -1)
            }
        }
    }
}


/**
 * USAGE EXAMPLE:
 * 
 * // In your Activity or Fragment:
 * 
 * // 1. Set up contacts (do this once, e.g., in settings)
 * ZeroDataEmergency.setContacts(listOf(
 *     ZeroDataEmergency.EmergencyContact("Ammi", "+923001234567"),
 *     ZeroDataEmergency.EmergencyContact("Abu", "+923219876543"),
 *     ZeroDataEmergency.EmergencyContact("Bhai", "+923331234567"),
 * ))
 * ZeroDataEmergency.saveContacts(this)
 * 
 * // 2. Trigger SOS (from button click, shake, or voice command)
 * val result = ZeroDataEmergency.triggerSOS(this)
 * 
 * // 3. Check result
 * if (result.smsSent) {
 *     // SMS was sent to all contacts
 * }
 * if (result.mode == "offline") {
 *     // Was handled without internet
 * }
 */
