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
