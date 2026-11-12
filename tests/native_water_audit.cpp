#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <map>
#include <set>
#include <stdexcept>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <gsl/gsl_errno.h>

// Avoid macro conflicts: include native headers and rename main
#define main magrathea_native_main
#include "src/main.cpp"
#undef main

// Forward declaration from phase.h
void configure_prescribed_hhe_audit();

// Helper: escape a string for CSV (RFC4180)
std::string csv_escape(const std::string& s) {
    bool needs_quotes = false;
    for (size_t i = 0; i < s.size(); ++i) {
        char c = s[i];
        if (c == ',' || c == '"' || c == '\n' || c == '\r') {
            needs_quotes = true;
            break;
        }
    }
    if (!needs_quotes) return s;
    std::string out = "\"";
    for (size_t i = 0; i < s.size(); ++i) {
        char c = s[i];
        if (c == '"') out += "\"\"";
        else out += c;
    }
    out += "\"";
    return out;
}

// Helper: format a double with 17 significant digits
std::string fmt17(double x) {
    if (std::isnan(x)) return "nan";
    if (std::isinf(x)) return (x > 0 ? "inf" : "-inf");
    char buf[64];
    snprintf(buf, sizeof(buf), "%.17g", x);
    return std::string(buf);
}

// Helper: parse a double, return false on failure
bool parse_double(const std::string& s, double& out) {
    if (s.empty()) return false;
    char* end = NULL;
    errno = 0;
    out = strtod(s.c_str(), &end);
    if (errno != 0 || end != s.c_str() + s.size()) return false;
    return true;
}

// Helper: split a line by comma, respecting quotes (RFC4180)
bool split_csv_line(const std::string& line, std::vector<std::string>& fields) {
    fields.clear();
    std::string cur;
    bool in_quotes = false;
    for (size_t i = 0; i < line.size(); ++i) {
        char c = line[i];
        if (in_quotes) {
            if (c == '"') {
                if (i + 1 < line.size() && line[i+1] == '"') {
                    cur += '"';
                    ++i;
                } else {
                    in_quotes = false;
                }
            } else {
                cur += c;
            }
        } else {
            if (c == '"') {
                in_quotes = true;
            } else if (c == ',') {
                fields.push_back(cur);
                cur.clear();
            } else {
                cur += c;
            }
        }
    }
    if (in_quotes) return false; // unterminated quote
    fields.push_back(cur);
    return true;
}

// Helper: trim whitespace from both ends
std::string trim(const std::string& s) {
    size_t start = s.find_first_not_of(" \t\r\n");
    if (start == std::string::npos) return "";
    size_t end = s.find_last_not_of(" \t\r\n");
    return s.substr(start, end - start + 1);
}

// Registry of known phase labels to EOS pointers (deduplicated)
static std::map<std::string, EOS*> build_label_registry() {
    std::map<std::string, EOS*> reg;
    // Water-related
    reg["Water_SF"] = Water_SF;
    reg["Water_Brown"] = Water_Brown;
    reg["Water_IAPWS"] = Water_IAPWS;
    reg["Water_Vap_IAPWS"] = Water_Vap_IAPWS;
    reg["Water_sc_Mazevet"] = Water_sc_Mazevet;
    reg["IceIh_SF"] = IceIh_SF;
    reg["IceII_SF"] = IceII_SF;
    reg["IceIII_SF"] = IceIII_SF;
    reg["IceV_SF"] = IceV_SF;
    reg["IceVI_SF"] = IceVI_SF;
    reg["IceVII_Bezacier"] = IceVII_Bezacier;
    reg["IceVII_Fei"] = IceVII_Fei;
    reg["IceX"] = IceX;
    reg["vdW_H2O"] = vdW_H2O;
    reg["vdW_H2O_iso"] = vdW_H2O_iso;
    reg["vdW_H2O_lo"] = vdW_H2O_lo;
    reg["vdW_H2O_hi"] = vdW_H2O_hi;
    reg["H2O_AQUA"] = H2O_AQUA;
    // Fe phases
    reg["Fe_hcp"] = Fe_hcp;
    reg["Fe_liquid"] = Fe_liquid;
    reg["Fe_liquid2"] = Fe_liquid2;
    reg["Fe_fcc"] = Fe_fcc;
    reg["Fe_bcc"] = Fe_bcc;
    reg["Fe_hcp2"] = Fe_hcp2;
    reg["Fe_hcp3"] = Fe_hcp3;
    // Silicate phases
    reg["Si_Pv_Shim"] = Si_Pv_Shim;
    reg["Si_Pv"] = Si_Pv;
    reg["Si_PPv"] = Si_PPv;
    reg["Si_PPv_Sakai"] = Si_PPv_Sakai;
    reg["Si_Dummy"] = Si_Dummy;
    reg["Si_Liquid_Wolf"] = Si_Liquid_Wolf;
    reg["Fo"] = Fo;
    reg["Wds"] = Wds;
    reg["Rwd"] = Rwd;
    reg["Akm"] = Akm;
    reg["Pv_Doro"] = Pv_Doro;
    reg["PPv_Doro"] = PPv_Doro;
    reg["Fo_Sotin"] = Fo_Sotin;
    reg["En"] = En;
    reg["Mw"] = Mw;
    // Gas phases
    reg["Gas_hhe"] = Gas_hhe;
    reg["Gas_hhe_iso100"] = Gas_hhe_iso100;
    // Check for duplicate labels mapping to different pointers
    std::map<EOS*, std::string> ptr_to_label;
    for (std::map<std::string, EOS*>::iterator it = reg.begin(); it != reg.end(); ++it) {
        EOS* ptr = it->second;
        if (ptr_to_label.find(ptr) != ptr_to_label.end()) {
            throw std::runtime_error("Duplicate label mapping to same EOS pointer: " + ptr_to_label[ptr] + " and " + it->first);
        }
        ptr_to_label[ptr] = it->first;
    }
    return reg;
}

// Resolve EOS pointer by requested ID (for --query)
static EOS* resolve_query_eos(const std::string& id, double P_GPa, double T_K) {
    if (id == "water_default") {
        return find_phase_water_default(P_GPa * 1e10, T_K);
    } else if (id == "water_tabulated") {
        return find_phase_water_tabulated(P_GPa * 1e10, T_K);
    } else {
        // Direct lookup in registry
        static std::map<std::string, EOS*> reg = build_label_registry();
        std::map<std::string, EOS*>::const_iterator it = reg.find(id);
        if (it == reg.end()) return NULL;
        return it->second;
    }
}

// Resolve EOS pointer by exact phase label (for --profile)
static EOS* resolve_profile_eos(const std::string& label) {
    static std::map<std::string, EOS*> reg = build_label_registry();
    std::set<EOS*> matches;
    for (std::map<std::string, EOS*>::const_iterator it = reg.begin(); it != reg.end(); ++it) {
        EOS* eos = it->second;
        if (eos && eos->getEOS() == label) {
            matches.insert(eos);
        }
    }
    if (matches.empty()) return NULL;
    if (matches.size() > 1) {
        throw std::runtime_error("Ambiguous profile label: " + label);
    }
    return *matches.begin();
}

// Check if a file exists
bool file_exists(const std::string& path) {
    std::ifstream f(path.c_str());
    return f.good();
}

// Mode: --query INPUT.csv OUTPUT.csv
int query_mode(const std::string& input_path, const std::string& output_path) {
    // Refuse overwrite
    if (file_exists(output_path)) {
        std::cerr << "Error: output file already exists: " << output_path << std::endl;
        return 1;
    }

    gsl_set_error_handler_off();
    configure_prescribed_hhe_audit();
    Water_sc_Mazevet->modify_dTdP(dTdP_S_H2OSC);

    std::ifstream in(input_path.c_str());
    if (!in) {
        std::cerr << "Error: cannot open input file: " << input_path << std::endl;
        return 1;
    }

    std::ofstream out(output_path.c_str());
    if (!out) {
        std::cerr << "Error: cannot open output file: " << output_path << std::endl;
        return 1;
    }

    // Write header
    out << "case_id,P_GPa,T_K,requested_id,selected_id,phase,domain,thermal_code,rho_g_cm3,dTdP_K_per_GPa,nabla,rejected_delta\n";

    std::string line;
    unsigned long long line_no = 0;
    unsigned long long rejected_total = 0;
    unsigned long long data_row_count = 0;
    bool header_parsed = false;
    while (std::getline(in, line)) {
        ++line_no;
        // Allow CRLF: remove trailing \r
        if (!line.empty() && line[line.size()-1] == '\r') line.erase(line.size()-1);
        // Skip empty lines
        if (line.empty()) continue;

        if (!header_parsed) {
            // First non-empty line must be header
            if (line != "case_id,P_GPa,T_K,eos_id") {
                std::cerr << "Error: invalid header on line " << line_no << std::endl;
                return 1;
            }
            header_parsed = true;
            continue;
        }

        // Reject any quotes in raw line before parsing (simple unquoted CSV)
        if (line.find('"') != std::string::npos) {
            std::cerr << "Error: quotes not allowed in line " << line_no << std::endl;
            return 1;
        }

        // Parse data line: simple comma-separated, no quotes allowed
        std::vector<std::string> fields;
        if (!split_csv_line(line, fields)) {
            std::cerr << "Error: malformed CSV line " << line_no << std::endl;
            return 1;
        }
        if (fields.size() != 4) {
            std::cerr << "Error: line " << line_no << " has " << fields.size() << " fields, expected 4" << std::endl;
            return 1;
        }

        // Trim fields
        for (size_t i = 0; i < fields.size(); ++i) fields[i] = trim(fields[i]);

        // Reject any quotes in fields (simple unquoted CSV)
        for (size_t i = 0; i < fields.size(); ++i) {
            if (fields[i].find('"') != std::string::npos) {
                std::cerr << "Error: quotes not allowed in field " << i+1 << " on line " << line_no << std::endl;
                return 1;
            }
        }

        // Parse case_id (non-empty string)
        std::string case_id = fields[0];
        if (case_id.empty()) {
            std::cerr << "Error: empty case_id on line " << line_no << std::endl;
            return 1;
        }
        // Parse P_GPa
        double P_GPa;
        if (!parse_double(fields[1], P_GPa) || !std::isfinite(P_GPa) || P_GPa <= 0.0) {
            std::cerr << "Error: invalid P_GPa on line " << line_no << std::endl;
            return 1;
        }
        // Parse T_K
        double T_K;
        if (!parse_double(fields[2], T_K) || !std::isfinite(T_K) || T_K <= 0.0) {
            std::cerr << "Error: invalid T_K on line " << line_no << std::endl;
            return 1;
        }
        // Parse eos_id
        std::string eos_id = fields[3];
        if (eos_id.empty()) {
            std::cerr << "Error: empty eos_id on line " << line_no << std::endl;
            return 1;
        }

        // Resolve EOS pointer
        EOS* eos = resolve_query_eos(eos_id, P_GPa, T_K);
        if (eos == NULL) {
            std::cerr << "Error: unknown eos_id '" << eos_id << "' on line " << line_no << std::endl;
            return 1;
        }

        // Convert pressure to cgs (microbar)
        double P_cgs = P_GPa * 1e10;
        double T = T_K;

        // Check domain
        bool domain = eos->table_domain_contains(P_cgs, T);
        double rho = std::numeric_limits<double>::quiet_NaN();
        double dTdP = std::numeric_limits<double>::quiet_NaN();
        double nabla = std::numeric_limits<double>::quiet_NaN();
        unsigned long long rejected_before = EOS::rejected_table_queries();

        if (domain) {
            // Compute density
            double rho_guess = -1.0;
            rho = eos->density(P_cgs, T, rho_guess);
            if (!std::isfinite(rho)) {
                rho = std::numeric_limits<double>::quiet_NaN();
            }

            // Compute gradient based on thermal_code
            int tc = eos->thermal_code();
            if (tc == 0) {
                dTdP = 0.0;
            } else if (tc == 2) {
                // external callback: dTdP(Pcgs,T,rho) returns K/microbar, convert to K/GPa
                if (eos->dTdP != NULL) {
                    double rho_guess2 = rho; // use computed rho as guess
                    double val = eos->dTdP(P_cgs, T, rho_guess2);
                    if (std::isfinite(val)) {
                        dTdP = val * 1e10; // K/microbar -> K/GPa
                    } else {
                        dTdP = std::numeric_limits<double>::quiet_NaN();
                    }
                } else {
                    dTdP = std::numeric_limits<double>::quiet_NaN();
                }
            } else {
                // other codes: use dTdP_S(Pgpa,T,rhoguess) returns K/GPa
                double rho_guess2 = rho; // use computed rho as guess
                double val = eos->dTdP_S(P_GPa, T, rho_guess2);
                if (std::isfinite(val)) {
                    dTdP = val;
                } else {
                    dTdP = std::numeric_limits<double>::quiet_NaN();
                }
            }

            // Compute nabla = P/T * dTdP
            if (std::isfinite(dTdP)) {
                nabla = (P_GPa / T) * dTdP;
            }
        }

        unsigned long long rejected_after = EOS::rejected_table_queries();
        unsigned long long rejected_delta = rejected_after - rejected_before;
        rejected_total += rejected_delta;

        // Determine selected_id: use audit_id()
        std::string selected_id = eos->audit_id();

        ++data_row_count;

        // Write row
        out << csv_escape(case_id) << ","
            << fmt17(P_GPa) << ","
            << fmt17(T_K) << ","
            << csv_escape(eos_id) << ","
            << csv_escape(selected_id) << ","
            << csv_escape(eos->getEOS()) << ","
            << (domain ? "true" : "false") << ","
            << eos->thermal_code() << ","
            << fmt17(rho) << ","
            << fmt17(dTdP) << ","
            << fmt17(nabla) << ","
            << rejected_delta << "\n";
    }

    if (!header_parsed) {
        std::cerr << "Error: no header found in input file" << std::endl;
        return 1;
    }

    if (data_row_count == 0) {
        std::cerr << "Error: no data rows found in input file" << std::endl;
        return 1;
    }

    out.close();
    if (!out) {
        std::cerr << "Error: failed to write output file completely" << std::endl;
        return 1;
    }

    return 0;
}

// Mode: --profile INPUT.dat OUTPUT.csv
int profile_mode(const std::string& input_path, const std::string& output_path) {
    // Refuse overwrite
    if (file_exists(output_path)) {
        std::cerr << "Error: output file already exists: " << output_path << std::endl;
        return 1;
    }

    gsl_set_error_handler_off();
    configure_prescribed_hhe_audit();
    Water_sc_Mazevet->modify_dTdP(dTdP_S_H2OSC);

    std::ifstream in(input_path.c_str());
    if (!in) {
        std::cerr << "Error: cannot open input file: " << input_path << std::endl;
        return 1;
    }

    std::ofstream out(output_path.c_str());
    if (!out) {
        std::cerr << "Error: cannot open output file: " << output_path << std::endl;
        return 1;
    }

    // Write header
    out << "index,R_RE,P_GPa,M_ME,T_K,rho_saved,rho_recomputed,rho_relerr,phase,selected_id,domain,thermal_code,dTdP_K_per_GPa,nabla,rejected_delta\n";

    std::string line;
    unsigned long long line_no = 0;
    bool header_parsed = false;
    unsigned long long rejected_total = 0;
    unsigned long long data_row_count = 0;
    while (std::getline(in, line)) {
        ++line_no;
        // Allow CRLF: remove trailing \r
        if (!line.empty() && line[line.size()-1] == '\r') line.erase(line.size()-1);
        // Skip empty lines
        if (line.empty()) continue;

        if (!header_parsed) {
            // First non-empty line must be header
            std::istringstream header_stream(line);
            std::string first_token;
            if (!(header_stream >> first_token) || first_token != "Index") {
                std::cerr << "Error: invalid header on line " << line_no << std::endl;
                return 1;
            }
            header_parsed = true;
            continue;
        }
        ++data_row_count;

        // Parse data line: whitespace-delimited, six numeric fields then phase label (may contain spaces)
        // Use istringstream and getline to split by whitespace, but we need to preserve the remainder as label.
        // We'll read the line into a stringstream and extract six numeric values, then the rest of the line is the label.
        std::istringstream iss(line);
        double index_d, R_RE, P_GPa, M_ME, rho_saved, T_K;
        if (!(iss >> index_d >> R_RE >> P_GPa >> M_ME >> rho_saved >> T_K)) {
            std::cerr << "Error: malformed line " << line_no << " (cannot read six numeric fields)" << std::endl;
            return 1;
        }
        // Validate numeric fields
        if (!std::isfinite(index_d) || index_d < 0.0 || std::floor(index_d) != index_d) {
            std::cerr << "Error: invalid index on line " << line_no << std::endl;
            return 1;
        }
        if (!std::isfinite(R_RE) || R_RE < 0.0) {
            std::cerr << "Error: invalid R_RE on line " << line_no << std::endl;
            return 1;
        }
        if (!std::isfinite(P_GPa) || P_GPa <= 0.0) {
            std::cerr << "Error: invalid P_GPa on line " << line_no << std::endl;
            return 1;
        }
        if (!std::isfinite(M_ME) || M_ME < 0.0) {
            std::cerr << "Error: invalid M_ME on line " << line_no << std::endl;
            return 1;
        }
        if (!std::isfinite(rho_saved) || rho_saved <= 0.0) {
            std::cerr << "Error: invalid rho_saved on line " << line_no << std::endl;
            return 1;
        }
        if (!std::isfinite(T_K) || T_K <= 0.0) {
            std::cerr << "Error: invalid T_K on line " << line_no << std::endl;
            return 1;
        }

        // The remainder of the line is the phase label; trim edges only.
        std::string phase_label;
        std::getline(iss, phase_label);
        phase_label = trim(phase_label);
        if (phase_label.empty()) {
            std::cerr << "Error: empty phase label on line " << line_no << std::endl;
            return 1;
        }

        // Resolve EOS pointer by exact label
        EOS* eos = resolve_profile_eos(phase_label);
        if (eos == NULL) {
            std::cerr << "Error: unknown phase label '" << phase_label << "' on line " << line_no << std::endl;
            return 1;
        }

        // Convert pressure to cgs
        double P_cgs = P_GPa * 1e10;
        double T = T_K;

        // Check domain
        bool domain = eos->table_domain_contains(P_cgs, T);
        double rho_recomputed = std::numeric_limits<double>::quiet_NaN();
        double rho_relerr = std::numeric_limits<double>::quiet_NaN();
        double dTdP = std::numeric_limits<double>::quiet_NaN();
        double nabla = std::numeric_limits<double>::quiet_NaN();
        unsigned long long rejected_before = EOS::rejected_table_queries();

        if (domain) {
            double rho_guess = rho_saved; // use saved density as initial guess
            rho_recomputed = eos->density(P_cgs, T, rho_guess);
            if (std::isfinite(rho_recomputed) && std::isfinite(rho_saved) && rho_saved != 0.0) {
                rho_relerr = (rho_recomputed - rho_saved) / rho_saved;
            }

            int tc = eos->thermal_code();
            if (tc == 0) {
                dTdP = 0.0;
            } else if (tc == 2) {
                if (eos->dTdP != NULL) {
                    double rho_guess2 = rho_recomputed;
                    double val = eos->dTdP(P_cgs, T, rho_guess2);
                    if (std::isfinite(val)) {
                        dTdP = val * 1e10;
                    } else {
                        dTdP = std::numeric_limits<double>::quiet_NaN();
                    }
                } else {
                    dTdP = std::numeric_limits<double>::quiet_NaN();
                }
            } else {
                double rho_guess2 = rho_recomputed;
                double val = eos->dTdP_S(P_GPa, T, rho_guess2);
                if (std::isfinite(val)) {
                    dTdP = val;
                } else {
                    dTdP = std::numeric_limits<double>::quiet_NaN();
                }
            }

            if (std::isfinite(dTdP)) {
                nabla = (P_GPa / T) * dTdP;
            }
        }

        unsigned long long rejected_after = EOS::rejected_table_queries();
        unsigned long long rejected_delta = rejected_after - rejected_before;
        rejected_total += rejected_delta;

        // selected_id: use audit_id()
        std::string selected_id = eos->audit_id();

        // Write row
        out << fmt17(index_d) << ","
            << fmt17(R_RE) << ","
            << fmt17(P_GPa) << ","
            << fmt17(M_ME) << ","
            << fmt17(T_K) << ","
            << fmt17(rho_saved) << ","
            << fmt17(rho_recomputed) << ","
            << fmt17(rho_relerr) << ","
            << csv_escape(phase_label) << ","
            << csv_escape(selected_id) << ","
            << (domain ? "true" : "false") << ","
            << eos->thermal_code() << ","
            << fmt17(dTdP) << ","
            << fmt17(nabla) << ","
            << rejected_delta << "\n";
    }

    if (!header_parsed) {
        std::cerr << "Error: no header found in input file" << std::endl;
        return 1;
    }

    // Ensure at least one data row was processed
    if (data_row_count == 0) {
        std::cerr << "Error: no data rows found in input file" << std::endl;
        return 1;
    }

    out.close();
    if (!out) {
        std::cerr << "Error: failed to write output file completely" << std::endl;
        return 1;
    }

    return 0;
}

int main(int argc, char** argv) {
    try {
        if (argc != 4) {
            std::cerr << "Usage: " << argv[0] << " --query INPUT.csv OUTPUT.csv\n";
            std::cerr << "       " << argv[0] << " --profile INPUT.dat OUTPUT.csv\n";
            return 1;
        }

        std::string mode = argv[1];
        if (mode == "--query") {
            return query_mode(argv[2], argv[3]);
        } else if (mode == "--profile") {
            return profile_mode(argv[2], argv[3]);
        } else {
            std::cerr << "Error: unknown mode '" << mode << "'" << std::endl;
            return 1;
        }
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
}
