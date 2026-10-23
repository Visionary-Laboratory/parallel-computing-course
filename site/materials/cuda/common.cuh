#pragma once
#include <cuda_runtime.h>
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <vector>

inline void cuda_check(cudaError_t err, const char* expr, const char* file, int line) {
    if (err != cudaSuccess) {
        std::fprintf(stderr, "%s:%d: %s: %s\n", file, line, expr, cudaGetErrorString(err));
        std::exit(EXIT_FAILURE);
    }
}
#define CUDA_CHECK(expr) cuda_check((expr), #expr, __FILE__, __LINE__)
inline void require(bool ok, const char* message) {
    if (!ok) { std::fprintf(stderr, "%s\n", message); std::exit(EXIT_FAILURE); }
}
inline void device_info() {
    cudaDeviceProp p{};
    CUDA_CHECK(cudaSetDevice(0));
    CUDA_CHECK(cudaGetDeviceProperties(&p, 0));
    int driver=0, runtime=0;
    CUDA_CHECK(cudaDriverGetVersion(&driver));
    CUDA_CHECK(cudaRuntimeGetVersion(&runtime));
    std::printf("Device=%s, CC=%d.%d, SMs=%d, driver=%d, runtime=%d\n",
                p.name, p.major, p.minor, p.multiProcessorCount, driver, runtime);
    require(p.major >= 7, "This teaching bundle targets compute capability >= 7.0.");
}
template<class T> struct DeviceBuffer {
    T* p=nullptr; size_t n=0;
    explicit DeviceBuffer(size_t count): n(count) {
        require(n <= std::numeric_limits<size_t>::max()/sizeof(T), "Allocation size overflow");
        if(n) CUDA_CHECK(cudaMalloc((void**)&p,n*sizeof(T)));
    }
    ~DeviceBuffer() { if(p) CUDA_CHECK(cudaFree(p)); }
    DeviceBuffer(const DeviceBuffer&)=delete;
    DeviceBuffer& operator=(const DeviceBuffer&)=delete;
    void upload(const std::vector<T>& x) {
        require(x.size()==n,"Upload size mismatch");
        if(n) CUDA_CHECK(cudaMemcpy(p,x.data(),n*sizeof(T),cudaMemcpyHostToDevice));
    }
    std::vector<T> download() const {
        std::vector<T> x(n);
        if(n) CUDA_CHECK(cudaMemcpy(x.data(),p,n*sizeof(T),cudaMemcpyDeviceToHost));
        return x;
    }
};
inline double check_close(const std::vector<float>& y,const std::vector<double>& ref,
                          double atol=1e-5,double rtol=1e-5) {
    require(y.size()==ref.size(),"Result size mismatch");
    double worst=0;
    for(size_t i=0;i<y.size();++i) {
        double error=std::abs(double(y[i])-ref[i]); worst=std::max(worst,error);
        if(!std::isfinite(y[i]) || !std::isfinite(ref[i]) || error>atol+rtol*std::abs(ref[i])) {
            std::fprintf(stderr,"Mismatch i=%zu: got %.9g, ref %.17g, error %.4g\n",i,double(y[i]),ref[i],error);
            std::exit(EXIT_FAILURE);
        }
    }
    return worst;
}
