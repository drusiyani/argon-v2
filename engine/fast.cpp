// fast.cpp: the speed-critical parts of Argon's backtest, in C++.
// 1) the minute-by-minute trade walker, in C++ for speed.
// It plays one trade out on 1-minute candles: finds the minute the limit order filled, then checks every minute,
// stop before target, until the stop, the target or the 15:55 New York flat. It tracks two versions of the trade at
// once: one that leaves the stop alone ("none") and one that moves it to entry after +1R ("be1").
// This is a line-for-line port of walk1m() in backtest_core.py, which stays as the fallback and the reference.
#include <algorithm>
#include <cmath>
extern "C" {

// out[0..4]  = kind, R, exit time, exit price, exit 5m index   (version that leaves the stop alone)
// out[5..9]  = the same for the break-even version
// out[10..11]= best R reached (MFE), worst R (MAE)
// kind: 0 = closed at the flat, 1 = stopped, 2 = scratched at entry, 3 = hit target
int walk1m(const double* T, const double* O, const double* H, const double* L, const double* C, const int* K5, int n,
           const int* SD5, const int* SMIN5, int nbars, int eod_smin,
           double t0, int fill_sd, int d, double entry, double stop, double target, double* out) {
    if (n <= 0) return -1;
    const double risk = std::fabs(entry - stop);
    if (risk <= 0) return -2;
    int j = int(std::lower_bound(T, T + n, t0) - T);
    int jf = j;
    while (jf < n && T[jf] < t0 + 300) {
        if (d == -1 ? H[jf] >= entry : L[jf] <= entry) break;
        jf++;
    }
    if (jf >= n || T[jf] >= t0 + 300) jf = j;
    bool done[2] = {false, false};
    double st[2] = {stop, stop};
    double mfe = 0.0, mae = 0.0, t_none = 0.0;
    bool first = true;
    auto set = [&](int m, int kind, double R, double t, double px, int k) {
        double* o = out + 5 * m; o[0] = kind; o[1] = R; o[2] = t; o[3] = px; o[4] = k; done[m] = true;
        if (m == 0) t_none = t;
    };
    for (int i = jf; i < n; i++) {
        int kk = K5[i];
        if (kk < 0) continue;
        if (SD5[kk] != fill_sd || SMIN5[kk] >= eod_smin) {
            for (int m = 0; m < 2; m++) if (!done[m]) set(m, 0, (O[i] - entry) * d / risk, T[i], O[i], kk);
            break;
        }
        double fav = d == -1 ? L[i] : H[i];
        double adv = d == -1 ? H[i] : L[i];
        for (int m = 0; m < 2; m++) {
            if (done[m]) continue;
            double sp = st[m];
            if (d == -1 ? adv >= sp : adv <= sp) { set(m, sp == stop ? 1 : 2, (sp - entry) * d / risk, T[i], sp, kk); continue; }
            if (!first && (d == -1 ? fav <= target : fav >= target)) set(m, 3, std::fabs(target - entry) / risk, T[i], target, kk);
        }
        if (!done[0]) mae = std::min(mae, (adv - entry) * d / risk);
        if (!done[0] || (T[i] - t_none) <= 10800) mfe = std::max(mfe, (fav - entry) * d / risk);
        if (mfe >= 1.0) st[1] = entry;
        first = false;
        if (done[0] && done[1] && (T[i] - t_none) > 10800) break;
    }
    for (int m = 0; m < 2; m++) if (!done[m]) set(m, 0, (C[n - 1] - entry) * d / risk, T[n - 1], C[n - 1], nbars - 1);
    out[10] = mfe; out[11] = std::max(-1.0, mae);
    return 0;
}

// ---------------------------------------------------------------------------------------------------------------
// Reading HistData's 1-minute files. Each line looks like "20250103 093000;21420.5;21431.0;21418.25;21429.75;0"
// in New York local time, daylight saving included. Python's strptime + zoneinfo made this the slowest part of the
// whole backtest, so the parsing and the time zone maths happen here instead.
#include <cstdlib>
#include <cstring>
static long days_from_civil(int y, unsigned m, unsigned d) {           // days since 1970-01-01 (Howard Hinnant's method)
    y -= m <= 2; const long era = (y >= 0 ? y : y - 399) / 400; const unsigned yoe = unsigned(y - era * 400);
    const unsigned doy = (153 * (m + (m > 2 ? -3 : 9)) + 2) / 5 + d - 1; const unsigned doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    return era * 146097 + long(doe) - 719468;
}
static int weekday(long days) { long w = (days + 4) % 7; return int(w < 0 ? w + 7 : w); }       // 0 = Sunday
static long nth_sunday(int y, unsigned m, int n) { long d1 = days_from_civil(y, m, 1); int w = weekday(d1); return d1 + (7 - w) % 7 + 7 * (n - 1); }
// US daylight saving since 2007: from the 2nd Sunday of March 02:00 to the 1st Sunday of November 02:00, local time.
// Matches Python zoneinfo with fold=0: the repeated 1am hour in November counts as daylight time.
static long ny_to_utc(int y, unsigned mo, unsigned d, int hh, int mm, int ss) {
    long day = days_from_civil(y, mo, d); long local = day * 86400 + hh * 3600 + mm * 60 + ss;
    long start = nth_sunday(y, 3, 2) * 86400 + 3 * 3600, end = nth_sunday(y, 11, 1) * 86400 + 2 * 3600;
    bool dst = local >= start && local < end;
    return local + (dst ? 4 : 5) * 3600;
}
static int num(const char*& p, int digits) { int v = 0; for (int i = 0; i < digits; i++) v = v * 10 + (*p++ - '0'); return v; }
// Parse a whole CSV buffer. Returns the number of minutes written (never more than cap).
int parse_histdata(const char* buf, long len, double* T, double* O, double* H, double* L, double* C, long cap) {
    const char* p = buf; const char* e = buf + len; long n = 0;
    while (p < e && n < cap) {
        const char* line_end = (const char*)memchr(p, '\n', size_t(e - p)); if (!line_end) line_end = e;
        if (line_end - p >= 20 && p[8] == ' ') {
            const char* q = p; int y = num(q, 4), mo = num(q, 2), d = num(q, 2); q++; int hh = num(q, 2), mm = num(q, 2), ss = num(q, 2);
            if (*q == ';') {
                char* r; double o = strtod(q + 1, &r); double h = strtod(r + 1, &r); double l = strtod(r + 1, &r); double c = strtod(r + 1, &r);
                T[n] = double(ny_to_utc(y, mo, d, hh, mm, ss)); O[n] = o; H[n] = h; L[n] = l; C[n] = c; n++;
            }
        }
        p = line_end + 1;
    }
    return int(n);
}
// Group sorted 1-minute candles into 5-minute candles. Returns how many 5-minute candles were written.
int to_5m(const double* T, const double* O, const double* H, const double* L, const double* C, long n,
          double* T5, double* O5, double* H5, double* L5, double* C5) {
    long m = -1; double cur = -1;
    for (long i = 0; i < n; i++) {
        double k = std::floor(T[i] / 300.0) * 300.0;
        if (k != cur) { m++; cur = k; T5[m] = k; O5[m] = O[i]; H5[m] = H[i]; L5[m] = L[i]; C5[m] = C[i]; }
        else { if (H[i] > H5[m]) H5[m] = H[i]; if (L[i] < L5[m]) L5[m] = L[i]; C5[m] = C[i]; }
    }
    return int(m + 1);
}
}

// Sort 1-minute candles by time, breaking ties by open, high, low, close: the same order Python's tuple sort gives.
// (HistData's files list a few hundred minutes twice; this keeps those duplicates in exactly the order the Python
// version used, so the C++ and Python backtests give identical results.)
#include <vector>
#include <numeric>
extern "C" void sort_m1(double* T, double* O, double* H, double* L, double* C, long n) {
    std::vector<long> idx(n); std::iota(idx.begin(), idx.end(), 0);
    std::sort(idx.begin(), idx.end(), [&](long a, long b) {
        if (T[a] != T[b]) return T[a] < T[b]; if (O[a] != O[b]) return O[a] < O[b];
        if (H[a] != H[b]) return H[a] < H[b]; if (L[a] != L[b]) return L[a] < L[b]; return C[a] < C[b]; });
    double* cols[5] = {T, O, H, L, C};
    std::vector<double> tmp(n);
    for (double* c : cols) { for (long i = 0; i < n; i++) tmp[i] = c[idx[i]]; std::copy(tmp.begin(), tmp.end(), c); }
}
// Sort by time only, keeping file order for equal times (a stable sort). The 5-minute bars are built from this order.
extern "C" void stable_time_sort(double* T, double* O, double* H, double* L, double* C, long n) {
    std::vector<long> idx(n); std::iota(idx.begin(), idx.end(), 0);
    std::stable_sort(idx.begin(), idx.end(), [&](long a, long b) { return T[a] < T[b]; });
    double* cols[5] = {T, O, H, L, C};
    std::vector<double> tmp(n);
    for (double* c : cols) { for (long i = 0; i < n; i++) tmp[i] = c[idx[i]]; std::copy(tmp.begin(), tmp.end(), c); }
}
