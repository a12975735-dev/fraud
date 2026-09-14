/**
 * Behavioral Biometrics Tracking Script
 * -------------------------------------
 * Captures keystroke dynamics (dwell & flight times) and throttled mouse movement
 * features (MDA, MSD, total distance, average speed) for continuous fraud scoring.
 */

(function (root, factory) {
  if (typeof define === 'function' && define.amd) {
    define([], factory);
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.BehavioralBiometricsTracker = factory();
  }
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  class BehavioralBiometricsTracker {
    /**
     * @param {Object} options Configuration options
     * @param {number} [options.throttleMs=50] Throttle interval for mousemove events in ms
     * @param {EventTarget} [options.targetElement=window] DOM target element for event listeners
     */
    constructor(options = {}) {
      this.throttleMs = options.throttleMs || 50;
      this.targetElement = options.targetElement || (typeof window !== 'undefined' ? window : null);

      // Keystroke state
      this.activeKeydowns = new Map();
      this.dwellTimes = [];
      this.flightTimes = [];
      this.lastKeyUpTimestamp = null;

      // Mouse tracking state
      this.mousePoints = [];
      this.lastMouseThrottleTime = 0;

      // Bound event handler references for proper cleanup
      this._handleKeyDown = this._handleKeyDown.bind(this);
      this._handleKeyUp = this._handleKeyUp.bind(this);
      this._handleMouseMove = this._handleMouseMove.bind(this);

      this.isTracking = false;
      this._scoreTimer = null;
      this.scoringEndpoint = options.scoringEndpoint || 'http://127.0.0.1:8000/api/v1/biometrics/score';
      this.lastBiometricResult = null;
      if (options.autoStart !== false && this.targetElement) {
        this.start();
      }
      if (options.autoSend !== false && typeof window !== 'undefined') {
        this.startPeriodicScoring(options.sendIntervalMs || 2500);
      }
    }

    /**
     * Attach event listeners to start tracking.
     */
    start() {
      if (this.isTracking || !this.targetElement) return;

      this.targetElement.addEventListener('keydown', this._handleKeyDown, true);
      this.targetElement.addEventListener('keyup', this._handleKeyUp, true);
      this.targetElement.addEventListener('mousemove', this._handleMouseMove, true);

      this.isTracking = true;
    }

    /**
     * Remove event listeners and stop tracking to prevent memory leaks.
     */
    cleanup() {
      if (!this.isTracking || !this.targetElement) return;

      this.targetElement.removeEventListener('keydown', this._handleKeyDown, true);
      this.targetElement.removeEventListener('keyup', this._handleKeyUp, true);
      this.targetElement.removeEventListener('mousemove', this._handleMouseMove, true);

      this.isTracking = false;
      this.stopPeriodicScoring();
    }

    /**
     * Reset recorded biometric buffers.
     */
    reset() {
      this.activeKeydowns.clear();
      this.dwellTimes = [];
      this.flightTimes = [];
      this.lastKeyUpTimestamp = null;
      this.mousePoints = [];
      this.lastMouseThrottleTime = 0;
    }

    /**
     * KeyDown Event Handler
     */
    _handleKeyDown(event) {
      if (event.repeat) return;

      const now = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();

      if (this.lastKeyUpTimestamp !== null) {
        const flightTime = now - this.lastKeyUpTimestamp;
        if (flightTime >= 0 && flightTime < 10000) {
          this.flightTimes.push(flightTime);
        }
      }

      const keyIdentifier = event.code || event.key;
      this.activeKeydowns.set(keyIdentifier, now);
    }

    /**
     * KeyUp Event Handler
     */
    _handleKeyUp(event) {
      const now = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
      const keyIdentifier = event.code || event.key;

      if (this.activeKeydowns.has(keyIdentifier)) {
        const keyDownTimestamp = this.activeKeydowns.get(keyIdentifier);
        const dwellTime = now - keyDownTimestamp;
        if (dwellTime >= 0 && dwellTime < 10000) {
          this.dwellTimes.push(dwellTime);
        }
        this.activeKeydowns.delete(keyIdentifier);
      }

      this.lastKeyUpTimestamp = now;
    }

    /**
     * Throttled MouseMove Event Handler
     */
    _handleMouseMove(event) {
      const now = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();

      if (now - this.lastMouseThrottleTime < this.throttleMs) {
        return;
      }
      this.lastMouseThrottleTime = now;

      const x = event.clientX !== undefined ? event.clientX : event.pageX || 0;
      const y = event.clientY !== undefined ? event.clientY : event.pageY || 0;

      this.mousePoints.push({ x, y, timestamp: now });
    }

    /**
     * Calculate average helper.
     */
    _mean(array) {
      if (!array || array.length === 0) return 0.0;
      const sum = array.reduce((acc, val) => acc + val, 0);
      return sum / array.length;
    }

    /**
     * Calculate Movement Direction Average (MDA) in degrees using Math.atan2.
     */
    _calculateMDA() {
      if (this.mousePoints.length < 2) return 0.0;

      const angles = [];
      for (let i = 0; i < this.mousePoints.length - 1; i++) {
        const p1 = this.mousePoints[i];
        const p2 = this.mousePoints[i + 1];
        const dx = p2.x - p1.x;
        const dy = p2.y - p1.y;

        if (dx === 0 && dy === 0) continue;

        // Angle in radians [-PI, PI], converted to degrees [-180, 180]
        const angleRad = Math.atan2(dy, dx);
        const angleDeg = angleRad * (180.0 / Math.PI);
        angles.push(angleDeg);
      }

      return this._mean(angles);
    }

    /**
     * Calculate mouse movement metrics: total distance, average speed, and MSD ratio.
     */
    _calculateMouseMetrics() {
      if (this.mousePoints.length < 2) {
        return { total_distance: 0.0, avg_speed: 0.0, msd: 0.0, mda: 0.0 };
      }

      let totalDistance = 0.0;
      const stepSpeeds = [];
      const startTime = this.mousePoints[0].timestamp;
      const endTime = this.mousePoints[this.mousePoints.length - 1].timestamp;
      const totalTimeMs = endTime - startTime;

      for (let i = 0; i < this.mousePoints.length - 1; i++) {
        const p1 = this.mousePoints[i];
        const p2 = this.mousePoints[i + 1];
        const dx = p2.x - p1.x;
        const dy = p2.y - p1.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const dt = p2.timestamp - p1.timestamp;

        totalDistance += dist;
        if (dt > 0) {
          stepSpeeds.push(dist / dt); // Speed in pixels per ms
        }
      }

      const avgSpeed = totalTimeMs > 0 ? (totalDistance / totalTimeMs) : this._mean(stepSpeeds);
      const msd = totalDistance > 0 ? (avgSpeed / totalDistance) : 0.0;
      const mda = this._calculateMDA();

      return {
        mda: Number(mda.toFixed(4)),
        msd: Number(msd.toFixed(6)),
        total_distance: Number(totalDistance.toFixed(2)),
        avg_speed: Number(avgSpeed.toFixed(4))
      };
    }

    /**
     * Generate structured biometric payload.
     * @returns {Object} JSON payload with exact required keys.
     */
    getBiometricPayload() {
      const avgDwell = this._mean(this.dwellTimes);
      const avgFlight = this._mean(this.flightTimes);
      const mouseMetrics = this._calculateMouseMetrics();

      return {
        keystroke_features: {
          avg_dwell_time: Number(avgDwell.toFixed(2)),
          avg_flight_time: Number(avgFlight.toFixed(2))
        },
        mouse_features: mouseMetrics
      };
    }

    /**
     * POST captured telemetry to the existing biometrics scoring endpoint.
     * @param {string} [endpoint] Target API endpoint
     * @returns {Promise<Object>} API response JSON
     */
    async sendBiometricPayload(endpoint) {
      const target = endpoint || this.scoringEndpoint || 'http://127.0.0.1:8000/api/v1/biometrics/score';
      const payload = this.getBiometricPayload();

      if (typeof fetch === 'undefined') {
        throw new Error('Fetch API is not available in current environment.');
      }

      const response = await fetch(target, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Biometric API post failed (${response.status}): ${errorText}`);
      }

      const result = await response.json();
      this.lastBiometricResult = result;
      return result;
    }

    /**
     * Periodically POST telemetry while the tracker is running.
     */
    startPeriodicScoring(intervalMs, endpoint) {
      this.stopPeriodicScoring();
      if (typeof window === 'undefined') return;

      const send = () => {
        const payload = this.getBiometricPayload();
        const hasSignal = payload.keystroke_features.avg_dwell_time > 0
          || payload.mouse_features.total_distance > 0;
        if (!hasSignal) return;
        this.sendBiometricPayload(endpoint).catch((error) => {
          if (typeof console !== 'undefined') {
            console.warn('Biometric telemetry was not scored:', error);
          }
        });
      };

      this._scoreTimer = window.setInterval(send, intervalMs || 2500);
    }

    stopPeriodicScoring() {
      if (this._scoreTimer !== null && typeof window !== 'undefined') {
        window.clearInterval(this._scoreTimer);
        this._scoreTimer = null;
      }
    }
  }

  // Auto-instantiate default global tracker in browser environments
  if (typeof window !== 'undefined') {
    window.biometricsTracker = new BehavioralBiometricsTracker({ autoStart: true });
  }

  return BehavioralBiometricsTracker;
}));
