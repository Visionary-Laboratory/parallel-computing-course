// Classroom demo: read the five numbered stages from top to bottom.
// For repeatable CPU/GPU measurements, use 05_vector_add.cu instead.
#include <cuda_runtime.h>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <vector>

#define CUDA_CHECK(call) do { \
    cudaError_t error = (call); \
    if (error != cudaSuccess) { \
        std::fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, \
                     cudaGetErrorString(error)); \
        std::exit(EXIT_FAILURE); \
    } \
} while (0)

__global__ void add(const float* a, const float* b, float* c, size_t n) {
    size_t i = size_t(blockIdx.x) * blockDim.x + threadIdx.x;
    if (i < n) c[i] = a[i] + b[i];
}

int main() {
    // Change n to 0, 1, 256, 257 or 1003; save, recompile with nvcc, then run.
    constexpr size_t n = 1003;
    constexpr unsigned threads = 256;
    static_assert(n <= (1u << 24), "Keep this classroom example bounded.");
    static_assert(threads > 0 && threads <= 1024, "Invalid block size.");
    if (n == 0) {
        std::puts("PASS: N=0, empty result; no kernel launch.");
        return 0;
    }

    // 1. Prepare CPU input; values vary with i and are exactly representable.
    std::vector<float> a(n), b(n), c(n, std::numeric_limits<float>::quiet_NaN());
    for (size_t i = 0; i < n; ++i) {
        a[i] = float(int(i % 17) - 8);
        b[i] = float(int(i % 11) - 5) * 0.25f;
    }

    // 2. Allocate GPU arrays and upload inputs (H2D).
    const size_t bytes = n * sizeof(float);
    float *d_a = nullptr, *d_b = nullptr, *d_c = nullptr;
    CUDA_CHECK(cudaMalloc((void**)&d_a, bytes));
    CUDA_CHECK(cudaMalloc((void**)&d_b, bytes));
    CUDA_CHECK(cudaMalloc((void**)&d_c, bytes));
    CUDA_CHECK(cudaMemcpy(d_a, a.data(), bytes, cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(d_b, b.data(), bytes, cudaMemcpyHostToDevice));
    // NaN sentinels make missing writes visible during validation.
    CUDA_CHECK(cudaMemcpy(d_c, c.data(), bytes, cudaMemcpyHostToDevice));

    // 3. Launch, check submission, then wait for execution to finish.
    const unsigned blocks = unsigned(n / threads + (n % threads != 0));
    add<<<blocks, threads>>>(d_a, d_b, d_c, n);
    CUDA_CHECK(cudaGetLastError());
    CUDA_CHECK(cudaDeviceSynchronize());

    // 4. Download the result (D2H) and compare EVERY element with the CPU.
    CUDA_CHECK(cudaMemcpy(c.data(), d_c, bytes, cudaMemcpyDeviceToHost));
    size_t mismatches = 0;
    for (size_t i = 0; i < n; ++i) {
        const float expected = a[i] + b[i];
        if (!std::isfinite(c[i]) || c[i] != expected) {
            if (mismatches < 3)
                std::printf("Mismatch i=%zu: got=%g expected=%g\n", i, c[i], expected);
            ++mismatches;
        }
    }
    std::printf("N=%zu, blocks=%u, threads/block=%u, logical threads=%zu\n",
                n, blocks, threads, size_t(blocks) * threads);
    std::printf("c[0]=%g, c[%zu]=%g, checked=%zu, mismatches=%zu\n",
                c[0], n - 1, c[n - 1], n, mismatches);

    // 5. Free buffers only after their last use has completed.
    CUDA_CHECK(cudaFree(d_a));
    CUDA_CHECK(cudaFree(d_b));
    CUDA_CHECK(cudaFree(d_c));
    std::puts(mismatches == 0 ? "PASS: every element matches." : "FAIL");
    return mismatches == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
}
