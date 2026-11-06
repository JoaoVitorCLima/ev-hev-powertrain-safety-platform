#include "safety_supervisor.hpp"
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

static Telemetry parse(const std::string& line) {
    std::stringstream ss(line);
    std::vector<std::string> fields;
    std::string field;
    while (std::getline(ss, field, ',')) fields.push_back(field);
    if (fields.size() != 8) throw std::runtime_error("Expected 8 CSV fields");
    for (auto& value : fields) if (!value.empty() && value.back() == '\r') value.pop_back();
    Telemetry t;
    t.timestamp_s = std::stod(fields[0]);
    t.speed_kph = std::stod(fields[1]);
    t.soc_pct = std::stod(fields[2]);
    t.battery_temp_c = std::stod(fields[3]);
    t.battery_current_a = std::stod(fields[4]);
    t.requested_torque_nm = std::stod(fields[5]);
    t.can_age_ms = std::stod(fields[6]);
    const unsigned long counter = std::stoul(fields[7]);
    if (counter > 15UL) throw std::runtime_error("CAN counter out of range");
    t.can_counter = static_cast<unsigned>(counter);
    return t;
}
static void decision_row(std::ostream& out, const Telemetry& t, const Decision& d) {
    out << std::fixed << std::setprecision(3) << t.timestamp_s << ','
        << state_name(d.state) << ',' << d.allowed_torque_nm << ',' << d.reason << '\n';
    out.flush();
}
static const char* HEADER = "timestamp_s,speed_kph,soc_pct,battery_temp_c,battery_current_a,requested_torque_nm,can_age_ms,can_counter";
int main(int argc, char** argv) {
    // --stream is a persistent request/response protocol. One telemetry CSV line in,
    // one decision CSV line out, flushing on every row. Suitable for local SIL co-simulation.
    if (argc == 2 && std::string(argv[1]) == "--stream") {
        SafetySupervisor supervisor;
        std::cout << "timestamp_s,state,allowed_torque_nm,reason\n" << std::flush;
        std::string line;
        while (std::getline(std::cin, line)) {
            if (line.empty()) continue;
            try {
                const auto t = parse(line);
                decision_row(std::cout, t, supervisor.step(t));
            } catch (const std::exception& e) {
                std::cerr << "Stream parse error: " << e.what() << '\n';
                return 2;
            }
        }
        return 0;
    }
    if (argc != 3) {
        std::cerr << "Usage: safety_supervisor INPUT.csv OUTPUT.csv | --stream\n";
        return 2;
    }
    std::ifstream in(argv[1]);
    std::ofstream out(argv[2]);
    if (!in || !out) {
        std::cerr << "Unable to open input or output file\n";
        return 2;
    }
    std::string line;
    if (!std::getline(in, line)) { std::cerr << "Missing CSV header\n"; return 2; }
    if (!line.empty() && line.back() == '\r') line.pop_back();
    if (line != HEADER) { std::cerr << "Invalid CSV header\n"; return 2; }
    out << "timestamp_s,state,allowed_torque_nm,reason\n";
    SafetySupervisor supervisor;
    std::size_t n = 0;
    try {
        while (std::getline(in, line)) {
            if (line.empty()) continue;
            const auto t = parse(line);
            decision_row(out, t, supervisor.step(t));
            ++n;
        }
    } catch (const std::exception& e) {
        std::cerr << "CSV parse error on data row " << (n + 1) << ": " << e.what() << '\n';
        return 2;
    }
    std::cout << "Processed " << n << " telemetry frames -> " << argv[2] << '\n';
    return 0;
}
