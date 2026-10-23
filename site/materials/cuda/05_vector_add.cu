#include "common.cuh"
#include <cerrno>
#include <cstring>

__global__ void add_stride(const float* a, const float* b, float* c, size_t n) {
    size_t step = size_t(blockDim.x) * gridDim.x;
    for (size_t i = size_t(blockIdx.x) * blockDim.x + threadIdx.x; i < n; i += step)
        c[i] = a[i] + b[i];
}

// Optimized single host thread; SIMD is allowed. noinline plus a volatile read on
// every call keeps repeated CPU work observable without making the arrays volatile.
#if defined(_MSC_VER)
__declspec(noinline)
#else
__attribute__((noinline))
#endif
void cpu_add(const float* a, const float* b, float* c, size_t n) {
    for (size_t i = 0; i < n; ++i) c[i] = a[i] + b[i];
}
volatile float cpu_sink = 0;

struct Stats { double lo, median, hi; };
Stats stats(std::array<double, 5> x) {
    std::sort(x.begin(), x.end());
    return {x[0], x[2], x[4]};
}
template<class F> Stats host_time(F operation, int repeats) {
    for (int i = 0; i < 3; ++i) operation();
    std::array<double, 5> times{};
    for (double& ms : times) {
        auto start = std::chrono::steady_clock::now();
        for (int i = 0; i < repeats; ++i) operation();
        auto stop = std::chrono::steady_clock::now();
        ms = std::chrono::duration<double, std::milli>(stop - start).count() / repeats;
    }
    return stats(times);
}
template<class F> Stats gpu_time(F launch, int repeats) {
    for (int i = 0; i < 3; ++i) launch();
    CUDA_CHECK(cudaGetLastError());
    CUDA_CHECK(cudaDeviceSynchronize());
    cudaEvent_t start, stop;
    CUDA_CHECK(cudaEventCreate(&start));
    CUDA_CHECK(cudaEventCreate(&stop));
    std::array<double, 5> times{};
    for (double& ms : times) {
        CUDA_CHECK(cudaEventRecord(start));
        for (int i = 0; i < repeats; ++i) launch();
        CUDA_CHECK(cudaGetLastError());
        CUDA_CHECK(cudaEventRecord(stop));
        CUDA_CHECK(cudaEventSynchronize(stop));
        float elapsed = 0;
        CUDA_CHECK(cudaEventElapsedTime(&elapsed, start, stop));
        ms = elapsed / repeats;
    }
    CUDA_CHECK(cudaEventDestroy(start));
    CUDA_CHECK(cudaEventDestroy(stop));
    return stats(times);
}

// Bounded teaching inputs also make byte counts and grid-stride increments safe.
size_t number(const char* value, size_t low, size_t high, const char* message) {
    require(value[0] >= '0' && value[0] <= '9', message);
    errno = 0;
    char* end = nullptr;
    unsigned long long parsed = std::strtoull(value, &end, 10);
    require(errno == 0 && *end == '\0' && parsed >= low && parsed <= high, message);
    return size_t(parsed);
}

void run(size_t n, int threads, int repeats, bool timed, const cudaDeviceProp& p) {
    if (!n) { std::puts("N=0: empty output; launch skipped; PASS"); return; }
    std::vector<float> a(n), b(n), got(n), cpu(n);
    std::vector<double> ref(n);
    for (size_t i = 0; i < n; ++i) {
        a[i] = float(int(i % 101) - 50) * 0.125f;
        b[i] = float(int(i % 37) - 18) * 0.25f;
        ref[i] = double(a[i]) + double(b[i]);
    }
    DeviceBuffer<float> da(n), db(n), dc(n);
    const size_t bytes = n * sizeof(float);
    // Same grid cap for all block-size candidates; query SM count, do not hardcode it.
    unsigned blocks = unsigned(std::min({n / threads + (n % threads != 0),
        size_t(p.multiProcessorCount) * 32, size_t(p.maxGridSize[0])}));
    auto launch = [&] { add_stride<<<blocks, threads>>>(da.p, db.p, dc.p, n); };
    auto download = [&] { CUDA_CHECK(cudaMemcpy(got.data(), dc.p, bytes, cudaMemcpyDeviceToHost)); };
    auto host = [&] { cpu_add(a.data(), b.data(), cpu.data(), n); cpu_sink = cpu[n / 2]; };
    auto end_to_end = [&] {
        da.upload(a); db.upload(b); launch();
        CUDA_CHECK(cudaGetLastError());
        download(); // Blocking D2H in the same default stream waits for completion.
    };
    da.upload(a); db.upload(b);
    CUDA_CHECK(cudaMemset(dc.p, 0xff, bytes)); // FP32 NaN sentinel detects unwritten output.
    launch(); CUDA_CHECK(cudaGetLastError()); CUDA_CHECK(cudaDeviceSynchronize());
    download(); host();
    check_close(cpu, ref, 0, 0);
    double error = check_close(got, ref, 0, 0);
    std::printf("N=%zu,threads=%d,blocks=%u,max_error=%.3g,PASS\n", n, threads, blocks, error);
    if (!timed) return;

    cudaFuncAttributes f{};
    int active_blocks = 0;
    CUDA_CHECK(cudaFuncGetAttributes(&f, add_stride));
    CUDA_CHECK(cudaOccupancyMaxActiveBlocksPerMultiprocessor(&active_blocks, add_stride, threads, 0));
    std::printf("kernel_regs_per_thread=%d,static_shared_bytes=%zu,active_blocks_per_SM=%d,theoretical_occupancy=%.3f\n",
        f.numRegs, f.sharedSizeBytes, active_blocks,
        double(active_blocks * threads) / p.maxThreadsPerMultiProcessor);
    // Each timing scope gets its own warm-up. No allocation or reference checking inside.
    Stats c = host_time(host, repeats);
    check_close(cpu, ref, 0, 0);
    Stats g = gpu_time(launch, repeats);
    download(); check_close(got, ref, 0, 0);
    Stats e = host_time(end_to_end, repeats);
    check_close(got, ref, 0, 0);
    require(c.median > 0 && g.median > 0 && e.median > 0, "Non-positive timing; increase repeats.");
    std::printf("RESULT,%zu,%d,%u,%d,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.3f,%.3f,%.3f,%.3f,%.6g\n",
        n, threads, blocks, repeats, c.lo, c.median, c.hi, g.lo, g.median, g.hi,
        e.lo, e.median, e.hi, 12.0 * n / (g.median * 1e6), c.median / g.median,
        c.median / e.median, 12.0 * n / (1 << 20), error);
}

int main(int argc, char** argv) {
    if (argc > 1 && std::strcmp(argv[1], "--help") == 0) {
        std::puts("vector_add [128|256|512] [N:0..16777216] [repeats:1..1000]\n"
                  "vector_add --check-only [128|256|512]\n"
                  "vector_add --sweep [repeats:1..1000]\n"
                  "Default: 256 threads, N=16777216, repeats=20; all modes run boundary checks.");
        return 0;
    }
    bool check_only = argc > 1 && std::strcmp(argv[1], "--check-only") == 0;
    bool sweep = argc > 1 && std::strcmp(argv[1], "--sweep") == 0;
    require(argc <= (check_only || sweep ? 3 : 4), "Too many arguments; use --help.");
    int threads = 256, repeats = 20;
    size_t n = 1 << 24;
    if (check_only) { if (argc > 2) threads = int(number(argv[2], 128, 512, "Invalid block size")); }
    else if (sweep) { if (argc > 2) repeats = int(number(argv[2], 1, 1000, "Invalid repeats")); }
    else {
        if (argc > 1) threads = int(number(argv[1], 128, 512, "Invalid block size"));
        if (argc > 2) n = number(argv[2], 0, 1 << 24, "N must be 0..16777216");
        if (argc > 3) repeats = int(number(argv[3], 1, 1000, "repeats must be 1..1000"));
    }
    require(threads == 128 || threads == 256 || threads == 512, "threads must be 128, 256 or 512");
    device_info();
    cudaDeviceProp p{};
    CUDA_CHECK(cudaGetDeviceProperties(&p, 0));
    std::printf("L2_MiB=%.1f,host_memory=pageable,batches=5,warmup_calls=3,CPU=single_thread_optimized\n", p.l2CacheSize / double(1 << 20));
    std::puts("Times exclude allocation, input generation and validation; event intervals may include submission gaps.");
    std::puts("HEADER,N,threads,blocks,repeats,cpu_min_ms,cpu_median_ms,cpu_max_ms,kernel_min_ms,kernel_median_ms,kernel_max_ms,e2e_min_ms,e2e_median_ms,e2e_max_ms,logical_GBps,cpu_over_kernel,cpu_over_e2e,working_set_MiB,max_error");
    const std::vector<int> configs = sweep ? std::vector<int>{128, 256, 512} : std::vector<int>{threads};
    for (int t : configs) {
        require(t <= p.maxThreadsPerBlock, "Block size exceeds this device limit");
        for (size_t k : {size_t(0), size_t(1), size_t(31), size_t(32), size_t(33),
                        size_t(127), size_t(128), size_t(129), size_t(255), size_t(256),
                        size_t(257), size_t(511), size_t(512), size_t(513), size_t(1003)})
            run(k, t, repeats, false, p);
    }
    if (check_only) return 0;
    if (sweep) {
        int rotation = 0;
        for (size_t k : {size_t(1003), size_t(1 << 16), size_t(1 << 20), size_t(1 << 22), size_t(1 << 24)}) {
            for (int i = 0; i < 3; ++i) run(k, configs[(i + rotation) % 3], repeats, true, p);
            ++rotation;
        }
    } else run(n, threads, repeats, true, p);
}
