#include "EOS.h"
#include "tp_profile.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>

static bool parse_double(const char* s, double& v) {
    if (!s || !*s) return false;
    char* end = nullptr;
    v = std::strtod(s, &end);
    return end != s && *end == '\0' && std::isfinite(v) && v > 0.0;
}

int main(int argc, char** argv) {
    if (argc != 5) { std::cerr << "usage: extend_tp input.csv output.csv Pmax_bar max_dlnP\n"; return 1; }
    double Pmax_bar, max_dlnP;
    if (!parse_double(argv[3], Pmax_bar) || !parse_double(argv[4], max_dlnP)) { std::cerr << "bad numeric arg\n"; return 1; }
    if (max_dlnP < 1e-5 || max_dlnP > 0.05) { std::cerr << "max_dlnP out of range\n"; return 1; }

    TPProfile prof = TPProfile::load_csv(argv[1]);
    double join_P_cgs = prof.max_pressure_cgs();
    double join_P_bar = join_P_cgs * 1e-6;
    if (Pmax_bar <= join_P_bar) { std::cerr << "Pmax <= join\n"; return 1; }
    double join_T = prof.at_cgs(join_P_cgs).temperature_K;

    std::ifstream in(argv[1], std::ios::binary);
    if (!in) { std::cerr << "cannot read input\n"; return 1; }
    std::ostringstream orig;
    orig << in.rdbuf();
    in.close();
    std::string prefix = orig.str();
    if (!prefix.empty() && prefix.back() != '\n') prefix += '\n';

    const std::string tablepath = "./tabulated/ChabrierHHe0275.txt";
    EOS eos("ChabrierHHe0275", tablepath);

    double P_GPa_join = join_P_cgs * 1e-10;
    double P_GPa_max = Pmax_bar * 1e-4;
    double x_join = std::log(P_GPa_join);
    double x_max = std::log(P_GPa_max);
    double T = join_T;
    double rho = 0.0;

    double P_cgs_check = P_GPa_join * 1e10;
    if (!eos.table_domain_contains(P_cgs_check, T)) { std::cerr << "join outside domain\n"; return 1; }
    rho = eos.density(P_cgs_check, T, rho);
    if (!std::isfinite(rho) || rho <= 0.0) { std::cerr << "bad join density\n"; return 1; }
    double slope = eos.dTdP_S(P_GPa_join, T, rho);
    if (!std::isfinite(slope) || slope <= 0.0) { std::cerr << "bad join slope\n"; return 1; }

    std::ostringstream rows;
    rows.precision(17);
    double x = x_join;
    double h = max_dlnP;
    int count = 0;
    const int max_steps = 200000;

    while (x < x_max - 1e-15) {
        if (count >= max_steps) { std::cerr << "too many steps\n"; return 1; }
        double step = h;
        if (x + step > x_max) step = x_max - x;
        double x0 = x, xh = x + step * 0.5, x1 = x + step;
        double P0 = std::exp(x0), Ph = std::exp(xh), P1 = std::exp(x1);
        double T0 = T, Th, T1;
        double rho0 = rho, rhoh, rho1;

        double Pcgs0 = P0 * 1e10;
        if (!eos.table_domain_contains(Pcgs0, T0)) { std::cerr << "domain fail k1\n"; return 1; }
        rho0 = eos.density(Pcgs0, T0, rho0);
        if (!std::isfinite(rho0) || rho0 <= 0.0) { std::cerr << "rho fail k1\n"; return 1; }
        double k1 = P0 * eos.dTdP_S(P0, T0, rho0);
        if (!std::isfinite(k1) || k1 <= 0.0) { std::cerr << "slope fail k1\n"; return 1; }

        Th = T0 + step * 0.5 * k1;
        double Pcgsh = Ph * 1e10;
        if (!eos.table_domain_contains(Pcgsh, Th)) { std::cerr << "domain fail k2\n"; return 1; }
        rhoh = eos.density(Pcgsh, Th, rho0);
        if (!std::isfinite(rhoh) || rhoh <= 0.0) { std::cerr << "rho fail k2\n"; return 1; }
        double k2 = Ph * eos.dTdP_S(Ph, Th, rhoh);
        if (!std::isfinite(k2) || k2 <= 0.0) { std::cerr << "slope fail k2\n"; return 1; }

        Th = T0 + step * 0.5 * k2;
        if (!eos.table_domain_contains(Pcgsh, Th)) { std::cerr << "domain fail k3\n"; return 1; }
        rhoh = eos.density(Pcgsh, Th, rhoh);
        if (!std::isfinite(rhoh) || rhoh <= 0.0) { std::cerr << "rho fail k3\n"; return 1; }
        double k3 = Ph * eos.dTdP_S(Ph, Th, rhoh);
        if (!std::isfinite(k3) || k3 <= 0.0) { std::cerr << "slope fail k3\n"; return 1; }

        T1 = T0 + step * k3;
        double Pcgs1 = P1 * 1e10;
        if (!eos.table_domain_contains(Pcgs1, T1)) { std::cerr << "domain fail k4\n"; return 1; }
        rho1 = eos.density(Pcgs1, T1, rhoh);
        if (!std::isfinite(rho1) || rho1 <= 0.0) { std::cerr << "rho fail k4\n"; return 1; }
        double k4 = P1 * eos.dTdP_S(P1, T1, rho1);
        if (!std::isfinite(k4) || k4 <= 0.0) { std::cerr << "slope fail k4\n"; return 1; }

        T = T0 + step / 6.0 * (k1 + 2.0 * k2 + 2.0 * k3 + k4);
        x = x1;
        rho = rho1;
        if (!std::isfinite(T) || T <= 0.0) { std::cerr << "T invalid\n"; return 1; }
        if (!eos.table_domain_contains(Pcgs1, T)) { std::cerr << "endpoint domain fail\n"; return 1; }
        double rho_check = eos.density(Pcgs1, T, rho);
        if (!std::isfinite(rho_check) || rho_check <= 0.0) { std::cerr << "endpoint rho fail\n"; return 1; }
        double slope_check = eos.dTdP_S(P1, T, rho_check);
        if (!std::isfinite(slope_check) || slope_check <= 0.0) { std::cerr << "endpoint slope fail\n"; return 1; }
        rho = rho_check;
        rows << (P1 * 1e4) << ',' << T << '\n';
        ++count;
    }

    if (std::fabs(x - x_max) > 1e-12) { std::cerr << "did not reach Pmax\n"; return 1; }
    double final_P_bar = std::exp(x_max) * 1e4;
    if (std::fabs(final_P_bar - Pmax_bar) > 1e-6 * Pmax_bar) { std::cerr << "final pressure mismatch\n"; return 1; }

    int fd = open(argv[2], O_WRONLY | O_CREAT | O_EXCL, 0644);
    if (fd < 0) { std::cerr << "output exists or cannot create\n"; return 1; }
    FILE* f = fdopen(fd, "w");
    if (!f) { close(fd); std::cerr << "fdopen failed\n"; return 1; }
    fwrite(prefix.data(), 1, prefix.size(), f);
    fwrite(rows.str().data(), 1, rows.str().size(), f);
    fclose(f);

    std::cout << "TEST_CONDITIONAL_HHE_ADIABATIC_EXTENSION "
              << join_P_bar << ' ' << join_T << ' ' << Pmax_bar << ' '
              << max_dlnP << ' ' << count << ' ' << tablepath << '\n';
    return 0;
}
