/**
 * SafePath AI - Zero-Data Emergency Mode
 * ========================================
 * Handles SOS alerts when the user has NO internet connection.
 * 
 * ONLINE:  Sends location to server API
 * OFFLINE: Uses SMS + tel: links to send distress messages via native handlers
 * 
 * Works in mobile browsers (Chrome/Safari) as a Progressive Web App feature.
 * For full hardware SMS/Call access, use the companion Android native module.
 */

class ZeroDataSOS {
    constructor(config = {}) {
        // Pre-saved emergency contacts (loaded from localStorage or defaults)
        this.emergencyContacts = config.contacts || this.loadContacts();
        
        // Pakistan emergency number
        this.emergencyServiceNumber = config.emergencyNumber || '1122';
        
        // Server API endpoint for online mode
        this.apiEndpoint = config.apiEndpoint || '/api/sos/trigger/';
        
        // CSRF token for Django
        this.csrfToken = this.getCookie('csrftoken');
        
        // Current location cache
        this.lastKnownLocation = null;
        
        // Bind network status listeners
        this._initNetworkMonitor();
        
        // Continuously cache GPS location for offline use
        this._initLocationCache();
        
        console.log('[ZeroDataSOS] Initialized. Contacts:', this.emergencyContacts.length);
    }

    // ================================================================
    // MAIN TRIGGER - Call this when SOS is activated
    // ================================================================
    
    async triggerSOS() {
        console.log('[ZeroDataSOS] SOS TRIGGERED');
        
        // Step 1: Get current location
        let location = null;
        try {
            location = await this.getCurrentLocation();
        } catch (err) {
            console.warn('[ZeroDataSOS] GPS failed, using last known:', err.message);
            location = this.lastKnownLocation;
        }

        // Step 2: Check connectivity and act accordingly
        if (this.isOnline()) {
            console.log('[ZeroDataSOS] ONLINE - Sending to server');
            const serverResult = await this.sendToServer(location);
            
            // Even if online, also send SMS as backup (belt + suspenders)
            if (location) {
                this.sendSMSAlerts(location);
            }
            return { mode: 'online', success: true, serverResult };
        } else {
            console.log('[ZeroDataSOS] OFFLINE - Zero Data Mode activated');
            return this.handleOfflineEmergency(location);
        }
    }

    // ================================================================
    // OFFLINE HANDLER - SMS + Emergency Call (No internet required)
    // ================================================================
    
    handleOfflineEmergency(location) {
        const results = { mode: 'offline', sms: false, call: false };

        if (!location) {
            // Last resort: send SOS without coordinates
            this.sendSMSAlerts(null);
            this.triggerEmergencyCall();
            results.sms = true;
            results.call = true;
            results.note = 'Location unavailable - sent alert without coordinates';
            return results;
        }

        // Send SMS to all emergency contacts
        results.sms = this.sendSMSAlerts(location);
        
        // Trigger emergency call to 1122
        results.call = this.triggerEmergencyCall();
        
        // Vibrate to confirm (3 short bursts)
        this.confirmVibration();
        
        return results;
    }

    // ================================================================
    // NETWORK CHECK
    // ================================================================
    
    isOnline() {
        return navigator.onLine;
    }

    _initNetworkMonitor() {
        window.addEventListener('online', () => {
            console.log('[ZeroDataSOS] Network restored - syncing pending alerts');
            this.syncPendingAlerts();
        });
        window.addEventListener('offline', () => {
            console.log('[ZeroDataSOS] Network LOST - Zero Data Mode ready');
        });
    }

    // ================================================================
    // GPS LOCATION
    // ================================================================
    
    getCurrentLocation() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Geolocation not supported by this browser'));
                return;
            }

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const loc = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude,
                        accuracy: position.coords.accuracy,
                        timestamp: Date.now()
                    };
                    // Cache for offline use
                    this.lastKnownLocation = loc;
                    localStorage.setItem('safepath_last_location', JSON.stringify(loc));
                    resolve(loc);
                },
                (error) => {
                    // Try to use cached location
                    const cached = localStorage.getItem('safepath_last_location');
                    if (cached) {
                        const loc = JSON.parse(cached);
                        console.warn('[ZeroDataSOS] Using cached location from', new Date(loc.timestamp));
                        resolve(loc);
                    } else {
                        reject(new Error(this._getGPSErrorMessage(error)));
                    }
                },
                {
                    enableHighAccuracy: true,   // Use GPS hardware, not cell towers
                    timeout: 10000,             // 10 second timeout
                    maximumAge: 60000           // Accept 1-minute old cache
                }
            );
        });
    }

    _initLocationCache() {
        // Periodically cache location for offline availability
        if (navigator.geolocation) {
            // Cache immediately
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    this.lastKnownLocation = {
                        lat: pos.coords.latitude,
                        lng: pos.coords.longitude,
                        accuracy: pos.coords.accuracy,
                        timestamp: Date.now()
                    };
                    localStorage.setItem('safepath_last_location', JSON.stringify(this.lastKnownLocation));
                },
                () => {} // Silent fail for background caching
            );
            
            // Update every 30 seconds
            setInterval(() => {
                navigator.geolocation.getCurrentPosition(
                    (pos) => {
                        this.lastKnownLocation = {
                            lat: pos.coords.latitude,
                            lng: pos.coords.longitude,
                            accuracy: pos.coords.accuracy,
                            timestamp: Date.now()
                        };
                        localStorage.setItem('safepath_last_location', JSON.stringify(this.lastKnownLocation));
                    },
                    () => {}
                );
            }, 30000);
        }
    }

    _getGPSErrorMessage(error) {
        switch (error.code) {
            case error.PERMISSION_DENIED:
                return 'GPS permission denied. Please enable location access.';
            case error.POSITION_UNAVAILABLE:
                return 'GPS position unavailable. Please ensure GPS is enabled.';
            case error.TIMEOUT:
                return 'GPS request timed out. Move to open area for better signal.';
            default:
                return 'Unknown GPS error.';
        }
    }

    // ================================================================
    // SMS SENDING (Works offline - uses native SMS handler)
    // ================================================================
    
    sendSMSAlerts(location) {
        if (this.emergencyContacts.length === 0) {
            console.warn('[ZeroDataSOS] No emergency contacts configured');
            return false;
        }

        // Format the distress message
        const message = this.formatDistressMessage(location);
        
        // Method 1: Use sms: URI scheme (opens native SMS app with pre-filled message)
        // This works on ALL mobile browsers without any permissions
        const numbers = this.emergencyContacts.map(c => c.phone).join(',');
        const smsURI = `sms:${numbers}?body=${encodeURIComponent(message)}`;
        
        // Open SMS app with pre-filled emergency message
        window.location.href = smsURI;
        
        // Store alert in localStorage for sync when back online
        this.storePendingAlert(location, message);
        
        console.log('[ZeroDataSOS] SMS drafted for:', this.emergencyContacts.length, 'contacts');
        return true;
    }

    formatDistressMessage(location) {
        let message = '🚨 EMERGENCY SOS - SafePath AI\n\n';
        message += 'I need help immediately!\n\n';
        
        if (location) {
            const mapsUrl = `https://www.google.com/maps?q=${location.lat},${location.lng}`;
            message += `📍 My Location:\n${mapsUrl}\n\n`;
            message += `Coordinates: ${location.lat.toFixed(6)}, ${location.lng.toFixed(6)}\n`;
            message += `Accuracy: ±${Math.round(location.accuracy || 0)}m\n\n`;
        } else {
            message += '📍 Location: UNAVAILABLE (GPS disabled)\n\n';
        }
        
        message += `⏰ Time: ${new Date().toLocaleString()}\n`;
        message += '🆘 Please call me or send help!\n';
        message += '📞 Emergency: 1122 (Rescue) | 15 (Police)';
        
        return message;
    }

    // ================================================================
    // EMERGENCY CALL (Works offline - uses tel: URI)
    // ================================================================
    
    triggerEmergencyCall() {
        // tel: URI triggers native phone dialer - works without internet
        const telURI = `tel:${this.emergencyServiceNumber}`;
        
        // Small delay to allow SMS to be sent first
        setTimeout(() => {
            window.location.href = telURI;
        }, 2000);
        
        console.log('[ZeroDataSOS] Emergency call initiated to:', this.emergencyServiceNumber);
        return true;
    }

    // ================================================================
    // ONLINE MODE - Server API
    // ================================================================
    
    async sendToServer(location) {
        if (!location) return { success: false, error: 'No location' };
        
        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken,
                },
                body: JSON.stringify({
                    latitude: location.lat,
                    longitude: location.lng,
                    message: 'SOS Emergency triggered via Zero-Data module',
                    accuracy: location.accuracy,
                }),
            });
            
            if (response.ok) {
                const data = await response.json();
                return { success: true, data };
            } else {
                throw new Error(`Server responded ${response.status}`);
            }
        } catch (error) {
            console.error('[ZeroDataSOS] Server send failed:', error.message);
            // Fallback to offline mode
            this.handleOfflineEmergency(location);
            return { success: false, error: error.message };
        }
    }

    // ================================================================
    // PENDING ALERTS (Sync when back online)
    // ================================================================
    
    storePendingAlert(location, message) {
        const pending = JSON.parse(localStorage.getItem('safepath_pending_alerts') || '[]');
        pending.push({
            location,
            message,
            timestamp: Date.now(),
            synced: false,
        });
        localStorage.setItem('safepath_pending_alerts', JSON.stringify(pending));
    }

    async syncPendingAlerts() {
        const pending = JSON.parse(localStorage.getItem('safepath_pending_alerts') || '[]');
        const unsynced = pending.filter(a => !a.synced);
        
        if (unsynced.length === 0) return;
        
        console.log('[ZeroDataSOS] Syncing', unsynced.length, 'pending alerts');
        
        for (const alert of unsynced) {
            try {
                await this.sendToServer(alert.location);
                alert.synced = true;
            } catch (e) {
                console.warn('[ZeroDataSOS] Sync failed for alert:', e.message);
            }
        }
        
        localStorage.setItem('safepath_pending_alerts', JSON.stringify(pending));
    }

    // ================================================================
    // CONTACT MANAGEMENT
    // ================================================================
    
    loadContacts() {
        const stored = localStorage.getItem('safepath_emergency_contacts');
        if (stored) return JSON.parse(stored);
        // Default fallback
        return [];
    }

    setContacts(contacts) {
        // contacts = [{name: 'Ammi', phone: '+923001234567'}, ...]
        this.emergencyContacts = contacts;
        localStorage.setItem('safepath_emergency_contacts', JSON.stringify(contacts));
    }

    addContact(name, phone) {
        this.emergencyContacts.push({ name, phone });
        localStorage.setItem('safepath_emergency_contacts', JSON.stringify(this.emergencyContacts));
    }

    // ================================================================
    // UTILITIES
    // ================================================================
    
    confirmVibration() {
        if (navigator.vibrate) {
            navigator.vibrate([200, 100, 200, 100, 200]);
        }
    }

    getCookie(name) {
        let value = null;
        if (document.cookie) {
            document.cookie.split(';').forEach(c => {
                c = c.trim();
                if (c.startsWith(name + '=')) {
                    value = decodeURIComponent(c.substring(name.length + 1));
                }
            });
        }
        return value;
    }
}


// ================================================================
// AUTO-INITIALIZE when script loads
// ================================================================

let safepathSOS = null;

document.addEventListener('DOMContentLoaded', () => {
    // Load contacts from the server-rendered page or localStorage
    safepathSOS = new ZeroDataSOS();
    
    // Expose globally for button onclick handlers
    window.safepathSOS = safepathSOS;
    
    console.log('[ZeroDataSOS] Ready. Online:', navigator.onLine);
});


/**
 * USAGE IN HTML:
 * 
 * <button onclick="window.safepathSOS.triggerSOS()">SOS EMERGENCY</button>
 * 
 * Or with contacts pre-loaded:
 * 
 * <script>
 *   safepathSOS = new ZeroDataSOS({
 *     contacts: [
 *       {name: 'Ammi', phone: '+923001234567'},
 *       {name: 'Abu', phone: '+923219876543'},
 *     ],
 *     emergencyNumber: '1122',
 *   });
 * </script>
 */
