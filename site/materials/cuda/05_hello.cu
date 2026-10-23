#include "common.cuh"

__global__ void hello() {
    printf("block=%u thread=%u blockDim=%u gridDim=%u global=%u\n",
           blockIdx.x, threadIdx.x, blockDim.x, gridDim.x,
           blockIdx.x * blockDim.x + threadIdx.x);
}
int main() {
    device_info();
    hello<<<2, 4>>>(); // Eight logical threads, not eight reserved CUDA cores.
    CUDA_CHECK(cudaGetLastError());
    CUDA_CHECK(cudaDeviceSynchronize()); // Wait for execution and flush device printf.
    std::puts("PASS: hello completed; the order of printed threads is not guaranteed.");
}
