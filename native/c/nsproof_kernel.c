#include <math.h>
#include <stddef.h>

#if defined(_WIN32)
#define NSPROOF_EXPORT __declspec(dllexport)
#else
#define NSPROOF_EXPORT __attribute__((visibility("default")))
#endif

enum {
    NSPROOF_KERNEL_OK = 0,
    NSPROOF_KERNEL_NULL_POINTER = -1,
    NSPROOF_KERNEL_BAD_ORDER = -2,
    NSPROOF_KERNEL_BAD_INDEX = -3,
    NSPROOF_KERNEL_DEGENERATE_INTERVAL = -4,
    NSPROOF_KERNEL_NONFINITE_INPUT = -5,
    NSPROOF_KERNEL_NONFINITE_OUTPUT = -6
};

static int check_order(int order) {
    return order >= 0 && order <= 4;
}

static int check_finite(double value) {
    return isfinite(value);
}

static double int_power(double base, int order) {
    double out = 1.0;
    int i;
    for (i = 0; i < order; i++) {
        out *= base;
    }
    return out;
}

static double falling(double value, int order) {
    double out = 1.0;
    int k;
    for (k = 0; k < order; k++) {
        out *= value - (double)k;
    }
    return out;
}

static int interval_inputs_ok(double lo, double hi) {
    return check_finite(lo) && check_finite(hi) && lo <= hi;
}

static double interval_down(double value) {
    if (isnan(value)) {
        return value;
    }
    if (value == -INFINITY) {
        return value;
    }
    return nextafter(value, -INFINITY);
}

static double interval_up(double value) {
    if (isnan(value)) {
        return value;
    }
    if (value == INFINITY) {
        return value;
    }
    return nextafter(value, INFINITY);
}

static int interval_add_impl(
    double a_lo,
    double a_hi,
    double b_lo,
    double b_hi,
    double *out_lo,
    double *out_hi
) {
    if (out_lo == NULL || out_hi == NULL) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    if (!interval_inputs_ok(a_lo, a_hi) || !interval_inputs_ok(b_lo, b_hi)) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }
    *out_lo = interval_down(a_lo + b_lo);
    *out_hi = interval_up(a_hi + b_hi);
    if (isnan(*out_lo) || isnan(*out_hi) || *out_lo > *out_hi) {
        return NSPROOF_KERNEL_NONFINITE_OUTPUT;
    }
    return NSPROOF_KERNEL_OK;
}

static int interval_sub_impl(
    double a_lo,
    double a_hi,
    double b_lo,
    double b_hi,
    double *out_lo,
    double *out_hi
) {
    if (out_lo == NULL || out_hi == NULL) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    if (!interval_inputs_ok(a_lo, a_hi) || !interval_inputs_ok(b_lo, b_hi)) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }
    *out_lo = interval_down(a_lo - b_hi);
    *out_hi = interval_up(a_hi - b_lo);
    if (isnan(*out_lo) || isnan(*out_hi) || *out_lo > *out_hi) {
        return NSPROOF_KERNEL_NONFINITE_OUTPUT;
    }
    return NSPROOF_KERNEL_OK;
}

static int interval_mul_impl(
    double a_lo,
    double a_hi,
    double b_lo,
    double b_hi,
    double *out_lo,
    double *out_hi
) {
    double p0;
    double p1;
    double p2;
    double p3;
    double lo;
    double hi;

    if (out_lo == NULL || out_hi == NULL) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    if (!interval_inputs_ok(a_lo, a_hi) || !interval_inputs_ok(b_lo, b_hi)) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }
    p0 = a_lo * b_lo;
    p1 = a_lo * b_hi;
    p2 = a_hi * b_lo;
    p3 = a_hi * b_hi;
    if (!check_finite(p0) || !check_finite(p1) || !check_finite(p2) || !check_finite(p3)) {
        return NSPROOF_KERNEL_NONFINITE_OUTPUT;
    }
    lo = fmin(fmin(p0, p1), fmin(p2, p3));
    hi = fmax(fmax(p0, p1), fmax(p2, p3));
    *out_lo = interval_down(lo);
    *out_hi = interval_up(hi);
    if (isnan(*out_lo) || isnan(*out_hi) || *out_lo > *out_hi) {
        return NSPROOF_KERNEL_NONFINITE_OUTPUT;
    }
    return NSPROOF_KERNEL_OK;
}

static int interval_recip_impl(
    double a_lo,
    double a_hi,
    double *out_lo,
    double *out_hi
) {
    double r0;
    double r1;
    double lo;
    double hi;

    if (out_lo == NULL || out_hi == NULL) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    if (!interval_inputs_ok(a_lo, a_hi)) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }
    if (a_lo <= 0.0 && a_hi >= 0.0) {
        return NSPROOF_KERNEL_DEGENERATE_INTERVAL;
    }
    r0 = 1.0 / a_lo;
    r1 = 1.0 / a_hi;
    if (!check_finite(r0) || !check_finite(r1)) {
        return NSPROOF_KERNEL_NONFINITE_OUTPUT;
    }
    lo = fmin(r0, r1);
    hi = fmax(r0, r1);
    *out_lo = interval_down(lo);
    *out_hi = interval_up(hi);
    if (isnan(*out_lo) || isnan(*out_hi) || *out_lo > *out_hi) {
        return NSPROOF_KERNEL_NONFINITE_OUTPUT;
    }
    return NSPROOF_KERNEL_OK;
}

static int interval_poly_eval_impl(
    int coeff_count,
    const double *coeffs,
    double x_lo,
    double x_hi,
    double *out_lo,
    double *out_hi
) {
    double acc_lo;
    double acc_hi;
    double prod_lo;
    double prod_hi;
    int i;
    int status;

    if (coeff_count <= 0) {
        return NSPROOF_KERNEL_BAD_INDEX;
    }
    if (coeffs == NULL || out_lo == NULL || out_hi == NULL) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    if (!interval_inputs_ok(x_lo, x_hi)) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }
    for (i = 0; i < coeff_count; i++) {
        if (!check_finite(coeffs[i])) {
            return NSPROOF_KERNEL_NONFINITE_INPUT;
        }
    }
    acc_lo = coeffs[coeff_count - 1];
    acc_hi = coeffs[coeff_count - 1];
    for (i = coeff_count - 2; i >= 0; i--) {
        status = interval_mul_impl(acc_lo, acc_hi, x_lo, x_hi, &prod_lo, &prod_hi);
        if (status != NSPROOF_KERNEL_OK) {
            return status;
        }
        status = interval_add_impl(prod_lo, prod_hi, coeffs[i], coeffs[i], &acc_lo, &acc_hi);
        if (status != NSPROOF_KERNEL_OK) {
            return status;
        }
    }
    *out_lo = acc_lo;
    *out_hi = acc_hi;
    return NSPROOF_KERNEL_OK;
}

NSPROOF_EXPORT int nsproof_interval_add_batch(
    int count,
    const double *a_lo,
    const double *a_hi,
    const double *b_lo,
    const double *b_hi,
    double *out_lo,
    double *out_hi,
    int *statuses
) {
    int i;
    int first_error = NSPROOF_KERNEL_OK;

    if (count < 0) {
        return NSPROOF_KERNEL_BAD_INDEX;
    }
    if (count == 0) {
        return NSPROOF_KERNEL_OK;
    }
    if (
        a_lo == NULL || a_hi == NULL || b_lo == NULL || b_hi == NULL ||
        out_lo == NULL || out_hi == NULL || statuses == NULL
    ) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    for (i = 0; i < count; i++) {
        statuses[i] = interval_add_impl(a_lo[i], a_hi[i], b_lo[i], b_hi[i], &out_lo[i], &out_hi[i]);
        if (statuses[i] != NSPROOF_KERNEL_OK && first_error == NSPROOF_KERNEL_OK) {
            first_error = statuses[i];
        }
    }
    return first_error;
}

NSPROOF_EXPORT int nsproof_interval_sub_batch(
    int count,
    const double *a_lo,
    const double *a_hi,
    const double *b_lo,
    const double *b_hi,
    double *out_lo,
    double *out_hi,
    int *statuses
) {
    int i;
    int first_error = NSPROOF_KERNEL_OK;

    if (count < 0) {
        return NSPROOF_KERNEL_BAD_INDEX;
    }
    if (count == 0) {
        return NSPROOF_KERNEL_OK;
    }
    if (
        a_lo == NULL || a_hi == NULL || b_lo == NULL || b_hi == NULL ||
        out_lo == NULL || out_hi == NULL || statuses == NULL
    ) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    for (i = 0; i < count; i++) {
        statuses[i] = interval_sub_impl(a_lo[i], a_hi[i], b_lo[i], b_hi[i], &out_lo[i], &out_hi[i]);
        if (statuses[i] != NSPROOF_KERNEL_OK && first_error == NSPROOF_KERNEL_OK) {
            first_error = statuses[i];
        }
    }
    return first_error;
}

NSPROOF_EXPORT int nsproof_interval_mul_batch(
    int count,
    const double *a_lo,
    const double *a_hi,
    const double *b_lo,
    const double *b_hi,
    double *out_lo,
    double *out_hi,
    int *statuses
) {
    int i;
    int first_error = NSPROOF_KERNEL_OK;

    if (count < 0) {
        return NSPROOF_KERNEL_BAD_INDEX;
    }
    if (count == 0) {
        return NSPROOF_KERNEL_OK;
    }
    if (
        a_lo == NULL || a_hi == NULL || b_lo == NULL || b_hi == NULL ||
        out_lo == NULL || out_hi == NULL || statuses == NULL
    ) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    for (i = 0; i < count; i++) {
        statuses[i] = interval_mul_impl(a_lo[i], a_hi[i], b_lo[i], b_hi[i], &out_lo[i], &out_hi[i]);
        if (statuses[i] != NSPROOF_KERNEL_OK && first_error == NSPROOF_KERNEL_OK) {
            first_error = statuses[i];
        }
    }
    return first_error;
}

NSPROOF_EXPORT int nsproof_interval_recip_batch(
    int count,
    const double *a_lo,
    const double *a_hi,
    double *out_lo,
    double *out_hi,
    int *statuses
) {
    int i;
    int first_error = NSPROOF_KERNEL_OK;

    if (count < 0) {
        return NSPROOF_KERNEL_BAD_INDEX;
    }
    if (count == 0) {
        return NSPROOF_KERNEL_OK;
    }
    if (a_lo == NULL || a_hi == NULL || out_lo == NULL || out_hi == NULL || statuses == NULL) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    for (i = 0; i < count; i++) {
        statuses[i] = interval_recip_impl(a_lo[i], a_hi[i], &out_lo[i], &out_hi[i]);
        if (statuses[i] != NSPROOF_KERNEL_OK && first_error == NSPROOF_KERNEL_OK) {
            first_error = statuses[i];
        }
    }
    return first_error;
}

NSPROOF_EXPORT int nsproof_interval_poly_eval_batch(
    int point_count,
    int coeff_count,
    const double *coeffs,
    const double *x_lo,
    const double *x_hi,
    double *out_lo,
    double *out_hi,
    int *statuses
) {
    int i;
    int first_error = NSPROOF_KERNEL_OK;

    if (point_count < 0 || coeff_count <= 0) {
        return NSPROOF_KERNEL_BAD_INDEX;
    }
    if (point_count == 0) {
        return NSPROOF_KERNEL_OK;
    }
    if (
        coeffs == NULL || x_lo == NULL || x_hi == NULL ||
        out_lo == NULL || out_hi == NULL || statuses == NULL
    ) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    for (i = 0; i < point_count; i++) {
        statuses[i] = interval_poly_eval_impl(
            coeff_count,
            coeffs,
            x_lo[i],
            x_hi[i],
            &out_lo[i],
            &out_hi[i]
        );
        if (statuses[i] != NSPROOF_KERNEL_OK && first_error == NSPROOF_KERNEL_OK) {
            first_error = statuses[i];
        }
    }
    return first_error;
}

NSPROOF_EXPORT int nsproof_bernstein_range_batch(
    int polynomial_count,
    const int *offsets,
    const int *counts,
    const double *coeff_lo,
    const double *coeff_hi,
    double *out_lo,
    double *out_hi,
    int *statuses
) {
    int poly;
    int first_error = NSPROOF_KERNEL_OK;

    if (polynomial_count < 0) {
        return NSPROOF_KERNEL_BAD_INDEX;
    }
    if (polynomial_count == 0) {
        return NSPROOF_KERNEL_OK;
    }
    if (
        offsets == NULL || counts == NULL || coeff_lo == NULL || coeff_hi == NULL ||
        out_lo == NULL || out_hi == NULL || statuses == NULL
    ) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    for (poly = 0; poly < polynomial_count; poly++) {
        int offset = offsets[poly];
        int count = counts[poly];
        int i;
        double lo;
        double hi;
        int status = NSPROOF_KERNEL_OK;

        if (offset < 0 || count <= 0) {
            status = NSPROOF_KERNEL_BAD_INDEX;
        } else if (!interval_inputs_ok(coeff_lo[offset], coeff_hi[offset])) {
            status = NSPROOF_KERNEL_NONFINITE_INPUT;
        } else {
            lo = coeff_lo[offset];
            hi = coeff_hi[offset];
            for (i = 1; i < count; i++) {
                int idx = offset + i;
                if (!interval_inputs_ok(coeff_lo[idx], coeff_hi[idx])) {
                    status = NSPROOF_KERNEL_NONFINITE_INPUT;
                    break;
                }
                if (coeff_lo[idx] < lo) {
                    lo = coeff_lo[idx];
                }
                if (coeff_hi[idx] > hi) {
                    hi = coeff_hi[idx];
                }
            }
            if (status == NSPROOF_KERNEL_OK) {
                out_lo[poly] = interval_down(lo);
                out_hi[poly] = interval_up(hi);
                if (isnan(out_lo[poly]) || isnan(out_hi[poly]) || out_lo[poly] > out_hi[poly]) {
                    status = NSPROOF_KERNEL_NONFINITE_OUTPUT;
                }
            }
        }
        statuses[poly] = status;
        if (status != NSPROOF_KERNEL_OK && first_error == NSPROOF_KERNEL_OK) {
            first_error = status;
        }
    }
    return first_error;
}

static int binom_small(int n, int k) {
    int i;
    int out;

    if (k < 0 || k > n) {
        return 0;
    }
    if (k > n - k) {
        k = n - k;
    }
    out = 1;
    for (i = 1; i <= k; i++) {
        out = (out * (n - k + i)) / i;
    }
    return out;
}

static int cheb_basis_value_impl(int index, double t, int order, double *value) {
    double prev2[5] = {0.0, 0.0, 0.0, 0.0, 0.0};
    double prev1[5] = {0.0, 0.0, 0.0, 0.0, 0.0};
    double curr[5] = {0.0, 0.0, 0.0, 0.0, 0.0};
    int n;
    int m;

    if (value == NULL) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    if (!check_order(order)) {
        return NSPROOF_KERNEL_BAD_ORDER;
    }
    if (index < 0) {
        return NSPROOF_KERNEL_BAD_INDEX;
    }
    if (!check_finite(t)) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }

    prev2[0] = 1.0;
    if (index == 0) {
        *value = prev2[order];
        return NSPROOF_KERNEL_OK;
    }

    prev1[0] = t;
    prev1[1] = 1.0;
    if (index == 1) {
        *value = prev1[order];
        return NSPROOF_KERNEL_OK;
    }

    for (n = 2; n <= index; n++) {
        for (m = 0; m <= order; m++) {
            double out = 2.0 * t * prev1[m] - prev2[m];
            if (m > 0) {
                out += 2.0 * (double)m * prev1[m - 1];
            }
            curr[m] = out;
        }
        for (m = 0; m <= order; m++) {
            prev2[m] = prev1[m];
            prev1[m] = curr[m];
        }
    }

    *value = prev1[order];
    if (!check_finite(*value)) {
        return NSPROOF_KERNEL_NONFINITE_OUTPUT;
    }
    return NSPROOF_KERNEL_OK;
}

static int cheb_basis_partial_impl(
    double q0,
    double q1,
    double x0,
    double x1,
    double q,
    double x,
    int kq,
    int kx,
    int dq_order,
    int dx_order,
    double *value
) {
    double tq;
    double tx;
    double q_value;
    double x_value;
    int status;

    if (value == NULL) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    if (!check_order(dq_order) || !check_order(dx_order)) {
        return NSPROOF_KERNEL_BAD_ORDER;
    }
    if (kq < 0 || kx < 0) {
        return NSPROOF_KERNEL_BAD_INDEX;
    }
    if (q1 == q0 || x1 == x0) {
        return NSPROOF_KERNEL_DEGENERATE_INTERVAL;
    }
    if (
        !check_finite(q0) ||
        !check_finite(q1) ||
        !check_finite(x0) ||
        !check_finite(x1) ||
        !check_finite(q) ||
        !check_finite(x)
    ) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }

    tq = (2.0 * q - q0 - q1) / (q1 - q0);
    tx = (2.0 * x - x0 - x1) / (x1 - x0);

    status = cheb_basis_value_impl(kq, tq, dq_order, &q_value);
    if (status != NSPROOF_KERNEL_OK) {
        return status;
    }
    status = cheb_basis_value_impl(kx, tx, dx_order, &x_value);
    if (status != NSPROOF_KERNEL_OK) {
        return status;
    }

    *value =
        q_value *
        x_value *
        int_power(2.0 / (q1 - q0), dq_order) *
        int_power(2.0 / (x1 - x0), dx_order);
    if (!check_finite(*value)) {
        return NSPROOF_KERNEL_NONFINITE_OUTPUT;
    }
    return NSPROOF_KERNEL_OK;
}

NSPROOF_EXPORT int nsproof_cheb_basis_values(
    int count,
    double t,
    int order,
    double *out
) {
    double prev2[5] = {0.0, 0.0, 0.0, 0.0, 0.0};
    double prev1[5] = {0.0, 0.0, 0.0, 0.0, 0.0};
    double curr[5] = {0.0, 0.0, 0.0, 0.0, 0.0};
    int n;
    int m;

    if (!check_order(order)) {
        return NSPROOF_KERNEL_BAD_ORDER;
    }
    if (!check_finite(t)) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }
    if (count <= 0) {
        return NSPROOF_KERNEL_OK;
    }
    if (out == NULL) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }

    prev2[0] = 1.0;
    out[0] = prev2[order];
    if (count == 1) {
        return NSPROOF_KERNEL_OK;
    }

    prev1[0] = t;
    prev1[1] = 1.0;
    out[1] = prev1[order];

    for (n = 2; n < count; n++) {
        for (m = 0; m <= order; m++) {
            double value = 2.0 * t * prev1[m] - prev2[m];
            if (m > 0) {
                value += 2.0 * (double)m * prev1[m - 1];
            }
            curr[m] = value;
        }
        out[n] = curr[order];
        if (!check_finite(out[n])) {
            return NSPROOF_KERNEL_NONFINITE_OUTPUT;
        }
        for (m = 0; m <= order; m++) {
            prev2[m] = prev1[m];
            prev1[m] = curr[m];
        }
    }

    return NSPROOF_KERNEL_OK;
}

NSPROOF_EXPORT double nsproof_cheb_basis_value(
    int index,
    double t,
    int order,
    int *status
) {
    double value = 0.0;
    int rc = cheb_basis_value_impl(index, t, order, &value);
    if (status != NULL) {
        *status = rc;
    }
    return value;
}

NSPROOF_EXPORT double nsproof_cheb_basis_partial(
    double q0,
    double q1,
    double x0,
    double x1,
    double q,
    double x,
    int kq,
    int kx,
    int dq_order,
    int dx_order,
    int *status
) {
    double value = 0.0;
    int rc = cheb_basis_partial_impl(
        q0,
        q1,
        x0,
        x1,
        q,
        x,
        kq,
        kx,
        dq_order,
        dx_order,
        &value
    );
    if (status != NULL) {
        *status = rc;
    }
    return value;
}

NSPROOF_EXPORT double nsproof_weighted_cheb_coeff_partial(
    double q0,
    double q1,
    double x0,
    double x1,
    double alpha,
    double q,
    double x,
    int kq,
    int kx,
    int dq_order,
    int dx_order,
    int *status
) {
    double total = 0.0;
    int i;
    int rc;

    if (!check_order(dq_order) || !check_order(dx_order)) {
        if (status != NULL) {
            *status = NSPROOF_KERNEL_BAD_ORDER;
        }
        return 0.0;
    }
    if (kq < 0 || kx < 0) {
        if (status != NULL) {
            *status = NSPROOF_KERNEL_BAD_INDEX;
        }
        return 0.0;
    }
    if (q1 == q0 || x1 == x0) {
        if (status != NULL) {
            *status = NSPROOF_KERNEL_DEGENERATE_INTERVAL;
        }
        return 0.0;
    }
    if (
        !check_finite(q0) ||
        !check_finite(q1) ||
        !check_finite(x0) ||
        !check_finite(x1) ||
        !check_finite(alpha) ||
        !check_finite(q) ||
        !check_finite(x)
    ) {
        if (status != NULL) {
            *status = NSPROOF_KERNEL_NONFINITE_INPUT;
        }
        return 0.0;
    }

    for (i = 0; i <= dq_order; i++) {
        double basis_partial = 0.0;
        double q_weight = falling(alpha, i) * pow(q, alpha - (double)i);
        if (!check_finite(q_weight)) {
            if (status != NULL) {
                *status = NSPROOF_KERNEL_NONFINITE_OUTPUT;
            }
            return 0.0;
        }
        rc = cheb_basis_partial_impl(
            q0,
            q1,
            x0,
            x1,
            q,
            x,
            kq,
            kx,
            dq_order - i,
            dx_order,
            &basis_partial
        );
        if (rc != NSPROOF_KERNEL_OK) {
            if (status != NULL) {
                *status = rc;
            }
            return 0.0;
        }
        total += (double)binom_small(dq_order, i) * q_weight * basis_partial;
        if (!check_finite(total)) {
            if (status != NULL) {
                *status = NSPROOF_KERNEL_NONFINITE_OUTPUT;
            }
            return 0.0;
        }
    }

    if (status != NULL) {
        *status = NSPROOF_KERNEL_OK;
    }
    return total;
}

NSPROOF_EXPORT int nsproof_weighted_cheb_coeff_partial_array(
    int count,
    double q0,
    double q1,
    double x0,
    double x1,
    const double *alpha,
    const double *q,
    const double *x,
    const int *kq,
    const int *kx,
    const int *dq_order,
    const int *dx_order,
    double *out
) {
    int i;

    if (count <= 0) {
        return NSPROOF_KERNEL_OK;
    }
    if (
        alpha == NULL ||
        q == NULL ||
        x == NULL ||
        kq == NULL ||
        kx == NULL ||
        dq_order == NULL ||
        dx_order == NULL ||
        out == NULL
    ) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }

    for (i = 0; i < count; i++) {
        int status = NSPROOF_KERNEL_OK;
        out[i] = nsproof_weighted_cheb_coeff_partial(
            q0,
            q1,
            x0,
            x1,
            alpha[i],
            q[i],
            x[i],
            kq[i],
            kx[i],
            dq_order[i],
            dx_order[i],
            &status
        );
        if (status != NSPROOF_KERNEL_OK) {
            return status;
        }
    }

    return NSPROOF_KERNEL_OK;
}

#define NSPROOF_JET_MAX_ORDER 4

typedef struct {
    int order;
    double c[NSPROOF_JET_MAX_ORDER + 1][NSPROOF_JET_MAX_ORDER + 1];
} NsproofJet2;

static int factorial_small(int value) {
    int out = 1;
    int i;
    for (i = 2; i <= value; i++) {
        out *= i;
    }
    return out;
}

static int rz_spec_count(int max_order) {
    return (max_order + 1) * (max_order + 2) / 2;
}

static NsproofJet2 jet_zero(int order) {
    NsproofJet2 out;
    int a;
    int b;
    out.order = order;
    for (a = 0; a <= NSPROOF_JET_MAX_ORDER; a++) {
        for (b = 0; b <= NSPROOF_JET_MAX_ORDER; b++) {
            out.c[a][b] = 0.0;
        }
    }
    return out;
}

static NsproofJet2 jet_const(int order, double value) {
    NsproofJet2 out = jet_zero(order);
    out.c[0][0] = value;
    return out;
}

static NsproofJet2 jet_var_r(int order, double value) {
    NsproofJet2 out = jet_const(order, value);
    if (order >= 1) {
        out.c[1][0] = 1.0;
    }
    return out;
}

static NsproofJet2 jet_var_z(int order, double value) {
    NsproofJet2 out = jet_const(order, value);
    if (order >= 1) {
        out.c[0][1] = 1.0;
    }
    return out;
}

static int jet_is_finite(const NsproofJet2 *jet) {
    int a;
    int b;
    for (a = 0; a <= jet->order; a++) {
        for (b = 0; b <= jet->order - a; b++) {
            if (!check_finite(jet->c[a][b])) {
                return 0;
            }
        }
    }
    return 1;
}

static NsproofJet2 jet_add(NsproofJet2 lhs, NsproofJet2 rhs) {
    NsproofJet2 out = jet_zero(lhs.order);
    int a;
    int b;
    for (a = 0; a <= lhs.order; a++) {
        for (b = 0; b <= lhs.order - a; b++) {
            out.c[a][b] = lhs.c[a][b] + rhs.c[a][b];
        }
    }
    return out;
}

static NsproofJet2 jet_sub(NsproofJet2 lhs, NsproofJet2 rhs) {
    NsproofJet2 out = jet_zero(lhs.order);
    int a;
    int b;
    for (a = 0; a <= lhs.order; a++) {
        for (b = 0; b <= lhs.order - a; b++) {
            out.c[a][b] = lhs.c[a][b] - rhs.c[a][b];
        }
    }
    return out;
}

static NsproofJet2 jet_scale(NsproofJet2 jet, double scale) {
    NsproofJet2 out = jet_zero(jet.order);
    int a;
    int b;
    for (a = 0; a <= jet.order; a++) {
        for (b = 0; b <= jet.order - a; b++) {
            out.c[a][b] = scale * jet.c[a][b];
        }
    }
    return out;
}

static NsproofJet2 jet_add_scalar(NsproofJet2 jet, double value) {
    NsproofJet2 out = jet;
    out.c[0][0] += value;
    return out;
}

static NsproofJet2 jet_mul(NsproofJet2 lhs, NsproofJet2 rhs) {
    NsproofJet2 out = jet_zero(lhs.order);
    int a1;
    int b1;
    int a2;
    int b2;
    for (a1 = 0; a1 <= lhs.order; a1++) {
        for (b1 = 0; b1 <= lhs.order - a1; b1++) {
            double v1 = lhs.c[a1][b1];
            if (v1 == 0.0) {
                continue;
            }
            for (a2 = 0; a2 <= rhs.order; a2++) {
                for (b2 = 0; b2 <= rhs.order - a2; b2++) {
                    int a = a1 + a2;
                    int b = b1 + b2;
                    if (a + b <= lhs.order) {
                        out.c[a][b] += v1 * rhs.c[a2][b2];
                    }
                }
            }
        }
    }
    return out;
}

static NsproofJet2 jet_dr(NsproofJet2 jet) {
    NsproofJet2 out = jet_zero(jet.order);
    int a;
    int b;
    for (a = 1; a <= jet.order; a++) {
        for (b = 0; b <= jet.order - a; b++) {
            out.c[a - 1][b] += (double)a * jet.c[a][b];
        }
    }
    return out;
}

static NsproofJet2 jet_dz(NsproofJet2 jet) {
    NsproofJet2 out = jet_zero(jet.order);
    int a;
    int b;
    for (a = 0; a <= jet.order; a++) {
        for (b = 1; b <= jet.order - a; b++) {
            out.c[a][b - 1] += (double)b * jet.c[a][b];
        }
    }
    return out;
}

static int jet_pow_real(NsproofJet2 jet, double exponent, NsproofJet2 *out) {
    double base;
    double binom_value = 1.0;
    int n;
    NsproofJet2 h;
    NsproofJet2 power;
    NsproofJet2 acc;

    if (out == NULL) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    if (!check_finite(exponent) || !jet_is_finite(&jet)) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }
    base = jet.c[0][0];
    if (!(base > 0.0) || !check_finite(base)) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }

    h = jet_scale(jet_sub(jet, jet_const(jet.order, base)), 1.0 / base);
    power = jet_const(jet.order, 1.0);
    acc = jet_zero(jet.order);
    for (n = 0; n <= jet.order; n++) {
        if (n > 0) {
            binom_value *= (exponent - (double)(n - 1)) / (double)n;
        }
        acc = jet_add(acc, jet_scale(power, binom_value));
        power = jet_mul(power, h);
    }
    *out = jet_scale(acc, pow(base, exponent));
    if (!jet_is_finite(out)) {
        return NSPROOF_KERNEL_NONFINITE_OUTPUT;
    }
    return NSPROOF_KERNEL_OK;
}

static int jet_div(NsproofJet2 lhs, NsproofJet2 rhs, NsproofJet2 *out) {
    NsproofJet2 inv;
    int status = jet_pow_real(rhs, -1.0, &inv);
    if (status != NSPROOF_KERNEL_OK) {
        return status;
    }
    *out = jet_mul(lhs, inv);
    if (!jet_is_finite(out)) {
        return NSPROOF_KERNEL_NONFINITE_OUTPUT;
    }
    return NSPROOF_KERNEL_OK;
}

static int jet_cheb_t(int index, NsproofJet2 t, NsproofJet2 *out) {
    NsproofJet2 prev2;
    NsproofJet2 prev1;
    NsproofJet2 curr;
    int n;

    if (out == NULL) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    if (index < 0) {
        return NSPROOF_KERNEL_BAD_INDEX;
    }
    prev2 = jet_const(t.order, 1.0);
    if (index == 0) {
        *out = prev2;
        return NSPROOF_KERNEL_OK;
    }
    prev1 = t;
    if (index == 1) {
        *out = prev1;
        return NSPROOF_KERNEL_OK;
    }
    for (n = 2; n <= index; n++) {
        curr = jet_sub(jet_scale(jet_mul(t, prev1), 2.0), prev2);
        prev2 = prev1;
        prev1 = curr;
    }
    *out = prev1;
    if (!jet_is_finite(out)) {
        return NSPROOF_KERNEL_NONFINITE_OUTPUT;
    }
    return NSPROOF_KERNEL_OK;
}

static double jet_partial(NsproofJet2 jet, int dR_order, int dZ_order) {
    return jet.c[dR_order][dZ_order] * (double)factorial_small(dR_order) * (double)factorial_small(dZ_order);
}

static int make_rz_qx_jets(double q_coord, double x_coord, int order, NsproofJet2 *q_jet, NsproofJet2 *x_jet) {
    double rho0;
    double R0;
    double Z0;
    NsproofJet2 R;
    NsproofJet2 Z;
    NsproofJet2 rho;
    NsproofJet2 one_plus_rho;
    int status;

    if (q_jet == NULL || x_jet == NULL) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    if (!check_finite(q_coord) || !check_finite(x_coord)) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }
    if (!(q_coord > 0.0) || !(q_coord < 1.0) || x_coord < 0.0 || x_coord > 1.0) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }

    rho0 = 1.0 / (q_coord * q_coord) - 1.0;
    if (!(rho0 > 0.0) || !check_finite(rho0)) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }
    R0 = rho0 * (1.0 - x_coord);
    Z0 = rho0 * x_coord;
    R = jet_var_r(order, R0);
    Z = jet_var_z(order, Z0);
    rho = jet_add(R, Z);
    one_plus_rho = jet_add_scalar(rho, 1.0);
    status = jet_pow_real(one_plus_rho, -0.5, q_jet);
    if (status != NSPROOF_KERNEL_OK) {
        return status;
    }
    status = jet_div(Z, rho, x_jet);
    if (status != NSPROOF_KERNEL_OK) {
        return status;
    }
    return NSPROOF_KERNEL_OK;
}

static int make_physical_qx_jets(
    double q_coord,
    double b_coord,
    int order,
    NsproofJet2 *r_jet,
    NsproofJet2 *z_jet,
    NsproofJet2 *q_jet,
    NsproofJet2 *x_jet
) {
    double rho2_value;
    double rho_value;
    double one_minus_b2;
    double r0;
    double z0;
    NsproofJet2 rho2;
    NsproofJet2 one_plus_rho2;
    NsproofJet2 z2;
    int status;

    if (r_jet == NULL || z_jet == NULL || q_jet == NULL || x_jet == NULL) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    if (!check_finite(q_coord) || !check_finite(b_coord)) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }
    if (!(q_coord > 0.0) || !(q_coord < 1.0) || b_coord < -1.0 || b_coord > 1.0) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }

    rho2_value = 1.0 / (q_coord * q_coord) - 1.0;
    one_minus_b2 = 1.0 - b_coord * b_coord;
    if (!(rho2_value > 0.0) || one_minus_b2 < 0.0 || !check_finite(rho2_value)) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }
    rho_value = sqrt(rho2_value);
    r0 = rho_value * sqrt(one_minus_b2);
    z0 = rho_value * b_coord;
    if (!(r0 > 0.0) || !check_finite(r0) || !check_finite(z0)) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }

    *r_jet = jet_var_r(order, r0);
    *z_jet = jet_var_z(order, z0);
    rho2 = jet_add(jet_mul(*r_jet, *r_jet), jet_mul(*z_jet, *z_jet));
    one_plus_rho2 = jet_add_scalar(rho2, 1.0);
    status = jet_pow_real(one_plus_rho2, -0.5, q_jet);
    if (status != NSPROOF_KERNEL_OK) {
        return status;
    }
    z2 = jet_mul(*z_jet, *z_jet);
    status = jet_div(z2, rho2, x_jet);
    if (status != NSPROOF_KERNEL_OK) {
        return status;
    }
    return NSPROOF_KERNEL_OK;
}

static int weighted_coeff_jet(
    int order,
    NsproofJet2 q_jet,
    NsproofJet2 x_jet,
    double q0,
    double q1,
    double x0,
    double x1,
    double alpha,
    int kq,
    int kx,
    NsproofJet2 *out
) {
    NsproofJet2 tq;
    NsproofJet2 tx;
    NsproofJet2 t_q;
    NsproofJet2 t_x;
    NsproofJet2 q_alpha;
    int status;

    if (out == NULL) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    if (!check_order(order)) {
        return NSPROOF_KERNEL_BAD_ORDER;
    }
    if (kq < 0 || kx < 0) {
        return NSPROOF_KERNEL_BAD_INDEX;
    }
    if (q1 == q0 || x1 == x0) {
        return NSPROOF_KERNEL_DEGENERATE_INTERVAL;
    }
    if (
        !check_finite(q0) ||
        !check_finite(q1) ||
        !check_finite(x0) ||
        !check_finite(x1) ||
        !check_finite(alpha)
    ) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }
    tq = jet_scale(jet_add_scalar(jet_scale(q_jet, 2.0), -q0 - q1), 1.0 / (q1 - q0));
    tx = jet_scale(jet_add_scalar(jet_scale(x_jet, 2.0), -x0 - x1), 1.0 / (x1 - x0));
    status = jet_cheb_t(kq, tq, &t_q);
    if (status != NSPROOF_KERNEL_OK) {
        return status;
    }
    status = jet_cheb_t(kx, tx, &t_x);
    if (status != NSPROOF_KERNEL_OK) {
        return status;
    }
    status = jet_pow_real(q_jet, alpha, &q_alpha);
    if (status != NSPROOF_KERNEL_OK) {
        return status;
    }
    *out = jet_mul(q_alpha, jet_mul(t_q, t_x));
    if (!jet_is_finite(out)) {
        return NSPROOF_KERNEL_NONFINITE_OUTPUT;
    }
    return NSPROOF_KERNEL_OK;
}

static int rz_weighted_coeff_partials_one(
    int max_order,
    double q_coord,
    double x_coord,
    double q0,
    double q1,
    double x0,
    double x1,
    double alpha,
    int kq,
    int kx,
    double *out
) {
    NsproofJet2 q_jet;
    NsproofJet2 x_jet;
    NsproofJet2 tq;
    NsproofJet2 tx;
    NsproofJet2 t_q;
    NsproofJet2 t_x;
    NsproofJet2 q_alpha;
    NsproofJet2 basis;
    NsproofJet2 weighted;
    int status;
    int total;
    int dR;
    int out_index = 0;

    if (out == NULL) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    if (!check_order(max_order)) {
        return NSPROOF_KERNEL_BAD_ORDER;
    }
    if (kq < 0 || kx < 0) {
        return NSPROOF_KERNEL_BAD_INDEX;
    }
    if (q1 == q0 || x1 == x0) {
        return NSPROOF_KERNEL_DEGENERATE_INTERVAL;
    }
    if (
        !check_finite(q0) ||
        !check_finite(q1) ||
        !check_finite(x0) ||
        !check_finite(x1) ||
        !check_finite(alpha) ||
        !check_finite(q_coord) ||
        !check_finite(x_coord)
    ) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }

    status = make_rz_qx_jets(q_coord, x_coord, max_order, &q_jet, &x_jet);
    if (status != NSPROOF_KERNEL_OK) {
        return status;
    }
    tq = jet_scale(jet_add_scalar(jet_scale(q_jet, 2.0), -q0 - q1), 1.0 / (q1 - q0));
    tx = jet_scale(jet_add_scalar(jet_scale(x_jet, 2.0), -x0 - x1), 1.0 / (x1 - x0));
    status = jet_cheb_t(kq, tq, &t_q);
    if (status != NSPROOF_KERNEL_OK) {
        return status;
    }
    status = jet_cheb_t(kx, tx, &t_x);
    if (status != NSPROOF_KERNEL_OK) {
        return status;
    }
    status = jet_pow_real(q_jet, alpha, &q_alpha);
    if (status != NSPROOF_KERNEL_OK) {
        return status;
    }
    basis = jet_mul(t_q, t_x);
    weighted = jet_mul(q_alpha, basis);
    if (!jet_is_finite(&weighted)) {
        return NSPROOF_KERNEL_NONFINITE_OUTPUT;
    }

    for (total = 0; total <= max_order; total++) {
        for (dR = 0; dR <= total; dR++) {
            int dZ = total - dR;
            double value = jet_partial(weighted, dR, dZ);
            if (!check_finite(value)) {
                return NSPROOF_KERNEL_NONFINITE_OUTPUT;
            }
            out[out_index++] = value;
        }
    }
    return NSPROOF_KERNEL_OK;
}

NSPROOF_EXPORT int nsproof_rz_weighted_coeff_partials_batch(
    int count,
    int max_order,
    const double *q,
    const double *x,
    const double *q0,
    const double *q1,
    const double *x0,
    const double *x1,
    const double *alpha,
    const int *kq,
    const int *kx,
    double *out_rz_partials,
    int *out_status
) {
    int i;
    int spec_count;
    int first_status = NSPROOF_KERNEL_OK;

    if (!check_order(max_order)) {
        return NSPROOF_KERNEL_BAD_ORDER;
    }
    if (count <= 0) {
        return NSPROOF_KERNEL_OK;
    }
    if (
        q == NULL ||
        x == NULL ||
        q0 == NULL ||
        q1 == NULL ||
        x0 == NULL ||
        x1 == NULL ||
        alpha == NULL ||
        kq == NULL ||
        kx == NULL ||
        out_rz_partials == NULL
    ) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }

    spec_count = rz_spec_count(max_order);
    for (i = 0; i < count; i++) {
        int j;
        int status;
        double *out = out_rz_partials + ((size_t)i * (size_t)spec_count);
        for (j = 0; j < spec_count; j++) {
            out[j] = 0.0;
        }
        status = rz_weighted_coeff_partials_one(
            max_order,
            q[i],
            x[i],
            q0[i],
            q1[i],
            x0[i],
            x1[i],
            alpha[i],
            kq[i],
            kx[i],
            out
        );
        if (out_status != NULL) {
            out_status[i] = status;
        }
        if (status != NSPROOF_KERNEL_OK && first_status == NSPROOF_KERNEL_OK) {
            first_status = status;
        }
    }

    return first_status;
}

static int compactified_residual_factors_c(
    int residual_kind,
    double q,
    double b,
    double p,
    double *fac_psi,
    double *fac_gamma
) {
    double x;
    double one_minus_x;
    double one_minus_q2;
    double rho2;
    double rho;
    double q_factor;
    double floor_value = 1e-14;

    if (fac_psi == NULL || fac_gamma == NULL) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    if (!check_finite(q) || !check_finite(b) || !check_finite(p)) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }
    if (residual_kind == 0) {
        *fac_psi = 1.0;
        *fac_gamma = 1.0;
        return NSPROOF_KERNEL_OK;
    }
    if (residual_kind == 1) {
        rho2 = 1.0 / (q * q) - 1.0;
        rho = sqrt(rho2 > 0.0 ? rho2 : 0.0);
        one_minus_x = 1.0 - b * b;
        if (one_minus_x < 0.0) {
            one_minus_x = 0.0;
        }
        q_factor = pow(q, 2.0 * p);
        *fac_psi = q_factor * rho * rho * rho * one_minus_x * one_minus_x;
        *fac_gamma = q_factor * rho * rho * one_minus_x;
        if (fabs(*fac_psi) < floor_value) {
            *fac_psi = floor_value;
        }
        if (fabs(*fac_gamma) < floor_value) {
            *fac_gamma = floor_value;
        }
        return NSPROOF_KERNEL_OK;
    }
    x = b * b;
    one_minus_x = 1.0 - x;
    if (one_minus_x < 0.0) {
        one_minus_x = 0.0;
    }
    one_minus_q2 = 1.0 - q * q;
    if (one_minus_q2 < 0.0) {
        one_minus_q2 = 0.0;
    }
    if (residual_kind == 2) {
        *fac_psi = b * one_minus_x * one_minus_x * pow(one_minus_q2, 2.5) * pow(q, p - 1.0);
        *fac_gamma = one_minus_x * one_minus_q2 * pow(q, p);
    } else if (residual_kind == 3) {
        *fac_psi = b * one_minus_x * one_minus_x * pow(one_minus_q2, 2.5) * pow(q, 2.0 * p - 3.0);
        *fac_gamma = one_minus_x * one_minus_q2 * pow(q, 2.0 * p - 2.0);
    } else {
        return NSPROOF_KERNEL_BAD_INDEX;
    }
    if (!check_finite(*fac_psi) || !check_finite(*fac_gamma)) {
        return NSPROOF_KERNEL_NONFINITE_OUTPUT;
    }
    if (fabs(*fac_psi) <= floor_value || fabs(*fac_gamma) <= floor_value) {
        return NSPROOF_KERNEL_DEGENERATE_INTERVAL;
    }
    return NSPROOF_KERNEL_OK;
}

static int pde_tail_coeff_column_one(
    int residual_kind,
    double gamma_value,
    double p,
    double q_coord,
    double b_coord,
    double psi_r,
    double psi_z,
    double swirl_value,
    double swirl_r,
    double swirl_z,
    double a_value,
    double a_r,
    double a_z,
    double q0,
    double q1,
    double x0,
    double x1,
    double alpha,
    int kq,
    int kx,
    int component,
    double *out_e_psi,
    double *out_e_gamma
) {
    const int order = 3;
    NsproofJet2 r_jet;
    NsproofJet2 z_jet;
    NsproofJet2 q_jet;
    NsproofJet2 x_jet;
    NsproofJet2 coeff;
    NsproofJet2 q_p;
    NsproofJet2 r2;
    NsproofJet2 dpsi;
    NsproofJet2 dgamma_jet;
    NsproofJet2 dpsi_r_jet;
    NsproofJet2 dpsi_z_jet;
    NsproofJet2 dgamma_r_jet;
    NsproofJet2 dgamma_z_jet;
    NsproofJet2 dpsi_rr_jet;
    NsproofJet2 dpsi_zz_jet;
    NsproofJet2 div_term;
    NsproofJet2 da;
    double r;
    double z;
    double dpsi_r;
    double dpsi_z;
    double dgamma_value;
    double dgamma_r;
    double dgamma_z;
    double da_value;
    double da_r_value;
    double da_z_value;
    double e_psi;
    double e_gamma;
    double fac_psi;
    double fac_gamma;
    int status;

    if (out_e_psi == NULL || out_e_gamma == NULL) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    if (
        !check_finite(gamma_value) ||
        !check_finite(p) ||
        !check_finite(psi_r) ||
        !check_finite(psi_z) ||
        !check_finite(swirl_value) ||
        !check_finite(swirl_r) ||
        !check_finite(swirl_z) ||
        !check_finite(a_value) ||
        !check_finite(a_r) ||
        !check_finite(a_z)
    ) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }
    if (component != 0 && component != 1) {
        return NSPROOF_KERNEL_BAD_INDEX;
    }

    status = make_physical_qx_jets(q_coord, b_coord, order, &r_jet, &z_jet, &q_jet, &x_jet);
    if (status != NSPROOF_KERNEL_OK) {
        return status;
    }
    status = weighted_coeff_jet(order, q_jet, x_jet, q0, q1, x0, x1, alpha, kq, kx, &coeff);
    if (status != NSPROOF_KERNEL_OK) {
        return status;
    }
    status = jet_pow_real(q_jet, p, &q_p);
    if (status != NSPROOF_KERNEL_OK) {
        return status;
    }
    r2 = jet_mul(r_jet, r_jet);
    if (component == 0) {
        dpsi = jet_mul(jet_mul(jet_mul(r2, z_jet), q_p), coeff);
        dgamma_jet = jet_zero(order);
    } else {
        dpsi = jet_zero(order);
        dgamma_jet = jet_mul(jet_mul(r2, q_p), coeff);
    }

    dpsi_r_jet = jet_dr(dpsi);
    dpsi_z_jet = jet_dz(dpsi);
    dgamma_r_jet = jet_dr(dgamma_jet);
    dgamma_z_jet = jet_dz(dgamma_jet);
    dpsi_rr_jet = jet_dr(dpsi_r_jet);
    dpsi_zz_jet = jet_dz(dpsi_z_jet);
    status = jet_div(dpsi_r_jet, r_jet, &div_term);
    if (status != NSPROOF_KERNEL_OK) {
        return status;
    }
    da = jet_add(jet_sub(dpsi_rr_jet, div_term), dpsi_zz_jet);

    r = r_jet.c[0][0];
    z = z_jet.c[0][0];
    dpsi_r = dpsi_r_jet.c[0][0];
    dpsi_z = dpsi_z_jet.c[0][0];
    dgamma_value = dgamma_jet.c[0][0];
    dgamma_r = dgamma_r_jet.c[0][0];
    dgamma_z = dgamma_z_jet.c[0][0];
    da_value = da.c[0][0];
    da_r_value = jet_dr(da).c[0][0];
    da_z_value = jet_dz(da).c[0][0];

    e_psi =
        (1.0 - gamma_value) * r * r * da_value
        + gamma_value * r * r * r * da_r_value
        + gamma_value * z * r * r * da_z_value
        + r * (dpsi_r * a_z + psi_r * da_z_value - dpsi_z * a_r - psi_z * da_r_value)
        + 2.0 * dpsi_z * a_value
        + 2.0 * psi_z * da_value
        + 2.0 * (swirl_z * dgamma_value + swirl_value * dgamma_z);
    e_gamma =
        (1.0 - 2.0 * gamma_value) * dgamma_value
        + gamma_value * (r * dgamma_r + z * dgamma_z)
        + (dpsi_r * swirl_z + psi_r * dgamma_z - dpsi_z * swirl_r - psi_z * dgamma_r) / r;

    status = compactified_residual_factors_c(residual_kind, q_coord, b_coord, p, &fac_psi, &fac_gamma);
    if (status != NSPROOF_KERNEL_OK) {
        return status;
    }
    *out_e_psi = e_psi / fac_psi;
    *out_e_gamma = e_gamma / fac_gamma;
    if (!check_finite(*out_e_psi) || !check_finite(*out_e_gamma)) {
        return NSPROOF_KERNEL_NONFINITE_OUTPUT;
    }
    return NSPROOF_KERNEL_OK;
}

NSPROOF_EXPORT int nsproof_pde_tail_coeff_columns_batch(
    int count,
    int residual_kind,
    double gamma_value,
    double p,
    double q,
    double b,
    double psi_r,
    double psi_z,
    double swirl,
    double swirl_r,
    double swirl_z,
    double a_value,
    double a_r,
    double a_z,
    const double *q0,
    const double *q1,
    const double *x0,
    const double *x1,
    const double *alpha,
    const int *kq,
    const int *kx,
    const int *component,
    double *out_e_psi,
    double *out_e_gamma,
    int *out_status
) {
    int i;
    int first_status = NSPROOF_KERNEL_OK;

    if (count <= 0) {
        return NSPROOF_KERNEL_OK;
    }
    if (
        q0 == NULL ||
        q1 == NULL ||
        x0 == NULL ||
        x1 == NULL ||
        alpha == NULL ||
        kq == NULL ||
        kx == NULL ||
        component == NULL ||
        out_e_psi == NULL ||
        out_e_gamma == NULL
    ) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    for (i = 0; i < count; i++) {
        int status = pde_tail_coeff_column_one(
            residual_kind,
            gamma_value,
            p,
            q,
            b,
            psi_r,
            psi_z,
            swirl,
            swirl_r,
            swirl_z,
            a_value,
            a_r,
            a_z,
            q0[i],
            q1[i],
            x0[i],
            x1[i],
            alpha[i],
            kq[i],
            kx[i],
            component[i],
            &out_e_psi[i],
            &out_e_gamma[i]
        );
        if (out_status != NULL) {
            out_status[i] = status;
        }
        if (status != NSPROOF_KERNEL_OK && first_status == NSPROOF_KERNEL_OK) {
            first_status = status;
        }
    }
    return first_status;
}

NSPROOF_EXPORT int nsproof_stage0_prediction_scan_batch(
    int row_count,
    int column_count,
    int alpha_count,
    const double *jacobian_rows,
    const double *residuals,
    const double *step,
    const double *alphas,
    double *out_l2,
    double *out_max_abs,
    double *out_objective,
    int *out_status
) {
    int alpha_index;
    int row;
    int col;
    int first_status = NSPROOF_KERNEL_OK;

    if (row_count < 0 || column_count < 0 || alpha_count < 0) {
        return NSPROOF_KERNEL_BAD_INDEX;
    }
    if (alpha_count == 0) {
        return NSPROOF_KERNEL_OK;
    }
    if (
        jacobian_rows == NULL ||
        residuals == NULL ||
        step == NULL ||
        alphas == NULL ||
        out_l2 == NULL ||
        out_max_abs == NULL ||
        out_objective == NULL
    ) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }

    for (alpha_index = 0; alpha_index < alpha_count; alpha_index++) {
        double alpha = alphas[alpha_index];
        long double sumsq = 0.0L;
        double max_abs = 0.0;
        int status = NSPROOF_KERNEL_OK;

        if (!check_finite(alpha)) {
            status = NSPROOF_KERNEL_NONFINITE_INPUT;
        }
        for (row = 0; row < row_count && status == NSPROOF_KERNEL_OK; row++) {
            long double value = (long double)residuals[row];
            if (!check_finite(residuals[row])) {
                status = NSPROOF_KERNEL_NONFINITE_INPUT;
                break;
            }
            for (col = 0; col < column_count; col++) {
                double j_value = jacobian_rows[row * column_count + col];
                double step_value = step[col];
                if (!check_finite(j_value) || !check_finite(step_value)) {
                    status = NSPROOF_KERNEL_NONFINITE_INPUT;
                    break;
                }
                value += (long double)alpha * (long double)j_value * (long double)step_value;
            }
            if (status != NSPROOF_KERNEL_OK) {
                break;
            }
            if (!isfinite((double)value)) {
                status = NSPROOF_KERNEL_NONFINITE_OUTPUT;
                break;
            }
            {
                long double abs_value = fabsl(value);
                if (abs_value > (long double)max_abs) {
                    max_abs = (double)abs_value;
                }
                sumsq += value * value;
            }
            if (!isfinite((double)sumsq)) {
                status = NSPROOF_KERNEL_NONFINITE_OUTPUT;
                break;
            }
        }

        if (status == NSPROOF_KERNEL_OK) {
            long double objective = 0.5L * sumsq;
            long double l2 = sqrtl(sumsq);
            if (!isfinite((double)objective) || !isfinite((double)l2)) {
                status = NSPROOF_KERNEL_NONFINITE_OUTPUT;
            } else {
                out_l2[alpha_index] = (double)l2;
                out_max_abs[alpha_index] = max_abs;
                out_objective[alpha_index] = (double)objective;
            }
        }
        if (status != NSPROOF_KERNEL_OK) {
            out_l2[alpha_index] = 0.0;
            out_max_abs[alpha_index] = 0.0;
            out_objective[alpha_index] = 0.0;
            if (first_status == NSPROOF_KERNEL_OK) {
                first_status = status;
            }
        }
        if (out_status != NULL) {
            out_status[alpha_index] = status;
        }
    }
    return first_status;
}

NSPROOF_EXPORT int nsproof_tail_exact_residual(
    int coeff_count,
    int residual_kind,
    double gamma_value,
    double p,
    double B,
    double q,
    double b,
    const double *coeff,
    const double *q0,
    const double *q1,
    const double *x0,
    const double *x1,
    const double *alpha,
    const int *kq,
    const int *kx,
    const int *component,
    double *out_e_psi,
    double *out_e_gamma,
    int *out_status
) {
    const int order = 3;
    NsproofJet2 r_jet;
    NsproofJet2 z_jet;
    NsproofJet2 q_jet;
    NsproofJet2 x_jet;
    NsproofJet2 f_total;
    NsproofJet2 g_total;
    NsproofJet2 q_p;
    NsproofJet2 r2;
    NsproofJet2 psi;
    NsproofJet2 swirl;
    NsproofJet2 psi_r;
    NsproofJet2 psi_z;
    NsproofJet2 swirl_r;
    NsproofJet2 swirl_z;
    NsproofJet2 a;
    NsproofJet2 a_r;
    NsproofJet2 a_z;
    NsproofJet2 div_term;
    NsproofJet2 e_psi_jet;
    NsproofJet2 e_gamma_jet;
    NsproofJet2 gamma_transport;
    NsproofJet2 gamma_nonlinear;
    double fac_psi;
    double fac_gamma;
    int i;
    int status;

    if (out_e_psi == NULL || out_e_gamma == NULL) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    if (coeff_count < 0) {
        return NSPROOF_KERNEL_BAD_INDEX;
    }
    if (
        coeff_count > 0 &&
        (
            coeff == NULL ||
            q0 == NULL ||
            q1 == NULL ||
            x0 == NULL ||
            x1 == NULL ||
            alpha == NULL ||
            kq == NULL ||
            kx == NULL ||
            component == NULL
        )
    ) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    if (!check_finite(gamma_value) || !check_finite(p) || !check_finite(B)) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }

    status = make_physical_qx_jets(q, b, order, &r_jet, &z_jet, &q_jet, &x_jet);
    if (status != NSPROOF_KERNEL_OK) {
        if (out_status != NULL) {
            *out_status = status;
        }
        return status;
    }
    f_total = jet_const(order, 0.5);
    g_total = jet_const(order, B);
    for (i = 0; i < coeff_count; i++) {
        NsproofJet2 term;
        if (!check_finite(coeff[i])) {
            status = NSPROOF_KERNEL_NONFINITE_INPUT;
            break;
        }
        if (component[i] != 0 && component[i] != 1) {
            status = NSPROOF_KERNEL_BAD_INDEX;
            break;
        }
        status = weighted_coeff_jet(order, q_jet, x_jet, q0[i], q1[i], x0[i], x1[i], alpha[i], kq[i], kx[i], &term);
        if (status != NSPROOF_KERNEL_OK) {
            break;
        }
        term = jet_scale(term, coeff[i]);
        if (component[i] == 0) {
            f_total = jet_add(f_total, term);
        } else {
            g_total = jet_add(g_total, term);
        }
    }
    if (status != NSPROOF_KERNEL_OK) {
        if (out_status != NULL) {
            *out_status = status;
        }
        return status;
    }

    status = jet_pow_real(q_jet, p, &q_p);
    if (status != NSPROOF_KERNEL_OK) {
        if (out_status != NULL) {
            *out_status = status;
        }
        return status;
    }
    r2 = jet_mul(r_jet, r_jet);
    psi = jet_mul(jet_mul(jet_mul(r2, z_jet), q_p), f_total);
    swirl = jet_mul(jet_mul(r2, q_p), g_total);
    psi_r = jet_dr(psi);
    psi_z = jet_dz(psi);
    swirl_r = jet_dr(swirl);
    swirl_z = jet_dz(swirl);
    status = jet_div(psi_r, r_jet, &div_term);
    if (status != NSPROOF_KERNEL_OK) {
        if (out_status != NULL) {
            *out_status = status;
        }
        return status;
    }
    a = jet_add(jet_sub(jet_dr(psi_r), div_term), jet_dz(psi_z));
    a_r = jet_dr(a);
    a_z = jet_dz(a);

    e_psi_jet = jet_add(
        jet_add(
            jet_add(
                jet_scale(jet_mul(r2, a), 1.0 - gamma_value),
                jet_scale(jet_mul(jet_mul(r2, r_jet), a_r), gamma_value)
            ),
            jet_scale(jet_mul(jet_mul(z_jet, r2), a_z), gamma_value)
        ),
        jet_add(
            jet_add(
                jet_mul(r_jet, jet_sub(jet_mul(psi_r, a_z), jet_mul(psi_z, a_r))),
                jet_scale(jet_mul(psi_z, a), 2.0)
            ),
            jet_dz(jet_mul(swirl, swirl))
        )
    );
    gamma_transport = jet_add(
        jet_scale(swirl, 1.0 - 2.0 * gamma_value),
        jet_scale(jet_add(jet_mul(r_jet, swirl_r), jet_mul(z_jet, swirl_z)), gamma_value)
    );
    status = jet_div(jet_sub(jet_mul(psi_r, swirl_z), jet_mul(psi_z, swirl_r)), r_jet, &gamma_nonlinear);
    if (status != NSPROOF_KERNEL_OK) {
        if (out_status != NULL) {
            *out_status = status;
        }
        return status;
    }
    e_gamma_jet = jet_add(gamma_transport, gamma_nonlinear);
    if (!jet_is_finite(&e_psi_jet) || !jet_is_finite(&e_gamma_jet)) {
        status = NSPROOF_KERNEL_NONFINITE_OUTPUT;
        if (out_status != NULL) {
            *out_status = status;
        }
        return status;
    }

    status = compactified_residual_factors_c(residual_kind, q, b, p, &fac_psi, &fac_gamma);
    if (status != NSPROOF_KERNEL_OK) {
        if (out_status != NULL) {
            *out_status = status;
        }
        return status;
    }
    *out_e_psi = e_psi_jet.c[0][0] / fac_psi;
    *out_e_gamma = e_gamma_jet.c[0][0] / fac_gamma;
    if (!check_finite(*out_e_psi) || !check_finite(*out_e_gamma)) {
        status = NSPROOF_KERNEL_NONFINITE_OUTPUT;
        if (out_status != NULL) {
            *out_status = status;
        }
        return status;
    }
    if (out_status != NULL) {
        *out_status = NSPROOF_KERNEL_OK;
    }
    return NSPROOF_KERNEL_OK;
}

NSPROOF_EXPORT int nsproof_rz_mortar_residual_terms_batch(
    int row_count,
    int term_count,
    double B,
    const double *row_q,
    const double *row_x,
    const int *row_dR,
    const int *row_dZ,
    const int *row_component,
    const int *term_row,
    const int *term_kind,
    const double *coeff,
    const double *q0,
    const double *q1,
    const double *x0,
    const double *x1,
    const double *alpha,
    const int *kq,
    const int *kx,
    const int *r_power,
    const int *z_power,
    double *out_residual,
    int *out_status
) {
    int row;
    int term;
    int first_status = NSPROOF_KERNEL_OK;

    if (row_count < 0 || term_count < 0) {
        return NSPROOF_KERNEL_BAD_INDEX;
    }
    if (!check_finite(B)) {
        return NSPROOF_KERNEL_NONFINITE_INPUT;
    }
    if (
        row_count > 0 &&
        (
            row_q == NULL ||
            row_x == NULL ||
            row_dR == NULL ||
            row_dZ == NULL ||
            row_component == NULL ||
            out_residual == NULL
        )
    ) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }
    if (
        term_count > 0 &&
        (
            term_row == NULL ||
            term_kind == NULL ||
            coeff == NULL ||
            q0 == NULL ||
            q1 == NULL ||
            x0 == NULL ||
            x1 == NULL ||
            alpha == NULL ||
            kq == NULL ||
            kx == NULL ||
            r_power == NULL ||
            z_power == NULL
        )
    ) {
        return NSPROOF_KERNEL_NULL_POINTER;
    }

    for (row = 0; row < row_count; row++) {
        if (
            !check_finite(row_q[row]) ||
            !check_finite(row_x[row]) ||
            !check_order(row_dR[row]) ||
            !check_order(row_dZ[row]) ||
            row_dR[row] + row_dZ[row] > NSPROOF_JET_MAX_ORDER ||
            (row_component[row] != 0 && row_component[row] != 1)
        ) {
            return NSPROOF_KERNEL_NONFINITE_INPUT;
        }
        out_residual[row] = 0.0;
        if (row_dR[row] == 0 && row_dZ[row] == 0) {
            out_residual[row] += row_component[row] == 0 ? 0.5 : B;
        }
    }
    if (out_status != NULL) {
        for (term = 0; term < term_count; term++) {
            out_status[term] = NSPROOF_KERNEL_OK;
        }
    }

    for (term = 0; term < term_count; term++) {
        int target_row = term_row[term];
        int kind = term_kind[term];
        int dR;
        int dZ;
        double contribution = 0.0;
        int status = NSPROOF_KERNEL_OK;

        if (target_row < 0 || target_row >= row_count || (kind != 0 && kind != 1)) {
            status = NSPROOF_KERNEL_BAD_INDEX;
        } else if (!check_finite(coeff[term])) {
            status = NSPROOF_KERNEL_NONFINITE_INPUT;
        } else {
            dR = row_dR[target_row];
            dZ = row_dZ[target_row];
            if (kind == 0) {
                NsproofJet2 q_jet;
                NsproofJet2 x_jet;
                NsproofJet2 basis;
                status = make_rz_qx_jets(row_q[target_row], row_x[target_row], dR + dZ, &q_jet, &x_jet);
                if (status == NSPROOF_KERNEL_OK) {
                    status = weighted_coeff_jet(
                        dR + dZ,
                        q_jet,
                        x_jet,
                        q0[term],
                        q1[term],
                        x0[term],
                        x1[term],
                        alpha[term],
                        kq[term],
                        kx[term],
                        &basis
                    );
                }
                if (status == NSPROOF_KERNEL_OK) {
                    contribution = coeff[term] * jet_partial(basis, dR, dZ);
                }
            } else {
                double rho0;
                double R0;
                double Z0;
                int r_pow = r_power[term];
                int z_pow = z_power[term];
                if (r_pow < 0 || z_pow < 0) {
                    status = NSPROOF_KERNEL_BAD_INDEX;
                } else if (!(row_q[target_row] > 0.0) || !(row_q[target_row] < 1.0)) {
                    status = NSPROOF_KERNEL_NONFINITE_INPUT;
                } else {
                    rho0 = 1.0 / (row_q[target_row] * row_q[target_row]) - 1.0;
                    R0 = rho0 * (1.0 - row_x[target_row]);
                    Z0 = rho0 * row_x[target_row];
                    if (!check_finite(rho0) || !check_finite(R0) || !check_finite(Z0)) {
                        status = NSPROOF_KERNEL_NONFINITE_OUTPUT;
                    } else if (dR <= r_pow && dZ <= z_pow) {
                        contribution =
                            -coeff[term] *
                            falling((double)r_pow, dR) *
                            falling((double)z_pow, dZ) *
                            int_power(R0, r_pow - dR) *
                            int_power(Z0, z_pow - dZ);
                    }
                }
            }
        }
        if (status != NSPROOF_KERNEL_OK) {
            if (out_status != NULL) {
                out_status[term] = status;
            }
            if (first_status == NSPROOF_KERNEL_OK) {
                first_status = status;
            }
            continue;
        }
        out_residual[target_row] += contribution;
        if (!check_finite(out_residual[target_row])) {
            status = NSPROOF_KERNEL_NONFINITE_OUTPUT;
            if (out_status != NULL) {
                out_status[term] = status;
            }
            if (first_status == NSPROOF_KERNEL_OK) {
                first_status = status;
            }
        }
    }

    return first_status;
}
