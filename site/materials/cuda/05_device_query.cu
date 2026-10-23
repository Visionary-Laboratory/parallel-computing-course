#include "common.cuh"

// Device properties are hardware limits; cudaDeviceGetLimit reports runtime settings.
int main() {
    device_info();
    cudaDeviceProp p{};
    CUDA_CHECK(cudaGetDeviceProperties(&p, 0));
    size_t free_bytes = 0, total_bytes = 0;
    CUDA_CHECK(cudaMemGetInfo(&free_bytes, &total_bytes));
    int max_blocks = 0;
    CUDA_CHECK(cudaDeviceGetAttribute(&max_blocks, cudaDevAttrMaxBlocksPerMultiprocessor, 0));
    std::printf("totalGlobalMem_bytes=%zu, totalGlobalMem_GiB=%.3f\n", p.totalGlobalMem, p.totalGlobalMem / double(1ull << 30));
    std::printf("free_memory_MiB=%.1f (snapshot, not a hardware constant)\n", free_bytes / double(1 << 20));
    std::printf("warpSize=%d\n", p.warpSize);
    std::printf("maxThreadsPerBlock=%d\n", p.maxThreadsPerBlock);
    std::printf("maxThreadsDim=(%d,%d,%d)\n", p.maxThreadsDim[0], p.maxThreadsDim[1], p.maxThreadsDim[2]);
    std::printf("maxGridSize=(%d,%d,%d) [blocks in each dimension, not resident blocks]\n", p.maxGridSize[0], p.maxGridSize[1], p.maxGridSize[2]);
    std::printf("maxThreadsPerMultiProcessor=%d\n", p.maxThreadsPerMultiProcessor);
    std::printf("maxBlocksPerMultiProcessor=%d\n", max_blocks);
    std::printf("sharedMemPerBlock_bytes=%zu\n", p.sharedMemPerBlock);
    std::printf("sharedMemPerBlockOptin_bytes=%zu\n", p.sharedMemPerBlockOptin);
    std::printf("sharedMemPerMultiprocessor_bytes=%zu\n", p.sharedMemPerMultiprocessor);
    std::printf("regsPerBlock=%d, regsPerMultiprocessor=%d [32-bit registers]\n", p.regsPerBlock, p.regsPerMultiprocessor);
    std::printf("l2CacheSize_bytes=%d, l2CacheSize_MiB=%.1f\n", p.l2CacheSize, p.l2CacheSize / double(1 << 20));
    std::printf("totalConstMem_bytes=%zu\n", p.totalConstMem);
    std::printf("asyncEngineCount=%d, concurrentKernels=%d, integrated=%d\n", p.asyncEngineCount, p.concurrentKernels, p.integrated);
    for (auto limit : {cudaLimitStackSize, cudaLimitPrintfFifoSize, cudaLimitMallocHeapSize}) {
        size_t value = 0;
        CUDA_CHECK(cudaDeviceGetLimit(&value, limit));
        const char* name = limit == cudaLimitStackSize ? "cudaLimitStackSize" :
                           limit == cudaLimitPrintfFifoSize ? "cudaLimitPrintfFifoSize" : "cudaLimitMallocHeapSize";
        std::printf("%s_bytes=%zu [current process setting]\n", name, value);
    }
    std::puts("PASS: device queried; no hardware or runtime setting was changed.");
}
