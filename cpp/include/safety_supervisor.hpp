#pragma once
#include <cstdint>
#include <string>

struct Telemetry {
    double timestamp_s{};
    double speed_kph{};
    double soc_pct{};
    double battery_temp_c{};
    double battery_current_a{};
    double requested_torque_nm{};
    double can_age_ms{};
    unsigned can_counter{};
};

enum class State { NORMAL, DERATED, FAULT };

struct Decision {
    State state{State::NORMAL};
    double allowed_torque_nm{};
    std::string reason{"OK"};
};

class SafetySupervisor {
public:
    Decision step(const Telemetry& t);
private:
    bool has_counter_{false};
    unsigned last_counter_{0};
    bool latched_fault_{false};
};
const char* state_name(State s);
