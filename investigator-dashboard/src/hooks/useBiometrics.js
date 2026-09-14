import { useState, useEffect, useRef, useCallback } from 'react';

const BIOMETRICS_SCORING_URL = 'http://127.0.0.1:8000/api/v1/biometrics/score';

/**
 * useBiometrics — Native React behavioral biometrics telemetry hook.
 *
 * Implements the same metrics specified in §4.1 of the project proposal:
 *   - Keystroke dynamics: avg_dwell_time, avg_flight_time ("cognitive rhythms")
 *   - Mouse movement: MDA (Movement Direction Average, degrees via Math.atan2),
 *                     MSD (Movement Speed to Distance ratio),
 *                     total_distance, avg_speed
 *
 * All listeners are cleaned up on unmount (no memory leaks).
 * No dependency on static/biometrics.js — fully self-contained React hook.
 */
export default function useBiometrics() {
  const [metrics, setMetrics] = useState({
    avgDwellTime: 0,
    avgFlightTime: 0,
    mda: 0,
    msd: 0,
    totalDistance: 0,
    avgSpeed: 0,
  });
  const [biometricResult, setBiometricResult] = useState({
    biometricRiskScore: null,
    biometricRiskLevel: null,
  });
  const lastScoredAt = useRef(0);

  // Keystroke state — refs to avoid stale closure issues
  const keyDownTimes = useRef({});
  const dwellTimes = useRef([]);
  const flightTimes = useRef([]);
  const lastKeyUpTime = useRef(null);

  // Mouse state
  const lastMousePos = useRef(null);
  const lastMouseTime = useRef(null);
  const totalDistance = useRef(0);
  const speedSamples = useRef([]);
  const directionChanges = useRef([]);
  const lastDirection = useRef(null);
  const mouseThrottleTimer = useRef(null);

  // ── Compute and push updated metrics to state ──────────────────────────────
  const flushMetrics = useCallback(() => {
    const dwell = dwellTimes.current;
    const flight = flightTimes.current;
    const speeds = speedSamples.current;

    const avgDwellTime = dwell.length
      ? Math.round(dwell.reduce((a, b) => a + b, 0) / dwell.length)
      : 0;
    const avgFlightTime = flight.length
      ? Math.round(flight.reduce((a, b) => a + b, 0) / flight.length)
      : 0;
    const avgSpeed = speeds.length
      ? Math.round(speeds.reduce((a, b) => a + b, 0) / speeds.length)
      : 0;

    // MDA: circular mean of direction change angles (degrees)
    const dirs = directionChanges.current;
    let mda = 0;
    if (dirs.length > 0) {
      const sinSum = dirs.reduce((s, a) => s + Math.sin((a * Math.PI) / 180), 0);
      const cosSum = dirs.reduce((s, a) => s + Math.cos((a * Math.PI) / 180), 0);
      mda = Math.round(
        ((Math.atan2(sinSum / dirs.length, cosSum / dirs.length) * 180) / Math.PI + 360) % 360
      );
    }

    // MSD: ratio of avg speed to total distance traveled (bounded 0–1)
    const dist = totalDistance.current;
    const msd = dist > 0 ? parseFloat(Math.min(avgSpeed / dist, 1).toFixed(4)) : 0;

    setMetrics({
      avgDwellTime,
      avgFlightTime,
      mda,
      msd,
      totalDistance: Math.round(dist),
      avgSpeed,
    });
  }, []);

  // ── Keystroke handlers ────────────────────────────────────────────────────
  const handleKeyDown = useCallback((e) => {
    if (!keyDownTimes.current[e.code]) {
      keyDownTimes.current[e.code] = performance.now();
    }
  }, []);

  const handleKeyUp = useCallback(
    (e) => {
      const downTime = keyDownTimes.current[e.code];
      if (downTime !== undefined) {
        const dwell = performance.now() - downTime;
        dwellTimes.current.push(dwell);
        // Keep last 50 samples for a rolling window
        if (dwellTimes.current.length > 50) dwellTimes.current.shift();
        delete keyDownTimes.current[e.code];
      }

      const now = performance.now();
      if (lastKeyUpTime.current !== null) {
        const flight = now - lastKeyUpTime.current;
        if (flight < 2000) {
          // Ignore gaps > 2s (user paused typing)
          flightTimes.current.push(flight);
          if (flightTimes.current.length > 50) flightTimes.current.shift();
        }
      }
      lastKeyUpTime.current = now;
      flushMetrics();
    },
    [flushMetrics]
  );

  // ── Mouse handler (throttled to 50ms per proposal §4.1) ──────────────────
  const handleMouseMove = useCallback(
    (e) => {
      if (mouseThrottleTimer.current) return;
      mouseThrottleTimer.current = setTimeout(() => {
        mouseThrottleTimer.current = null;
      }, 50);

      const now = performance.now();
      const x = e.clientX;
      const y = e.clientY;

      if (lastMousePos.current) {
        const dx = x - lastMousePos.current.x;
        const dy = y - lastMousePos.current.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const dt = now - lastMouseTime.current; // ms

        if (dist > 1) {
          totalDistance.current += dist;

          // Speed in px/s
          const speed = dt > 0 ? (dist / dt) * 1000 : 0;
          speedSamples.current.push(speed);
          if (speedSamples.current.length > 100) speedSamples.current.shift();

          // Direction angle in degrees (Math.atan2 per proposal §4.1)
          const angleDeg = (Math.atan2(dy, dx) * 180) / Math.PI;
          directionChanges.current.push(angleDeg);
          if (directionChanges.current.length > 100) directionChanges.current.shift();
          lastDirection.current = angleDeg;
        }
      }

      lastMousePos.current = { x, y };
      lastMouseTime.current = now;
      flushMetrics();
    },
    [flushMetrics]
  );

  // ── Mount / unmount lifecycle ─────────────────────────────────────────────
  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    window.addEventListener('mousemove', handleMouseMove);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
      window.removeEventListener('mousemove', handleMouseMove);
      if (mouseThrottleTimer.current) clearTimeout(mouseThrottleTimer.current);
    };
  }, [handleKeyDown, handleKeyUp, handleMouseMove]);

  useEffect(() => {
    const hasTelemetry = metrics.avgDwellTime > 0 && metrics.avgFlightTime > 0 && metrics.totalDistance > 0;
    if (!hasTelemetry || Date.now() - lastScoredAt.current < 2000) return undefined;

    const controller = new AbortController();
    lastScoredAt.current = Date.now();
    fetch(BIOMETRICS_SCORING_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        keystroke_features: {
          avg_dwell_time: metrics.avgDwellTime,
          avg_flight_time: metrics.avgFlightTime,
        },
        mouse_features: {
          mda: metrics.mda,
          msd: metrics.msd,
          total_distance: metrics.totalDistance,
          avg_speed: metrics.avgSpeed,
        },
      }),
      signal: controller.signal,
    })
      .then((response) => (response.ok ? response.json() : Promise.reject(new Error('Biometric scoring failed'))))
      .then((data) => setBiometricResult({
        biometricRiskScore: data.biometric_score,
        biometricRiskLevel: data.risk_level,
      }))
      .catch((error) => {
        if (error.name !== 'AbortError') console.warn('Biometric telemetry was not scored:', error);
      });

    return () => controller.abort();
  }, [metrics]);

  return { ...metrics, ...biometricResult };
}
