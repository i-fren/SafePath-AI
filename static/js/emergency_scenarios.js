/**
 * SafePath AI - Emergency Scenarios Handler
 * ==========================================
 * 
 * Scenario A: Signal Lost → Dead-man's timer + SMS fallback
 * Scenario B: Kidnapping → Panic gesture + stealth lock + pre-shutdown alert
 * 
 * Works alongside zero_data_sos.js for offline SMS/call capabilities.
 */

class EmergencyScenarios {
    constructor() {
        // Config
        this.DEAD_MAN_TIMER_MS = 10 * 60 * 1000; // 10 minutes
        this.SIGNAL_CHECK_INTERVAL = 15000;        // Check signal every 15s
        this.PANIC_BUTTON_COUNT = 5;               // 5 rapid presses
        this.PANIC_WINDOW_MS = 3000;               // Within 3 seconds

        // State
        this.isJourneyActive = false;
        this.lastKnownLocation = null;
        this.signalLost = false;
        this.deadManTimer = null;
        this.signalCheckInterval = null;
        this.panicPressCount = 0;
        this.panicTimer = null;
        this.stealthLocked = false;
        this.journeyTrackingId = null;

        // Initialize
        this._initPanicGesture();
        this._initSignalMonitor();
        this._initShutdownDetector();
        this._initLocationCache();

        console.log('[EmergencyScenarios] Initialized');
    }

    // ================================================================
    // SCENARIO A: SIGNAL LOST
    // ================================================================

    /**
     * Call this when a journey starts to enable signal monitoring.
     */
    startJourneyMonitoring(trackingId) {
        this.isJourneyActive = true;
        this.journeyTrackingId = trackingId;
        this.signalLost = false;
        this._startSignalChecks();
        console.log('[Signal] Journey monitoring started:', trackingId);
    }

    stopJourneyMonitoring() {
        this.isJourneyActive = false;
        this._stopSignalChecks();
        this._clearDeadManTimer();
        console.log('[Signal] Journey monitoring stopped');
    }

    _initSignalMonitor() {
        // Listen for online/offline events
        window.addEventListener('offline', () => this._handleSignalLost());
        window.addEventListener('online', () => this._handleSignalRestored());
    }

    _startSignalChecks() {
        this.signalCheckInterval = setInterval(() => {
            if (!navigator.onLine && this.isJourneyActive && !this.signalLost) {
                this._handleSignalLost();
            }
        }, this.SIGNAL_CHECK_INTERVAL);
    }

    _stopSignalChecks() {
        if (this.signalCheckInterval) {
            clearInterval(this.signalCheckInterval);
            this.signalCheckInterval = null;
        }
    }

    _handleSignalLost() {
        if (!this.isJourneyActive || this.signalLost) return;
        this.signalLost = true;

        console.warn('[Signal] SIGNAL LOST during active journey!');

        // Get last known location
        const location = this._getCachedLocation();

        // Send immediate SMS alert
        this._sendSignalLostSMS(location);

        // Start dead-man's timer (repeat alert every 10 min)
        this._startDeadManTimer(location);

        // Show UI notification
        this._showSignalLostUI();
    }

    _handleSignalRestored() {
        if (!this.signalLost) return;
        this.signalLost = false;

        console.log('[Signal] Signal restored!');
        this._clearDeadManTimer();

        // Sync with server
        this._syncSignalRestoredWithServer();

        // Hide UI
        this._hideSignalLostUI();
    }

    _sendSignalLostSMS(location) {
        const timestamp = new Date().toLocaleString();
        let message = `⚠️ SafePath ALERT: Signal lost during journey!\n\n`;

        if (location) {
            message += `📍 Last known location:\nhttps://www.google.com/maps?q=${location.lat},${location.lng}\n\n`;
            message += `GPS: ${location.lat.toFixed(6)}, ${location.lng.toFixed(6)}\n`;
        } else {
            message += `📍 Location: Unavailable\n`;
        }

        message += `⏰ Time: ${timestamp}\n`;
        if (this.journeyTrackingId) {
            message += `🆔 Journey: ${this.journeyTrackingId}\n`;
        }
        message += `\n🚨 If I don't reconnect in 10 min, please check on me.\n`;
        message += `📞 Emergency: 15 (Police) | 1122 (Rescue)`;

        // Use SMS URI to send
        this._triggerSMS(message);
    }

    _startDeadManTimer(location) {
        this._clearDeadManTimer();
        this.deadManTimer = setInterval(() => {
            if (this.signalLost && this.isJourneyActive) {
                console.warn('[DeadMan] Timer expired - repeating alert');
                this._sendSignalLostSMS(location);
                // Vibrate to notify user their alert was re-sent
                if (navigator.vibrate) navigator.vibrate([500, 200, 500]);
            }
        }, this.DEAD_MAN_TIMER_MS);
    }

    _clearDeadManTimer() {
        if (this.deadManTimer) {
            clearInterval(this.deadManTimer);
            this.deadManTimer = null;
        }
    }

    _showSignalLostUI() {
        let banner = document.getElementById('signalLostBanner');
        if (!banner) {
            banner = document.createElement('div');
            banner.id = 'signalLostBanner';
            banner.style.cssText = 'position:fixed;top:0;left:0;right:0;background:#dc2626;color:white;padding:12px;text-align:center;z-index:99998;font-weight:700;animation:flashBg 1s infinite;';
            banner.innerHTML = '<i class="bi bi-wifi-off"></i> SIGNAL LOST — SMS alert sent to contacts. Dead-man timer: 10 min <button onclick="document.getElementById(\'signalLostBanner\').style.display=\'none\'" style="background:none;border:none;color:white;float:right;font-size:1.2rem;">×</button>';
            document.body.prepend(banner);
        }
        banner.style.display = 'block';
    }

    _hideSignalLostUI() {
        const banner = document.getElementById('signalLostBanner');
        if (banner) banner.style.display = 'none';
    }

    _syncSignalRestoredWithServer() {
        const location = this._getCachedLocation();
        if (!location) return;

        fetch('/api/sos/trigger/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this._getCookie('csrftoken'),
            },
            body: JSON.stringify({
                latitude: location.lat,
                longitude: location.lng,
                message: 'Signal restored after loss. User is back online.',
            }),
        }).catch(() => {});
    }

    // ================================================================
    // SCENARIO B: KIDNAPPING — PANIC GESTURE
    // ================================================================

    _initPanicGesture() {
        // Method 1: Rapid volume/power button simulation via visibility changes
        // (When power button is pressed, page visibility changes)
        let visibilityChanges = 0;
        let visibilityTimer = null;

        document.addEventListener('visibilitychange', () => {
            visibilityChanges++;
            if (visibilityTimer) clearTimeout(visibilityTimer);

            visibilityTimer = setTimeout(() => {
                if (visibilityChanges >= this.PANIC_BUTTON_COUNT) {
                    this._triggerKidnappingProtocol();
                }
                visibilityChanges = 0;
            }, this.PANIC_WINDOW_MS);
        });

        // Method 2: Volume button simulation (touch events in rapid succession on edges)
        let edgeTaps = 0;
        let edgeTimer = null;
        document.addEventListener('touchstart', (e) => {
            const x = e.touches[0].clientX;
            const screenWidth = window.innerWidth;
            // Right edge or left edge tap (simulates side button area)
            if (x > screenWidth - 30 || x < 30) {
                edgeTaps++;
                if (edgeTimer) clearTimeout(edgeTimer);
                edgeTimer = setTimeout(() => {
                    if (edgeTaps >= this.PANIC_BUTTON_COUNT) {
                        this._triggerKidnappingProtocol();
                    }
                    edgeTaps = 0;
                }, this.PANIC_WINDOW_MS);
            }
        });

        // Method 3: Triple-tap on screen with 3 fingers
        document.addEventListener('touchstart', (e) => {
            if (e.touches.length >= 3) {
                this.panicPressCount++;
                if (this.panicTimer) clearTimeout(this.panicTimer);
                this.panicTimer = setTimeout(() => {
                    if (this.panicPressCount >= 2) { // 3-finger tap twice
                        this._triggerKidnappingProtocol();
                    }
                    this.panicPressCount = 0;
                }, this.PANIC_WINDOW_MS);
            }
        });
    }

    _triggerKidnappingProtocol() {
        console.error('[KIDNAPPING] PANIC PROTOCOL ACTIVATED!');

        const location = this._getCachedLocation();

        // 1. Send emergency SOS to contacts
        this._sendKidnappingSMS(location);

        // 2. Send to server (dual channel)
        this._sendKidnappingToServer(location);

        // 3. Activate siren (maximum attention)
        this._activateEmergencySiren();

        // 4. Lock into stealth mode after 5 seconds
        setTimeout(() => {
            this._activateStealthLock();
        }, 5000);

        // 5. Vibrate SOS pattern (... --- ...)
        if (navigator.vibrate) {
            navigator.vibrate([
                100, 50, 100, 50, 100, // S (...)
                200, 50, 200, 50, 200, // O (---)
                100, 50, 100, 50, 100, // S (...)
            ]);
        }
    }

    _sendKidnappingSMS(location) {
        let message = `🚨🚨🚨 EMERGENCY — POSSIBLE KIDNAPPING 🚨🚨🚨\n\n`;
        message += `I am in DANGER. This is an automated alert from SafePath AI.\n\n`;

        if (location) {
            message += `📍 LAST LOCATION:\nhttps://www.google.com/maps?q=${location.lat},${location.lng}\n\n`;
            message += `GPS: ${location.lat.toFixed(6)}, ${location.lng.toFixed(6)}\n`;
        }

        message += `⏰ Time: ${new Date().toLocaleString()}\n\n`;
        message += `⚡ PLEASE CALL POLICE IMMEDIATELY: 15\n`;
        message += `🚑 Rescue: 1122\n`;
        message += `\n⚠️ If my phone goes off, this was my last known location.`;

        this._triggerSMS(message);
    }

    _sendKidnappingToServer(location) {
        if (!navigator.onLine) return;

        fetch('/api/sos/trigger/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this._getCookie('csrftoken'),
            },
            body: JSON.stringify({
                latitude: location ? location.lat : 0,
                longitude: location ? location.lng : 0,
                message: 'KIDNAPPING ALERT — Panic gesture triggered. Send help immediately!',
            }),
        }).catch(() => {});
    }

    _activateEmergencySiren() {
        // Create maximum volume siren
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.type = 'sawtooth';
            gain.gain.value = 1;

            const now = ctx.currentTime;
            for (let i = 0; i < 100; i++) {
                osc.frequency.setValueAtTime(600, now + i * 0.5);
                osc.frequency.linearRampToValueAtTime(1500, now + i * 0.5 + 0.25);
                osc.frequency.linearRampToValueAtTime(600, now + i * 0.5 + 0.5);
            }
            osc.start();

            // Store reference to stop later if needed
            this._sirenOsc = osc;
            this._sirenCtx = ctx;
        } catch (e) {}

        // Flash screen
        const overlay = document.createElement('div');
        overlay.id = 'kidnappingOverlay';
        overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;z-index:99999;animation:kidnappingFlash 0.3s infinite alternate;';
        overlay.innerHTML = '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:white;text-align:center;font-size:2rem;font-weight:900;">🚨 SOS ALERT SENT 🚨<br><br>POLICE: 15<br>RESCUE: 1122</div>';
        document.body.appendChild(overlay);

        // Add flash animation
        const style = document.createElement('style');
        style.textContent = '@keyframes kidnappingFlash{0%{background:rgba(220,38,38,0.95)}100%{background:rgba(29,78,216,0.95)}}';
        document.head.appendChild(style);
    }

    _activateStealthLock() {
        // After siren draws attention, switch to stealth mode
        // Remove the overlay (kidnapper thinks app stopped)
        this.stealthLocked = true;
        const overlay = document.getElementById('kidnappingOverlay');
        if (overlay) overlay.remove();

        // Stop siren sound
        if (this._sirenOsc) { try { this._sirenOsc.stop(); } catch(e){} }
        if (this._sirenCtx) { this._sirenCtx.close(); }

        // Replace entire page with black screen (looks like phone crashed)
        document.body.innerHTML = '';
        document.body.style.cssText = 'background:#000;margin:0;padding:0;';

        // But continue sending location silently in background
        this._startStealthTracking();
    }

    _startStealthTracking() {
        // Silently send location every 30 seconds even though screen is black
        setInterval(() => {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition((pos) => {
                    const loc = { lat: pos.coords.latitude, lng: pos.coords.longitude };
                    localStorage.setItem('safepath_last_location', JSON.stringify({...loc, timestamp: Date.now()}));

                    // Try to send to server
                    if (navigator.onLine) {
                        fetch('/api/sos/shake/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': this._getCookie('csrftoken'),
                            },
                            body: JSON.stringify({
                                latitude: loc.lat,
                                longitude: loc.lng,
                                trigger: 'stealth_tracking',
                            }),
                        }).catch(() => {});
                    }
                }, () => {});
            }
        }, 30000);
    }

    // ================================================================
    // SCENARIO B: PRE-SHUTDOWN DETECTION
    // ================================================================

    _initShutdownDetector() {
        // Detect when page is being unloaded (phone shutting down or app being killed)
        window.addEventListener('beforeunload', (e) => {
            if (this.isJourneyActive || this.stealthLocked) {
                this._sendShutdownAlert();
            }
        });

        // Also detect visibility hidden (phone sleep or app switch)
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'hidden' && (this.isJourneyActive || this.stealthLocked)) {
                this._sendShutdownAlert();
            }
        });

        // Battery API — alert when battery critically low
        if ('getBattery' in navigator) {
            navigator.getBattery().then(battery => {
                battery.addEventListener('levelchange', () => {
                    if (battery.level <= 0.05 && this.isJourneyActive) { // 5% battery
                        this._sendBatteryLowAlert(battery.level);
                    }
                });
            });
        }
    }

    _sendShutdownAlert() {
        const location = this._getCachedLocation();
        let message = `🚨 SafePath ALERT: Device shutting down!\n\n`;

        if (location) {
            message += `📍 FINAL LOCATION:\nhttps://www.google.com/maps?q=${location.lat},${location.lng}\n\n`;
            message += `GPS: ${location.lat.toFixed(6)}, ${location.lng.toFixed(6)}\n`;
        }

        message += `⏰ Time: ${new Date().toLocaleString()}\n`;
        message += `⚠️ Phone is being turned off or app is being closed.\n`;
        message += `📞 CALL ME or contact Police: 15`;

        // Use sendBeacon for reliable delivery before page closes
        if (navigator.sendBeacon && navigator.onLine) {
            const data = JSON.stringify({
                latitude: location ? location.lat : 0,
                longitude: location ? location.lng : 0,
                message: 'DEVICE SHUTTING DOWN. Final location sent. Check on user immediately.',
            });
            navigator.sendBeacon('/api/sos/trigger/', new Blob([data], {type: 'application/json'}));
        }

        // Also try SMS (may not complete before shutdown)
        this._triggerSMS(message);
    }

    _sendBatteryLowAlert(level) {
        const location = this._getCachedLocation();
        const pct = Math.round(level * 100);
        let message = `⚠️ SafePath: Battery critically low (${pct}%)!\n\n`;

        if (location) {
            message += `📍 Current location:\nhttps://www.google.com/maps?q=${location.lat},${location.lng}\n\n`;
        }

        message += `Phone may shut down soon. Last update: ${new Date().toLocaleTimeString()}\n`;
        message += `📞 Please check on me. Emergency: 15 | 1122`;

        this._triggerSMS(message);
    }

    // ================================================================
    // SHARED UTILITIES
    // ================================================================

    _triggerSMS(message) {
        // Load contacts from localStorage
        const contacts = JSON.parse(localStorage.getItem('safepath_emergency_contacts') || '[]');
        if (contacts.length === 0) return;

        const numbers = contacts.map(c => c.phone).join(',');
        const smsURI = `sms:${numbers}?body=${encodeURIComponent(message)}`;

        // Create hidden link and click it
        const link = document.createElement('a');
        link.href = smsURI;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    _initLocationCache() {
        // Continuously cache GPS for offline use
        if (navigator.geolocation) {
            const updateCache = () => {
                navigator.geolocation.getCurrentPosition((pos) => {
                    this.lastKnownLocation = {
                        lat: pos.coords.latitude,
                        lng: pos.coords.longitude,
                        accuracy: pos.coords.accuracy,
                        timestamp: Date.now(),
                    };
                    localStorage.setItem('safepath_last_location', JSON.stringify(this.lastKnownLocation));
                }, () => {});
            };
            updateCache();
            setInterval(updateCache, 20000); // Every 20 seconds
        }
    }

    _getCachedLocation() {
        if (this.lastKnownLocation) return this.lastKnownLocation;
        const cached = localStorage.getItem('safepath_last_location');
        return cached ? JSON.parse(cached) : null;
    }

    _getCookie(name) {
        let v = null;
        if (document.cookie) {
            document.cookie.split(';').forEach(c => {
                c = c.trim();
                if (c.startsWith(name + '=')) v = decodeURIComponent(c.substring(name.length + 1));
            });
        }
        return v;
    }
}


// ================================================================
// AUTO-INITIALIZE
// ================================================================
let emergencyHandler = null;

document.addEventListener('DOMContentLoaded', () => {
    emergencyHandler = new EmergencyScenarios();
    window.emergencyHandler = emergencyHandler;
    console.log('[EmergencyScenarios] Ready. Panic gesture and signal monitoring active.');
});
