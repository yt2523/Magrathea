#ifndef RADIUS_BRACKET_H
#define RADIUS_BRACKET_H

#include <algorithm>
#include <cmath>
#include <functional>
#include <limits>
#include <stdexcept>
#include <string>
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
    if (!(guess > 0.0) || !std::isfinite(guess)) {
        result.reason = "invalid guess";
        return result;
    }
    if (cap < 2) {
        result.reason = "cap too small";
        return result;
    }

    auto evaluate = [&](double x) -> RadiusSample {
        RadiusSample s;
        s.radius = x;
        s.valid = false;
        s.value = std::numeric_limits<double>::quiet_NaN();
        try {
            double v = eval(x);
            if (std::isfinite(v)) {
                s.value = v;
                s.valid = true;
            }
        } catch (const std::exception&) {
            // invalid
        }
        return s;
    };

    // Initial samples: 0.8, 0.9, 1.0, 1.1, 1.2 times guess
    std::vector<double> initial_factors = {0.8, 0.9, 1.0, 1.1, 1.2};
    for (double factor : initial_factors) {
        if (result.trials >= cap) break;
        double x = factor * guess;
        RadiusSample s = evaluate(x);
        result.samples.push_back(s);
        result.trials++;
    }

    // Sort samples by radius
    std::sort(result.samples.begin(), result.samples.end(),
              [](const RadiusSample& a, const RadiusSample& b) { return a.radius < b.radius; });

    // Check for adjacent valid samples with opposite signs (or zero)
    std::vector<std::pair<size_t, size_t>> brackets; // indices of adjacent samples forming bracket
    for (size_t i = 0; i + 1 < result.samples.size(); ++i) {
        const RadiusSample& a = result.samples[i];
        const RadiusSample& b = result.samples[i + 1];
        if (a.valid && b.valid) {
            if (a.value == 0.0 || b.value == 0.0) {
                brackets.push_back({i, i + 1});
            } else if ((a.value < 0.0 && b.value > 0.0) || (a.value > 0.0 && b.value < 0.0)) {
                brackets.push_back({i, i + 1});
            }
        }
    }

    if (brackets.size() > 1) {
        result.ambiguous = true;
        result.reason = "multiple sampled brackets";
        return result;
    }

    if (brackets.size() == 1) {
        size_t i = brackets[0].first;
        size_t j = brackets[0].second;
        // Check if there is an invalid sample between them? They are adjacent, so no.
        // Evaluate midpoint if budget allows
        if (result.trials < cap) {
            double mid = 0.5 * (result.samples[i].radius + result.samples[j].radius);
            RadiusSample midSample = evaluate(mid);
            result.samples.push_back(midSample);
            result.trials++;
            std::sort(result.samples.begin(), result.samples.end(),
                      [](const RadiusSample& a, const RadiusSample& b) { return a.radius < b.radius; });
            // Re-check brackets after adding midpoint
            brackets.clear();
            for (size_t k = 0; k + 1 < result.samples.size(); ++k) {
                const RadiusSample& a = result.samples[k];
                const RadiusSample& b = result.samples[k + 1];
                if (a.valid && b.valid) {
                    if (a.value == 0.0 || b.value == 0.0) {
                        brackets.push_back({k, k + 1});
                    } else if ((a.value < 0.0 && b.value > 0.0) || (a.value > 0.0 && b.value < 0.0)) {
                        brackets.push_back({k, k + 1});
                    }
                }
            }
            if (brackets.size() > 1) {
                result.ambiguous = true;
                result.reason = "multiple sampled brackets after midpoint";
                return result;
            }
            if (brackets.size() == 1) {
                i = brackets[0].first;
                j = brackets[0].second;
            } else {
                // Midpoint invalid or same sign, bracket lost
                result.reason = "midpoint invalid or same sign";
                return result;
            }
        }
        // Accept bracket
        result.found = true;
        result.lo = result.samples[i].radius;
        result.hi = result.samples[j].radius;
        result.reason = "found bracket";
        return result;
    }

    // No bracket found initially. Adaptive search.
    // We'll try to refine boundaries between valid/invalid and extend range if needed.
    // Strategy: find adjacent samples where one is valid and one invalid, and probe midpoint.
    // Also if all valid same sign, extend range.
    // We'll loop until cap exhausted or bracket found.

    while (result.trials < cap) {
        // Check if all samples are invalid
        bool all_invalid = true;
        for (const auto& s : result.samples) {
            if (s.valid) { all_invalid = false; break; }
        }
        if (all_invalid) {
            // Extend range: try lower and upper beyond current extremes
            double min_r = result.samples.front().radius;
            double max_r = result.samples.back().radius;
            // Try lower extension
            if (result.trials < cap) {
                double x = min_r * 0.8;
                RadiusSample s = evaluate(x);
                result.samples.push_back(s);
                result.trials++;
                std::sort(result.samples.begin(), result.samples.end(),
                          [](const RadiusSample& a, const RadiusSample& b) { return a.radius < b.radius; });
                // Recheck brackets
                brackets.clear();
                for (size_t k = 0; k + 1 < result.samples.size(); ++k) {
                    const RadiusSample& a = result.samples[k];
                    const RadiusSample& b = result.samples[k + 1];
                    if (a.valid && b.valid) {
                        if (a.value == 0.0 || b.value == 0.0) {
                            brackets.push_back({k, k + 1});
                        } else if ((a.value < 0.0 && b.value > 0.0) || (a.value > 0.0 && b.value < 0.0)) {
                            brackets.push_back({k, k + 1});
                        }
                    }
                }
                if (brackets.size() > 1) {
                    result.ambiguous = true;
                    result.reason = "multiple sampled brackets after extension";
                    return result;
                }
                if (brackets.size() == 1) {
                    result.found = true;
                    result.lo = result.samples[brackets[0].first].radius;
                    result.hi = result.samples[brackets[0].second].radius;
                    result.reason = "found bracket after extension";
                    return result;
                }
            }
            // Try upper extension
            if (result.trials < cap) {
                double x = max_r * 1.2;
                RadiusSample s = evaluate(x);
                result.samples.push_back(s);
                result.trials++;
                std::sort(result.samples.begin(), result.samples.end(),
                          [](const RadiusSample& a, const RadiusSample& b) { return a.radius < b.radius; });
                // Recheck brackets
                brackets.clear();
                for (size_t k = 0; k + 1 < result.samples.size(); ++k) {
                    const RadiusSample& a = result.samples[k];
                    const RadiusSample& b = result.samples[k + 1];
                    if (a.valid && b.valid) {
                        if (a.value == 0.0 || b.value == 0.0) {
                            brackets.push_back({k, k + 1});
                        } else if ((a.value < 0.0 && b.value > 0.0) || (a.value > 0.0 && b.value < 0.0)) {
                            brackets.push_back({k, k + 1});
                        }
                    }
                }
                if (brackets.size() > 1) {
                    result.ambiguous = true;
                    result.reason = "multiple sampled brackets after extension";
                    return result;
                }
                if (brackets.size() == 1) {
                    result.found = true;
                    result.lo = result.samples[brackets[0].first].radius;
                    result.hi = result.samples[brackets[0].second].radius;
                    result.reason = "found bracket after extension";
                    return result;
                }
            }
            continue;
        }

        // Not all invalid. Look for adjacent valid-invalid pairs to refine.
        // Find a pair where one is valid and one invalid, and the valid one has smallest abs value among valid samples.
        // We'll choose the boundary with the valid sample having smallest |value|.
        size_t best_i = 0, best_j = 0;
        bool found_boundary = false;
        double best_abs = std::numeric_limits<double>::max();
        for (size_t k = 0; k + 1 < result.samples.size(); ++k) {
            const RadiusSample& a = result.samples[k];
            const RadiusSample& b = result.samples[k + 1];
            if (a.valid != b.valid) {
                const RadiusSample& valid_s = a.valid ? a : b;
                double abs_val = std::abs(valid_s.value);
                if (abs_val < best_abs) {
                    best_abs = abs_val;
                    best_i = k;
                    best_j = k + 1;
                    found_boundary = true;
                }
            }
        }
        if (found_boundary) {
            // Probe midpoint of this boundary
            double mid = 0.5 * (result.samples[best_i].radius + result.samples[best_j].radius);
            RadiusSample s = evaluate(mid);
            result.samples.push_back(s);
            result.trials++;
            std::sort(result.samples.begin(), result.samples.end(),
                      [](const RadiusSample& a, const RadiusSample& b) { return a.radius < b.radius; });
            // Recheck brackets
            brackets.clear();
            for (size_t k = 0; k + 1 < result.samples.size(); ++k) {
                const RadiusSample& a = result.samples[k];
                const RadiusSample& b = result.samples[k + 1];
                if (a.valid && b.valid) {
                    if (a.value == 0.0 || b.value == 0.0) {
                        brackets.push_back({k, k + 1});
                    } else if ((a.value < 0.0 && b.value > 0.0) || (a.value > 0.0 && b.value < 0.0)) {
                        brackets.push_back({k, k + 1});
                    }
                }
            }
            if (brackets.size() > 1) {
                result.ambiguous = true;
                result.reason = "multiple sampled brackets after boundary refinement";
                return result;
            }
            if (brackets.size() == 1) {
                result.found = true;
                result.lo = result.samples[brackets[0].first].radius;
                result.hi = result.samples[brackets[0].second].radius;
                result.reason = "found bracket after boundary refinement";
                return result;
            }
            continue;
        }

        // No valid-invalid boundary? Then all samples are valid and same sign (since no bracket). Extend range.
        // Determine if all positive or all negative.
        bool all_positive = true;
        bool all_negative = true;
        for (const auto& s : result.samples) {
            if (!s.valid) { all_positive = all_negative = false; break; }
            if (s.value > 0.0) all_negative = false;
            if (s.value < 0.0) all_positive = false;
        }
        if (all_positive || all_negative) {
            // Extend in direction that might change sign: if all positive, try lower; if all negative, try higher.
            double min_r = result.samples.front().radius;
            double max_r = result.samples.back().radius;
            if (all_positive) {
                // Try lower extension
                if (result.trials < cap) {
                    double x = min_r * 0.8;
                    RadiusSample s = evaluate(x);
                    result.samples.push_back(s);
                    result.trials++;
                    std::sort(result.samples.begin(), result.samples.end(),
                              [](const RadiusSample& a, const RadiusSample& b) { return a.radius < b.radius; });
                    // Recheck brackets
                    brackets.clear();
                    for (size_t k = 0; k + 1 < result.samples.size(); ++k) {
                        const RadiusSample& a = result.samples[k];
                        const RadiusSample& b = result.samples[k + 1];
                        if (a.valid && b.valid) {
                            if (a.value == 0.0 || b.value == 0.0) {
                                brackets.push_back({k, k + 1});
                            } else if ((a.value < 0.0 && b.value > 0.0) || (a.value > 0.0 && b.value < 0.0)) {
                                brackets.push_back({k, k + 1});
                            }
                        }
                    }
                    if (brackets.size() > 1) {
                        result.ambiguous = true;
                        result.reason = "multiple sampled brackets after extension";
                        return result;
                    }
                    if (brackets.size() == 1) {
                        result.found = true;
                        result.lo = result.samples[brackets[0].first].radius;
                        result.hi = result.samples[brackets[0].second].radius;
                        result.reason = "found bracket after extension";
                        return result;
                    }
                }
            } else if (all_negative) {
                // Try upper extension
                if (result.trials < cap) {
                    double x = max_r * 1.2;
                    RadiusSample s = evaluate(x);
                    result.samples.push_back(s);
                    result.trials++;
                    std::sort(result.samples.begin(), result.samples.end(),
                              [](const RadiusSample& a, const RadiusSample& b) { return a.radius < b.radius; });
                    // Recheck brackets
                    brackets.clear();
                    for (size_t k = 0; k + 1 < result.samples.size(); ++k) {
                        const RadiusSample& a = result.samples[k];
                        const RadiusSample& b = result.samples[k + 1];
                        if (a.valid && b.valid) {
                            if (a.value == 0.0 || b.value == 0.0) {
                                brackets.push_back({k, k + 1});
                            } else if ((a.value < 0.0 && b.value > 0.0) || (a.value > 0.0 && b.value < 0.0)) {
                                brackets.push_back({k, k + 1});
                            }
                        }
                    }
                    if (brackets.size() > 1) {
                        result.ambiguous = true;
                        result.reason = "multiple sampled brackets after extension";
                        return result;
                    }
                    if (brackets.size() == 1) {
                        result.found = true;
                        result.lo = result.samples[brackets[0].first].radius;
                        result.hi = result.samples[brackets[0].second].radius;
                        result.reason = "found bracket after extension";
                        return result;
                    }
                }
            }
            continue;
        }

        // If we get here, something unexpected; break to avoid infinite loop
        break;
    }

    result.reason = "budget exhausted without bracket";
    return result;
}

#endif // RADIUS_BRACKET_H
