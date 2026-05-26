//! Prototype Chebyshev kernel boundary for NSProof.
//!
//! This file intentionally has no crate dependencies. It can be compiled
//! directly with:
//!
//!     rustc --crate-type cdylib -O native/rust/nsproof_kernel.rs -o libnsproof_kernel.dylib
//!
//! The exported functions mirror the scalar formulas in
//! validators/twochart_mortar_jacobian.py for Chebyshev basis derivatives and
//! weighted coefficient partials.

const ABI_VERSION: u32 = 1;

const OK: i32 = 0;
const ERR_BAD_ORDER: i32 = -1;
const ERR_NULL_OUT: i32 = -2;
const ERR_BAD_INTERVAL: i32 = -3;
const ERR_BAD_SIZE: i32 = -4;

#[no_mangle]
pub extern "C" fn nsproof_kernel_abi_version() -> u32 {
    ABI_VERSION
}

fn compute_cheb_table(count: usize, t: f64, max_order: u32) -> Result<Vec<[f64; 5]>, i32> {
    if max_order > 4 {
        return Err(ERR_BAD_ORDER);
    }

    let mut derivs = vec![[0.0_f64; 5]; count];
    if count == 0 {
        return Ok(derivs);
    }

    derivs[0][0] = 1.0;
    if count > 1 {
        derivs[1][0] = t;
        if max_order >= 1 {
            derivs[1][1] = 1.0;
        }
    }

    let max_m = max_order as usize;
    for n in 2..count {
        for m in 0..=max_m {
            let mut value = 2.0 * t * derivs[n - 1][m] - derivs[n - 2][m];
            if m > 0 {
                value += 2.0 * (m as f64) * derivs[n - 1][m - 1];
            }
            derivs[n][m] = value;
        }
    }

    Ok(derivs)
}

fn cheb_basis_derivative_at(k: usize, t: f64, order: u32) -> Result<f64, i32> {
    let count = k.checked_add(1).ok_or(ERR_BAD_SIZE)?;
    let table = compute_cheb_table(count, t, order)?;
    Ok(table[k][order as usize])
}

fn falling(value: f64, order: u32) -> f64 {
    let mut out = 1.0;
    for k in 0..order {
        out *= value - (k as f64);
    }
    out
}

fn binom(n: u32, k: u32) -> u32 {
    if k > n {
        return 0;
    }
    let kk = k.min(n - k);
    let mut out = 1_u32;
    for j in 1..=kk {
        out = out * (n + 1 - j) / j;
    }
    out
}

fn validate_partial_inputs(q0: f64, q1: f64, x0: f64, x1: f64, dq_order: u32, dx_order: u32) -> Result<(), i32> {
    if dq_order > 4 || dx_order > 4 {
        return Err(ERR_BAD_ORDER);
    }
    if q1 == q0 || x1 == x0 {
        return Err(ERR_BAD_INTERVAL);
    }
    Ok(())
}

fn cheb_basis_partial_internal(
    q0: f64,
    q1: f64,
    x0: f64,
    x1: f64,
    q: f64,
    x: f64,
    kq: usize,
    kx: usize,
    dq_order: u32,
    dx_order: u32,
) -> Result<f64, i32> {
    validate_partial_inputs(q0, q1, x0, x1, dq_order, dx_order)?;

    let tq = (2.0 * q - q0 - q1) / (q1 - q0);
    let tx = (2.0 * x - x0 - x1) / (x1 - x0);
    let q_value = cheb_basis_derivative_at(kq, tq, dq_order)?;
    let x_value = cheb_basis_derivative_at(kx, tx, dx_order)?;
    let q_scale = (2.0 / (q1 - q0)).powi(dq_order as i32);
    let x_scale = (2.0 / (x1 - x0)).powi(dx_order as i32);

    Ok(q_value * x_value * q_scale * x_scale)
}

fn weighted_cheb_coeff_partial_internal(
    q0: f64,
    q1: f64,
    x0: f64,
    x1: f64,
    alpha: f64,
    q: f64,
    x: f64,
    kq: usize,
    kx: usize,
    dq_order: u32,
    dx_order: u32,
) -> Result<f64, i32> {
    validate_partial_inputs(q0, q1, x0, x1, dq_order, dx_order)?;

    let mut total = 0.0;
    for i in 0..=dq_order {
        let q_weight = falling(alpha, i) * q.powf(alpha - (i as f64));
        let basis_partial = cheb_basis_partial_internal(q0, q1, x0, x1, q, x, kq, kx, dq_order - i, dx_order)?;
        total += (binom(dq_order, i) as f64) * q_weight * basis_partial;
    }
    Ok(total)
}

#[no_mangle]
pub extern "C" fn nsproof_cheb_basis_values(count: usize, t: f64, order: u32, out: *mut f64) -> i32 {
    if count == 0 {
        return OK;
    }
    if out.is_null() {
        return ERR_NULL_OUT;
    }

    let table = match compute_cheb_table(count, t, order) {
        Ok(table) => table,
        Err(code) => return code,
    };

    unsafe {
        for n in 0..count {
            *out.add(n) = table[n][order as usize];
        }
    }
    OK
}

#[no_mangle]
pub extern "C" fn nsproof_cheb_basis_table_order4(count: usize, t: f64, out: *mut f64) -> i32 {
    let len = match count.checked_mul(5) {
        Some(value) => value,
        None => return ERR_BAD_SIZE,
    };
    if len == 0 {
        return OK;
    }
    if out.is_null() {
        return ERR_NULL_OUT;
    }

    let table = match compute_cheb_table(count, t, 4) {
        Ok(table) => table,
        Err(code) => return code,
    };

    unsafe {
        for n in 0..count {
            for order in 0..5 {
                *out.add(n * 5 + order) = table[n][order];
            }
        }
    }
    OK
}

#[no_mangle]
pub extern "C" fn nsproof_cheb_basis_value(k: usize, t: f64, order: u32) -> f64 {
    match cheb_basis_derivative_at(k, t, order) {
        Ok(value) => value,
        Err(_) => f64::NAN,
    }
}

#[no_mangle]
pub extern "C" fn nsproof_cheb_basis_partial(
    q0: f64,
    q1: f64,
    x0: f64,
    x1: f64,
    q: f64,
    x: f64,
    kq: usize,
    kx: usize,
    dq_order: u32,
    dx_order: u32,
) -> f64 {
    match cheb_basis_partial_internal(q0, q1, x0, x1, q, x, kq, kx, dq_order, dx_order) {
        Ok(value) => value,
        Err(_) => f64::NAN,
    }
}

#[no_mangle]
pub extern "C" fn nsproof_weighted_cheb_coeff_partial(
    q0: f64,
    q1: f64,
    x0: f64,
    x1: f64,
    alpha: f64,
    q: f64,
    x: f64,
    kq: usize,
    kx: usize,
    dq_order: u32,
    dx_order: u32,
) -> f64 {
    match weighted_cheb_coeff_partial_internal(q0, q1, x0, x1, alpha, q, x, kq, kx, dq_order, dx_order) {
        Ok(value) => value,
        Err(_) => f64::NAN,
    }
}

#[no_mangle]
pub extern "C" fn nsproof_weighted_cheb_coeff_partials(
    q0: f64,
    q1: f64,
    x0: f64,
    x1: f64,
    alpha: f64,
    q: f64,
    x: f64,
    kq_count: usize,
    kx_count: usize,
    dq_order: u32,
    dx_order: u32,
    out: *mut f64,
) -> i32 {
    let len = match kq_count.checked_mul(kx_count) {
        Some(value) => value,
        None => return ERR_BAD_SIZE,
    };
    if len == 0 {
        return OK;
    }
    if out.is_null() {
        return ERR_NULL_OUT;
    }
    if let Err(code) = validate_partial_inputs(q0, q1, x0, x1, dq_order, dx_order) {
        return code;
    }

    let tq = (2.0 * q - q0 - q1) / (q1 - q0);
    let tx = (2.0 * x - x0 - x1) / (x1 - x0);
    let x_scale = (2.0 / (x1 - x0)).powi(dx_order as i32);
    let x_table = match compute_cheb_table(kx_count, tx, dx_order) {
        Ok(table) => table,
        Err(code) => return code,
    };

    unsafe {
        for index in 0..len {
            *out.add(index) = 0.0;
        }
    }

    for i in 0..=dq_order {
        let q_order = dq_order - i;
        let q_scale = (2.0 / (q1 - q0)).powi(q_order as i32);
        let q_weight = falling(alpha, i) * q.powf(alpha - (i as f64));
        let multiplier = (binom(dq_order, i) as f64) * q_weight * q_scale * x_scale;
        let q_table = match compute_cheb_table(kq_count, tq, q_order) {
            Ok(table) => table,
            Err(code) => return code,
        };

        unsafe {
            for kq in 0..kq_count {
                let q_value = q_table[kq][q_order as usize];
                for kx in 0..kx_count {
                    let x_value = x_table[kx][dx_order as usize];
                    *out.add(kq * kx_count + kx) += multiplier * q_value * x_value;
                }
            }
        }
    }

    OK
}
