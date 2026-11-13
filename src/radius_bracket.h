#ifndef RADIUS_BRACKET_H
#define RADIUS_BRACKET_H

#include <algorithm>
#include <cmath>
#include <exception>
#include <functional>
#include <limits>
#include <string>
#include <utility>
#include <vector>

struct RadiusSample {
    double radius;
    double value;
    bool valid;
};

struct RadiusBracket {
    bool found = false;
    bool ambiguous = false;
    double lo = 0.0;
    double hi = 0.0;
    int trials = 0;
    std::string reason;
    std::vector<RadiusSample> samples;
};

inline RadiusBracket find_radius_bracket(const std::function<double(double)>& eval, double guess, int cap = 12) {
    RadiusBracket result;
    if (!std::isfinite(guess) || guess <= 0.0 || cap < 1) {
        result.reason = "invalid guess or cap";
        return result;
    }

    const double initial_factors[] = {0.8, 0.9, 1.0, 1.1, 1.2};
    std::vector<double> radii;
    for (double f : initial_factors) {
        double r = guess * f;
        if (r > 0.0 && std::isfinite(r)) {
            radii.push_back(r);
        }
    }
    // Remove duplicates (if any)
    std::sort(radii.begin(), radii.end());
    radii.erase(std::unique(radii.begin(), radii.end()), radii.end());

    // Probe initial radii up to cap
    for (double r : radii) {
        if (result.trials >= cap) break;
        double val = 0.0;
        bool valid = false;
        try {
            val = eval(r);
            valid = std::isfinite(val);
        } catch (...) {
            valid = false;
        }
        result.samples.push_back({r, val, valid});
        ++result.trials;
    }

    // Helper to sort samples by radius
    auto sort_samples = [&]() {
        std::sort(result.samples.begin(), result.samples.end(),
                  [](const RadiusSample& a, const RadiusSample& b) { return a.radius < b.radius; });
    };

    // Main loop
    int extension_step = 0;
    int global_extension_step = 0;
    while (true) {
        sort_samples();

        // Count valid samples with value == 0
        int zero_count = 0;
        for (const auto& s : result.samples) {
            if (s.valid && s.value == 0.0) ++zero_count;
        }
        if (zero_count >= 2) {
            result.ambiguous = true;
            result.reason = "multiple known exact roots";
            return result;
        }

        // Collect strict opposite sign brackets between adjacent valid samples, ignoring zeros
        struct Bracket {
            double lo, hi;
        };
        std::vector<Bracket> brackets;
        for (size_t i = 0; i + 1 < result.samples.size(); ++i) {
            const RadiusSample& a = result.samples[i];
            const RadiusSample& b = result.samples[i + 1];
            if (a.valid && b.valid && a.value != 0.0 && b.value != 0.0) {
                if ((a.value < 0.0 && b.value > 0.0) || (a.value > 0.0 && b.value < 0.0)) {
                    brackets.push_back({a.radius, b.radius});
                }
            }
        }

        // If one zero exists and any strict bracket => ambiguous
        if (zero_count == 1 && !brackets.empty()) {
            result.ambiguous = true;
            result.reason = "known separate root";
            return result;
        }

        // If one zero and no strict bracket: choose adjacent valid nonzero neighbor
        if (zero_count == 1 && brackets.empty()) {
            // Find the zero sample
            size_t zero_idx = 0;
            for (size_t i = 0; i < result.samples.size(); ++i) {
                if (result.samples[i].valid && result.samples[i].value == 0.0) {
                    zero_idx = i;
                    break;
                }
            }
            // Check left adjacent sample
            if (zero_idx > 0) {
                const RadiusSample& left = result.samples[zero_idx - 1];
                if (left.valid && left.value != 0.0) {
                    result.found = true;
                    result.lo = left.radius;
                    result.hi = result.samples[zero_idx].radius;
                    if (result.lo > result.hi) std::swap(result.lo, result.hi);
                    result.reason = "zero with left neighbor";
                    return result;
                }
            }
            // Check right adjacent sample
            if (zero_idx + 1 < result.samples.size()) {
                const RadiusSample& right = result.samples[zero_idx + 1];
                if (right.valid && right.value != 0.0) {
                    result.found = true;
                    result.lo = result.samples[zero_idx].radius;
                    result.hi = right.radius;
                    if (result.lo > result.hi) std::swap(result.lo, result.hi);
                    result.reason = "zero with right neighbor";
                    return result;
                }
            }
            // No neighbor: continue searching or insufficient at cap
            if (result.trials >= cap) {
                result.reason = "insufficient samples around zero";
                return result;
            }
            // else continue to adaptive probing
        }

        // If strict brackets > 1 => ambiguous
        if (brackets.size() > 1) {
            result.ambiguous = true;
            result.reason = "multiple brackets";
            return result;
        }

        // If exactly one strict bracket
        if (brackets.size() == 1) {
            double lo = brackets[0].lo;
            double hi = brackets[0].hi;
            // If budget left, sample midpoint once (unless already known)
            if (result.trials < cap) {
                double mid = 0.5 * (lo + hi);
                // Check if mid already sampled
                bool already = false;
                for (const auto& s : result.samples) {
                    if (s.radius == mid) { already = true; break; }
                }
                if (!already) {
                    double val = 0.0;
                    bool valid = false;
                    try {
                        val = eval(mid);
                        valid = std::isfinite(val);
                    } catch (...) {
                        valid = false;
                    }
                    result.samples.push_back({mid, val, valid});
                    ++result.trials;
                    // If midpoint invalid, continue central scan with it recorded
                    if (!valid) {
                        continue; // loop will re-sort and re-evaluate
                    }
                    // Valid midpoint: return finite bracket containing root
                    if (val == 0.0) {
                        result.found = true;
                        result.lo = lo;
                        result.hi = mid;
                        result.reason = "midpoint is root";
                        return result;
                    }
                    // Determine which side has sign change
                    // We need values at lo and hi (they are valid and nonzero)
                    double val_lo = 0.0, val_hi = 0.0;
                    for (const auto& s : result.samples) {
                        if (s.radius == lo) val_lo = s.value;
                        if (s.radius == hi) val_hi = s.value;
                    }
                    if ((val_lo < 0.0 && val > 0.0) || (val_lo > 0.0 && val < 0.0)) {
                        result.found = true;
                        result.lo = lo;
                        result.hi = mid;
                        result.reason = "bracket refined";
                        return result;
                    } else {
                        result.found = true;
                        result.lo = mid;
                        result.hi = hi;
                        result.reason = "bracket refined";
                        return result;
                    }
                } else {
                    // Mid already known, but we shouldn't get here because we would have returned earlier if it was valid? Actually if mid was already sampled and valid, we would have had a bracket or zero. So if already, it's likely invalid? But we can just continue.
                    result.reason = "resolution failure";
                    return result;
                }
            } else {
                // Cap exhausted: return original finite endpoints
                result.found = true;
                result.lo = lo;
                result.hi = hi;
                result.reason = "midpoint budget exhausted";
                return result;
            }
        }

        // No bracket found yet
        if (result.trials >= cap) {
            result.reason = "insufficient samples";
            return result;
        }

        // Adaptive probing: alternate boundary midpoint and global extension
        // Determine if there is a boundary between valid and invalid adjacent samples
        bool boundary_found = false;
        double boundary_radius = 0.0;
        double invalid_radius = 0.0;
        double best_abs_res = std::numeric_limits<double>::max();
        // Scan all adjacent pairs to find the boundary with smallest abs residual
        for (size_t i = 0; i + 1 < result.samples.size(); ++i) {
            const RadiusSample& a = result.samples[i];
            const RadiusSample& b = result.samples[i + 1];
            if (a.valid != b.valid) {
                // Determine valid and invalid samples
                const RadiusSample* valid_sample = nullptr;
                const RadiusSample* invalid_sample = nullptr;
                if (a.valid) {
                    valid_sample = &a;
                    invalid_sample = &b;
                } else {
                    valid_sample = &b;
                    invalid_sample = &a;
                }
                double abs_res = std::abs(valid_sample->value);
                if (abs_res < best_abs_res) {
                    best_abs_res = abs_res;
                    boundary_radius = valid_sample->radius;
                    invalid_radius = invalid_sample->radius;
                    boundary_found = true;
                }
            }
        }

        double probe_radius = 0.0;
        if (boundary_found && (extension_step % 2 == 0)) {
            // Boundary midpoint: between valid and invalid
            probe_radius = 0.5 * (boundary_radius + invalid_radius);
        }

        if (!boundary_found || (extension_step % 2 == 1)) {
            // Global extension: extend current min radius *0.8 and max radius *1.2 alternating
            double min_radius = result.samples.front().radius;
            double max_radius = result.samples.back().radius;
            if (global_extension_step % 2 == 0) {
                probe_radius = min_radius * 0.8;
            } else {
                probe_radius = max_radius * 1.2;
            }
            global_extension_step++;
        }

        // Validate probe_radius before evaluation
        if (!(probe_radius > 0.0 && std::isfinite(probe_radius))) {
            result.reason = "resolution failure";
            return result;
        }

        // Check if probe_radius already sampled
        bool duplicate = false;
        for (const auto& s : result.samples) {
            if (s.radius == probe_radius) {
                duplicate = true;
                break;
            }
        }
        if (duplicate) {
            result.reason = "resolution failure";
            return result;
        }

        // Evaluate probe
        double val = 0.0;
        bool valid = false;
        try {
            val = eval(probe_radius);
            valid = std::isfinite(val);
        } catch (...) {
            valid = false;
        }
        result.samples.push_back({probe_radius, val, valid});
        ++result.trials;
        ++extension_step;
    }
}

#endif // RADIUS_BRACKET_H
