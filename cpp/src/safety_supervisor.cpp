#include "safety_supervisor.hpp"
#include <algorithm>
#include <cmath>

const char* state_name(State s) {
    switch (s) {
        case State::NORMAL: return "NORMAL";
        case State::DERATED: return "DERATED";
        case State::FAULT: return "FAULT";
    }
    return "UNKNOWN";
}

Decision SafetySupervisor::step(const Telemetry& t) {
    // Illustrative supervisory thresholds, NOT automotive-calibrated values.
    // In this simulation, FAULT inhibits requested motor torque in this synthetic plant.
    // It does not model vehicle stabilization, contactors or safe-stop logic.
    const bool finite = std::isfinite(t.timestamp_s) && std::isfinite(t.speed_kph) &&
        std::isfinite(t.soc_pct) && std::isfinite(t.battery_temp_c) &&
        std::isfinite(t.battery_current_a) && std::isfinite(t.requested_torque_nm) &&
        std::isfinite(t.can_age_ms);
    if (!finite || t.soc_pct < 0.0 || t.soc_pct > 100.0 || t.can_age_ms < 0.0 ||
        t.can_counter > 15U) {
        latched_fault_ = true;
        return {State::FAULT, 0.0, "INVALID_TELEMETRY"};
    }
    const bool bad_counter = has_counter_ && (t.can_counter != ((last_counter_ + 1U) % 16U));
    last_counter_ = t.can_counter;
    has_counter_ = true;
    if (bad_counter || t.can_age_ms > 100.0) {
        latched_fault_ = true;
        return {State::FAULT, 0.0, bad_counter ? "CAN_COUNTER" : "CAN_TIMEOUT"};
    }
    if (t.battery_temp_c >= 60.0 || std::abs(t.battery_current_a) >= 300.0) {
        latched_fault_ = true;
        return {State::FAULT, 0.0, t.battery_temp_c >= 60.0 ? "BATTERY_OVERTEMP" : "OVERCURRENT"};
    }
    if (latched_fault_) return {State::FAULT, 0.0, "FAULT_LATCHED"};
    if (t.battery_temp_c >= 48.0 || t.soc_pct < 15.0 ||
        std::abs(t.battery_current_a) > 200.0) {
        return {State::DERATED, std::clamp(t.requested_torque_nm, -20.0, 60.0), "POWER_DERATING"};
    }
    return {State::NORMAL, std::clamp(t.requested_torque_nm, -60.0, 180.0), "OK"};
}
