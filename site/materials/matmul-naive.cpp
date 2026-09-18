// Parallel Computing and Operator Programming, lecture 01.
// Sequential, row-major i-j-k baseline. No manual tiling, SIMD, or parallelism.
// Build: c++ -std=c++17 -O0 -g matmul-naive.cpp -o matmul
// Run:   ./matmul --self-test
//        ./matmul 128 3
#include <algorithm>
#include <chrono>
#include <climits>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

static_assert(CHAR_BIT == 8, "This lesson assumes 8-bit bytes.");
static_assert(sizeof(float) == 4 && std::numeric_limits<float>::is_iec559 &&
              std::numeric_limits<float>::digits == 24,
              "This lesson assumes IEEE 754 binary32 float.");

void matmul_naive(const std::vector<float>& A, const std::vector<float>& B,
                  std::vector<float>& C, int M, int N, int K) {
    if (M < 0 || N < 0 || K < 0 ||
        A.size() != static_cast<std::size_t>(M) * K ||
        B.size() != static_cast<std::size_t>(K) * N ||
        C.size() != static_cast<std::size_t>(M) * N)
        throw std::invalid_argument("Invalid dimensions or buffer sizes.");
    if (&A == &C || &B == &C)
        throw std::invalid_argument("Output must not alias an input vector.");
    for (int i = 0; i < M; ++i) {
        for (int j = 0; j < N; ++j) {
            float acc = 0.0f;
            for (int k = 0; k < K; ++k) {
                acc += A[i * K + k] * B[k * N + j];
            }
            C[i * N + j] = acc;
        }
    }
}

bool close_enough(double actual, double expected) {
    return std::isfinite(actual) &&
           std::abs(actual - expected) <= 1e-4 + 1e-4 * std::abs(expected);
}
void require_equal(const std::vector<float>& actual,
                   const std::vector<float>& expected) {
    if (actual.size() != expected.size()) throw std::runtime_error("Wrong shape.");
    for (std::size_t i = 0; i < actual.size(); ++i)
        if (!close_enough(actual[i], expected[i]))
            throw std::runtime_error("Incorrect result at element " + std::to_string(i));
}
void self_test() {
    // Rectangular dimensions expose stride errors that square tests can miss.
    std::vector<float> A{1,2,3,4,5,6}, B{7,8,9,10,11,12}, C(4, -999);
    matmul_naive(A, B, C, 2, 2, 3);
    require_equal(C, {58,64,139,154});
    // Calling again must overwrite, not accumulate a previous result.
    matmul_naive(A, B, C, 2, 2, 3);
    require_equal(C, {58,64,139,154});
    std::vector<float> identity{1,0,0,0,1,0,0,0,1};
    std::vector<float> values{1,-2,3,-4,5,-6}, output(6);
    matmul_naive(identity, values, output, 3, 2, 3);
    require_equal(output, values);
    std::vector<float> scalar(1);
    matmul_naive({-2}, {3}, scalar, 1, 1, 1);
    require_equal(scalar, {-6});
    std::vector<float> zero(4, -1);
    matmul_naive({}, {}, zero, 2, 2, 0);
    require_equal(zero, {0,0,0,0});
}
int integer_argument(const char* text, int maximum) {
    const std::string input(text); std::size_t used = 0;
    const int result = std::stoi(input, &used);
    if (used != input.size() || result < 1 || result > maximum)
        throw std::invalid_argument("Argument outside the allowed range.");
    return result;
}
int main(int argc, char** argv) {
    try {
        self_test();
        if (argc == 2 && std::string(argv[1]) == "--self-test") {
            std::cout << "PASS: rectangular, overwrite, identity, scalar, zero-K\n"
                      << "A(2x3) * B(3x2) = [58, 64; 139, 154]\n";
            return 0;
        }
        if (argc > 3) throw std::invalid_argument("Too many arguments.");
        const int n = argc >= 2 ? integer_argument(argv[1], 1024) : 128;
        const int repeats = argc >= 3 ? integer_argument(argv[2], 9) : 3;
        const std::size_t elements = static_cast<std::size_t>(n) * n;
        // Allocation and initialization are deliberately outside timing.
        std::vector<float> A(elements), B(elements), C(elements);
        for (std::size_t i = 0; i < elements; ++i) {
            A[i] = static_cast<float>((i * 17 + 3) % 19) / 19.0f;
            B[i] = static_cast<float>((i * 11 + 5) % 23) / 23.0f;
        }
        matmul_naive(A, B, C, n, n, n); // One warm-up, not reported.
        std::vector<double> timings;
        for (int r = 0; r < repeats; ++r) {
            const auto begin = std::chrono::steady_clock::now();
            matmul_naive(A, B, C, n, n, n);
            const auto end = std::chrono::steady_clock::now();
            timings.push_back(std::chrono::duration<double>(end - begin).count());
        }
        // Check representative output cells against double-precision dot products.
        for (int row : {0, n/2, n-1}) {
            for (int col : {0, n/2, n-1}) {
                double expected = 0;
                for (int k = 0; k < n; ++k)
                    expected += static_cast<double>(A[row*n+k]) * B[k*n+col];
                if (!close_enough(C[row*n+col], expected))
                    throw std::runtime_error("Benchmark result verification failed.");
            }
        }
        // Read the result outside timing so the calculated values are observable.
        double checksum = 0; for (float value : C) checksum += value;
        std::sort(timings.begin(), timings.end());
        const auto mid = timings.size()/2;
        const double median = timings.size()%2 ? timings[mid] : (timings[mid-1]+timings[mid])/2;
        const double operations = 2.0 * n * n * n;
        std::cout << std::setprecision(9)
                  << "compiler: " << __VERSION__ << '\n'
                  << "shape: " << n << " x " << n << " x " << n << "; float32\n"
                  << "buffers_bytes: " << 3 * elements * sizeof(float) << '\n'
                  << "operations_FLOPs: " << operations << " (2MNK convention)\n"
                  << "repeats: " << repeats << "; warmups: 1\n"
                  << "median_ms: " << median * 1000 << '\n'
                  << "achieved_GFLOP_per_s: " << operations / median / 1e9 << '\n'
                  << "checksum: " << checksum << '\n'
                  << "correctness: PASS\n"
                  << "Timing includes the function call and dimension checks; excludes allocation, initialization, validation and printing.\n"
                  << "Record your machine and build command. This is not a GPU benchmark.\n";
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << "\nUsage: ./matmul [N:1..1024] [repeats:1..9] or --self-test\n";
        return 1;
    }
}
