#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <map>
#include <stdexcept>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <set>
#include <gsl/gsl_errno.h>

// Avoid macro conflicts: include native headers and rename main
#define main magrathea_native_main
#include "src/main.cpp"
#undef main

// Forward declaration from phase.h
void configure_prescribed_hhe_audit();

// Allowed global EOS pointers for label lookup
static std::vector<EOS*> global_eos_ptrs() {
    std::vector<EOS*> v;
    v.push_back(Fe_hcp);
    v.push_back(Fe_liquid);
    v.push_back(Fe_liquid2);
    v.push_back(Water_SF);
    v.push_back(Water_Brown);
    v.push_back(Water_IAPWS);
    v.push_back(Water_Vap_IAPWS);
    v.push_back(Water_sc_Mazevet);
    v.push_back(IceIh_SF);
    v.push_back(IceII_SF);
    v.push_back(IceIII_SF);
    v.push_back(IceV_SF);
    v.push_back(IceVI_SF);
    v.push_back(IceVII_Bezacier);
    v.push_back(IceVII_Fei);
    v.push_back(IceX);
    v.push_back(vdW_H2O);
    v.push_back(vdW_H2O_iso);
    v.push_back(vdW_H2O_lo);
    v.push_back(vdW_H2O_hi);
    v.push_back(Gas_iso);
    v.push_back(Gas_hhe);
    return v;
}

// Helper: find EOS pointer by exact full phase label (unique match)
static EOS* find_eos_by_label(const std::string& label) {
    std::vector<EOS*> ptrs = global_eos_ptrs();
    EOS* found = NULL;
    int count = 0;
    for (size_t i = 0; i < ptrs.size(); ++i) {
        if (ptrs[i]->getEOS() == label) {
            found = ptrs[i];
            ++count;
        }
    }
    if (count == 1) return found;
    if (count == 0) throw std::runtime_error("phase label not found: " + label);
    throw std::runtime_error("phase label ambiguous: " + label);
}

// Helper: escape a string for JSON
std::string json_escape(const std::string& s) {
    std::string out;
    out.reserve(s.size());
    for (char c : s) {
        switch (c) {
            case '"': out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\b': out += "\\b"; break;
            case '\f': out += "\\f"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default:
                if (static_cast<unsigned char>(c) < 0x20) {
                    char buf[7];
                    snprintf(buf, sizeof(buf), "\\u%04x", c);
                    out += buf;
                } else {
                    out += c;
                }
        }
    }
    return out;
}

// Helper: format a double with 17 significant digits
std::string fmt17(double x) {
    char buf[64];
    snprintf(buf, sizeof(buf), "%.17g", x);
    return std::string(buf);
}

// Write runtime JSON after a --run invocation
void write_runtime_json(const std::string& path, int cli_exit_code, bool strict_audit, unsigned long long rejected,
                        const std::map<std::string, unsigned long long>& density_counts,
                        const std::map<std::string, unsigned long long>& gradient_counts) {
    std::ofstream out(path.c_str());
    if (!out) {
        throw std::runtime_error("Unable to open output file: " + path);
    }
    out << "{\n";
    out << "  \"cli_exit_code\": " << cli_exit_code << ",\n";
    out << "  \"strict_table_audit\": " << (strict_audit ? "true" : "false") << ",\n";
    out << "  \"rejected_table_queries\": " << rejected << ",\n";
    out << "  \"density_audit_counts\": {";
    bool first = true;
    for (std::map<std::string, unsigned long long>::const_iterator it = density_counts.begin(); it != density_counts.end(); ++it) {
        if (!first) out << ",";
        out << "\n    \"" << json_escape(it->first) << "\": " << it->second;
        first = false;
    }
    if (!density_counts.empty()) out << "\n  ";
    out << "},\n";
    out << "  \"gradient_audit_counts\": {";
    first = true;
    for (std::map<std::string, unsigned long long>::const_iterator it = gradient_counts.begin(); it != gradient_counts.end(); ++it) {
        if (!first) out << ",";
        out << "\n    \"" << json_escape(it->first) << "\": " << it->second;
        first = false;
    }
    if (!gradient_counts.empty()) out << "\n  ";
    out << "}\n";
    out << "}\n";
}

// Mode 1: --run <config.cfg> <runtime.json>
int run_mode(const std::string& config_path, const std::string& runtime_json_path) {
    // Refuse if runtime.json exists
    std::ifstream check(runtime_json_path.c_str());
    if (check.good()) {
        std::cerr << "Error: runtime output file already exists: " << runtime_json_path << std::endl;
        return 1;
    }
    check.close();

    // Disable GSL error handler
    gsl_set_error_handler_off();

    // Configure audit before invoking native main
    configure_prescribed_hhe_audit();

    // Prepare argv for magrathea_native_main
    char arg0[] = "native_audit";
    char* argv2[2];
    argv2[0] = arg0;
    argv2[1] = const_cast<char*>(config_path.c_str());
    int native_argc = 2;

    int exit_code = magrathea_native_main(native_argc, argv2);

    bool strict = EOS::strict_table_audit();
    unsigned long long rejected = EOS::rejected_table_queries();
    std::map<std::string, unsigned long long> density_counts = EOS::density_audit_counts();
    std::map<std::string, unsigned long long> gradient_counts = EOS::gradient_audit_counts();

    try {
        write_runtime_json(runtime_json_path, exit_code, strict, rejected, density_counts, gradient_counts);
    } catch (const std::exception& e) {
        std::cerr << "Error writing runtime JSON: " << e.what() << std::endl;
        return 1;
    }

    return exit_code;
}

// Mode 2: --probe <probe.csv>
int probe_mode(const std::string& output_csv) {
    std::ifstream check(output_csv.c_str());
    if (check.good()) {
        std::cerr << "Error: probe output file already exists: " << output_csv << std::endl;
        return 1;
    }
    check.close();

    gsl_set_error_handler_off();
    configure_prescribed_hhe_audit();

    std::ofstream out(output_csv.c_str());
    if (!out) {
        std::cerr << "Error: cannot open output file: " << output_csv << std::endl;
        return 1;
    }

    out << "kind,P_bar,T_K,eos_id,rho_g_cm3,dTdP_K_per_GPa,mmol,thermal_code,table_domain_contains\n";

    const double T = 350.0;
    const double P_bar_exact = 100.0;

    // Gas_iso at exactly 100 bar
    double rho_guess = -1.0;
    double rho_iso = Gas_iso->density(P_bar_exact * 1e6, T, rho_guess);
    if (!std::isfinite(rho_iso)) {
        std::cerr << "Error: Gas_iso density nonfinite" << std::endl;
        return 1;
    }
    rho_guess = rho_iso; // meaningful for dTdP_S
    double dTdP_iso = Gas_iso->dTdP_S(P_bar_exact * 1e-4, T, rho_guess); // Convert bar to GPa (1 bar = 1e-4 GPa)
    // Correct conversion: P_GPa = P_bar * 1e-4.
    double mmol_iso = Gas_iso->getmmol();
    int thermal_iso = Gas_iso->thermal_code();
    bool domain_iso = Gas_iso->table_domain_contains(P_bar_exact * 1e6, T);
    out << "common_ideal," << fmt17(P_bar_exact) << "," << fmt17(T) << ",Gas_iso,"
        << fmt17(rho_iso) << "," << fmt17(dTdP_iso) << "," << fmt17(mmol_iso) << ","
        << thermal_iso << "," << (domain_iso ? "true" : "false") << "\n";

    // Gas_hhe at exactly 100 bar
    rho_guess = -1.0;
    double rho_hhe = Gas_hhe->density(P_bar_exact * 1e6, T, rho_guess);
    if (!std::isfinite(rho_hhe)) {
        std::cerr << "Error: Gas_hhe density nonfinite" << std::endl;
        return 1;
    }
    rho_guess = rho_hhe;
    double dTdP_hhe = Gas_hhe->dTdP_S(P_bar_exact * 1e-4, T, rho_guess);
    double mmol_hhe = Gas_hhe->getmmol();
    int thermal_hhe = Gas_hhe->thermal_code();
    bool domain_hhe = Gas_hhe->table_domain_contains(P_bar_exact * 1e6, T);
    out << "common_hhe," << fmt17(P_bar_exact) << "," << fmt17(T) << ",Gas_hhe,"
        << fmt17(rho_hhe) << "," << fmt17(dTdP_hhe) << "," << fmt17(mmol_hhe) << ","
        << thermal_hhe << "," << (domain_hhe ? "true" : "false") << "\n";

    // selector rows at 100*(1-1e-8), 100, 100*(1+1e-8)
    const double deltas[3] = {-1.0e-8, 0.0, 1.0e-8};
    const char* kinds[3] = {"selector_minus", "selector_exact", "selector_plus"};
    for (int i = 0; i < 3; ++i) {
        double P_bar = P_bar_exact * (1.0 + deltas[i]);
        double P_cgs = P_bar * 1e6;
        EOS* eos = find_phase_HHe_tabulated(P_cgs, T);
        if (!eos) {
            std::cerr << "Error: find_phase_HHe_tabulated returned NULL for P_bar=" << P_bar << std::endl;
            return 1;
        }
        rho_guess = -1.0;
        double rho = eos->density(P_cgs, T, rho_guess);
        if (!std::isfinite(rho)) {
            std::cerr << "Error: nonfinite density for selector row" << std::endl;
            return 1;
        }
        rho_guess = rho;
        double dTdP = eos->dTdP_S(P_bar * 1e-4, T, rho_guess);
        double mmol = eos->getmmol();
        int thermal = eos->thermal_code();
        bool domain = eos->table_domain_contains(P_cgs, T);
        out << kinds[i] << "," << fmt17(P_bar) << "," << fmt17(T) << "," << eos->audit_id()
            << "," << fmt17(rho) << "," << fmt17(dTdP) << "," << fmt17(mmol) << ","
            << thermal << "," << (domain ? "true" : "false") << "\n";
    }

    out.close();
    return 0;
}

// Mode 3: --check <model.dat> <rows.csv>
int check_mode(const std::string& model_path, const std::string& output_csv) {
    std::ifstream check(output_csv.c_str());
    if (check.good()) {
        std::cerr << "Error: check output file already exists: " << output_csv << std::endl;
        return 1;
    }
    check.close();

    gsl_set_error_handler_off();
    configure_prescribed_hhe_audit();

    std::ifstream in(model_path.c_str());
    if (!in) {
        std::cerr << "Error: cannot open model file: " << model_path << std::endl;
        return 1;
    }

    // Read first line as header (required)
    std::string header_line;
    if (!std::getline(in, header_line)) {
        std::cerr << "Error: model.dat is empty" << std::endl;
        return 1;
    }

    // Parse each subsequent nonempty line
    std::vector<std::vector<std::string> > tokens;
    std::string line;
    while (std::getline(in, line)) {
        // Trim whitespace
        size_t start = line.find_first_not_of(" \t\r\n");
        if (start == std::string::npos) continue;
        size_t end = line.find_last_not_of(" \t\r\n");
        std::string trimmed = line.substr(start, end - start + 1);
        if (trimmed.empty()) continue;
        std::istringstream iss(trimmed);
        std::vector<std::string> row;
        std::string token;
        while (iss >> token) row.push_back(token);
        tokens.push_back(row);
    }
    in.close();

    if (tokens.empty()) {
        std::cerr << "Error: no data rows found in model.dat" << std::endl;
        return 1;
    }

    std::ofstream out(output_csv.c_str());
    if (!out) {
        std::cerr << "Error: cannot open output file: " << output_csv << std::endl;
        return 1;
    }
    out << "index,R_earth,P_GPa,M_earth,rho_saved,rho_evaluated,T_K,eos_id,table_domain_contains,gas_selector_id,dTdP_K_per_GPa\n";

    for (size_t i = 0; i < tokens.size(); ++i) {
        const std::vector<std::string>& row = tokens[i];
        if (row.size() < 7) {
            std::cerr << "Error: row " << i+1 << " has fewer than 7 columns (6 numeric + label)" << std::endl;
            return 1;
        }

        // Parse exactly 6 numeric fields; require full token consumed
        double index, R, P_GPa, M, rho_saved, T;
        char* endp = NULL;
        index = strtod(row[0].c_str(), &endp);
        if (endp == row[0].c_str() || *endp != '\0' || !std::isfinite(index)) {
            std::cerr << "Invalid index at row " << i+1 << std::endl;
            return 1;
        }
        R = strtod(row[1].c_str(), &endp);
        if (endp == row[1].c_str() || *endp != '\0' || !std::isfinite(R)) {
            std::cerr << "Invalid R at row " << i+1 << std::endl;
            return 1;
        }
        P_GPa = strtod(row[2].c_str(), &endp);
        if (endp == row[2].c_str() || *endp != '\0' || !std::isfinite(P_GPa)) {
            std::cerr << "Invalid P at row " << i+1 << std::endl;
            return 1;
        }
        M = strtod(row[3].c_str(), &endp);
        if (endp == row[3].c_str() || *endp != '\0' || !std::isfinite(M)) {
            std::cerr << "Invalid M at row " << i+1 << std::endl;
            return 1;
        }
        rho_saved = strtod(row[4].c_str(), &endp);
        if (endp == row[4].c_str() || *endp != '\0' || !std::isfinite(rho_saved)) {
            std::cerr << "Invalid rho at row " << i+1 << std::endl;
            return 1;
        }
        T = strtod(row[5].c_str(), &endp);
        if (endp == row[5].c_str() || *endp != '\0' || !std::isfinite(T)) {
            std::cerr << "Invalid T at row " << i+1 << std::endl;
            return 1;
        }

        // Remaining columns joined as phase label
        std::string phase_label;
        for (size_t j = 6; j < row.size(); ++j) {
            if (j > 6) phase_label += " ";
            phase_label += row[j];
        }
        // Trim again
        size_t pstart = phase_label.find_first_not_of(" \t");
        size_t pend = phase_label.find_last_not_of(" \t");
        if (pstart == std::string::npos) phase_label = "";
        else phase_label = phase_label.substr(pstart, pend - pstart + 1);
        if (phase_label.empty()) {
            std::cerr << "Error: empty phase label at row " << i+1 << std::endl;
            return 1;
        }

        // Find EOS by exact full phase label
        EOS* eos = NULL;
        try {
            eos = find_eos_by_label(phase_label);
        } catch (const std::exception& e) {
            std::cerr << "Error: " << e.what() << " at row " << i+1 << std::endl;
            return 1;
        }

        // Evaluate density at stored P/T
        double P_cgs = P_GPa * 1e10; // 1 GPa = 1e10 dyn/cm^2
        double rho_guess = rho_saved;
        double rho_eval = eos->density(P_cgs, T, rho_guess);
        if (!std::isfinite(rho_eval)) {
            std::cerr << "Error: nonfinite reevaluated density for row " << i+1 << std::endl;
            return 1;
        }

        // Determine if gas pointer
        bool is_gas = (eos == Gas_iso || eos == Gas_hhe);
        bool domain = eos->table_domain_contains(P_cgs, T);
        std::string gas_selector_id = "";
        double dTdP = 0.0;
        if (is_gas) {
            EOS* selector = find_phase_HHe_tabulated(P_cgs, T);
            if (selector) {
                gas_selector_id = selector->audit_id();
            } else {
                // If selector returns NULL, still output blank (could indicate problem)
            }
            rho_guess = rho_saved;
            dTdP = eos->dTdP_S(P_GPa, T, rho_guess); // P in GPa
            if (!std::isfinite(dTdP)) {
                std::cerr << "Error: nonfinite dTdP for gas row " << i+1 << std::endl;
                return 1;
            }
        }

        out << fmt17(index) << "," << fmt17(R) << "," << fmt17(P_GPa) << "," << fmt17(M)
            << "," << fmt17(rho_saved) << "," << fmt17(rho_eval) << "," << fmt17(T)
            << "," << eos->audit_id() << "," << (domain ? "true" : "false")
            << "," << gas_selector_id << "," << (is_gas ? fmt17(dTdP) : "") << "\n";
    }

    out.close();
    return 0;
}

int main(int argc, char** argv) {
    try {
        if (argc < 2) {
            std::cerr << "Usage:\n  native_audit --run <config.cfg> <runtime.json>\n  native_audit --probe <probe.csv>\n  native_audit --check <model.dat> <rows.csv>\n";
            return 1;
        }
        std::string mode = argv[1];
        if (mode == "--run") {
            if (argc != 4) {
                std::cerr << "Error: --run requires exactly 2 arguments (config, runtime.json)" << std::endl;
                return 1;
            }
            return run_mode(argv[2], argv[3]);
        } else if (mode == "--probe") {
            if (argc != 3) {
                std::cerr << "Error: --probe requires 1 argument (output csv)" << std::endl;
                return 1;
            }
            return probe_mode(argv[2]);
        } else if (mode == "--check") {
            if (argc != 4) {
                std::cerr << "Error: --check requires 2 arguments (model.dat, rows.csv)" << std::endl;
                return 1;
            }
            return check_mode(argv[2], argv[3]);
        } else {
            std::cerr << "Error: unknown mode " << mode << std::endl;
            return 1;
        }
    } catch (const std::exception& e) {
        std::cerr << "Fatal error: " << e.what() << std::endl;
        return 1;
    }
}