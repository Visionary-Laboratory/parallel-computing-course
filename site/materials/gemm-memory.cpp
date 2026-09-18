// Lecture 02: single-thread CPU locality experiment, not a GPU benchmark.
// c++ -std=c++17 -O3 -ffp-contract=off gemm-memory.cpp -o gemm-memory
// ./gemm-memory --self-test
// ./gemm-memory 256 5
#include <algorithm>
#include <atomic>
#include <chrono>
#include <climits>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
static_assert(CHAR_BIT==8 && sizeof(float)==4 && std::numeric_limits<float>::is_iec559,
              "This experiment assumes IEEE binary32 float and 8-bit bytes.");

void ijk(const float* A,const float* B,float* C,int M,int N,int K,int) {
    for(int i=0;i<M;++i) for(int j=0;j<N;++j) {
        float sum=0;
        for(int k=0;k<K;++k) sum+=A[i*K+k]*B[k*N+j];
        C[i*N+j]=sum;
    }
}
void ikj(const float* A,const float* B,float* C,int M,int N,int K,int) {
    std::fill(C,C+M*N,0.0f);
    for(int i=0;i<M;++i) for(int k=0;k<K;++k) {
        const float a=A[i*K+k];
        for(int j=0;j<N;++j) C[i*N+j]+=a*B[k*N+j];
    }
}
void blocked(const float* A,const float* B,float* C,int M,int N,int K,int tile) {
    std::fill(C,C+M*N,0.0f);
    for(int ii=0;ii<M;ii+=tile) for(int jj=0;jj<N;jj+=tile)
        for(int kk=0;kk<K;kk+=tile)
            for(int i=ii;i<std::min(ii+tile,M);++i)
                for(int k=kk;k<std::min(kk+tile,K);++k) {
                    const float a=A[i*K+k];
                    for(int j=jj;j<std::min(jj+tile,N);++j)
                        C[i*N+j]+=a*B[k*N+j];
                }
}
using Kernel=void(*)(const float*,const float*,float*,int,int,int,int);
struct Variant { const char* name; int tile; Kernel kernel; };
const std::vector<Variant> variants={{"ijk",0,ijk},{"ikj",0,ikj},
    {"blocked",16,blocked},{"blocked",32,blocked},{"blocked",64,blocked}};

std::vector<double> reference(const std::vector<float>& A,const std::vector<float>& B,int M,int N,int K) {
    std::vector<double> result(M*N);
    for(int i=0;i<M;++i) for(int j=0;j<N;++j)
        for(int k=0;k<K;++k) result[i*N+j]+=double(A[i*K+k])*double(B[k*N+j]);
    return result;
}
double verify(const std::vector<float>& actual,const std::vector<double>& expected) {
    if(actual.size()!=expected.size()) throw std::runtime_error("Shape mismatch");
    double maxError=0;
    for(std::size_t i=0;i<actual.size();++i) {
        double error=std::abs(double(actual[i])-expected[i]);
        if(!std::isfinite(actual[i]) || error>1e-4+2e-4*std::abs(expected[i]))
            throw std::runtime_error("Numerical check failed at element "+std::to_string(i));
        maxError=std::max(maxError,error);
    }
    return maxError;
}
void inputs(std::vector<float>& A,std::vector<float>& B) {
    for(std::size_t i=0;i<A.size();++i) A[i]=float(int((i*17+3)%37)-18)/37.0f;
    for(std::size_t i=0;i<B.size();++i) B[i]=float(int((i*11+5)%41)-20)/41.0f;
}
void selfTest() {
    for(auto shape:std::vector<std::vector<int>>{{2,2,3},{7,5,19},{35,37,23},{1,1,1},{3,4,0}}) {
        int M=shape[0],N=shape[1],K=shape[2];
        std::vector<float>A(M*K),B(K*N),C(M*N);
        inputs(A,B);
        auto ref=reference(A,B,M,N,K);
        for(auto v:variants) {
            std::fill(C.begin(),C.end(),std::numeric_limits<float>::quiet_NaN());
            v.kernel(A.data(),B.data(),C.data(),M,N,K,v.tile);
            verify(C,ref);
            v.kernel(A.data(),B.data(),C.data(),M,N,K,v.tile);
            verify(C,ref); // C=AB, including on repeat; never C+=AB.
        }
    }
    std::vector<float>A{1,2,3,4,5,6},B{7,8,9,10,11,12},C(4);
    for(auto v:variants){v.kernel(A.data(),B.data(),C.data(),2,2,3,v.tile);verify(C,{58,64,139,154});}
}
int positive(const char* s,int max) {
    std::string value(s);std::size_t end=0;
    int n=std::stoi(value,&end);
    if(end!=value.size()||n<1||n>max)throw std::invalid_argument("Argument out of range");
    return n;
}
volatile double observedChecksum=0;
int main(int argc,char** argv) {
    try {
        selfTest();
        if(argc==2 && std::string(argv[1])=="--self-test") {
            std::cout<<"PASS: all 5 variants; rectangular, tile tails, signed inputs, overwrite, zero-K, known answer\n";return 0;
        }
        if(argc>3)throw std::invalid_argument("Usage: gemm-memory [N<=1024] [repeats<=15]");
        const int n=argc>1?positive(argv[1],1024):256;
        const int repeats=argc>2?positive(argv[2],15):5;
        std::vector<float>A(n*n),B(n*n),C(n*n);inputs(A,B);
        const auto expected=reference(A,B,n,n,n);
        std::vector<std::vector<double>> samples(variants.size());
        std::vector<double> errors(variants.size()),checksums(variants.size());
        // All variants share FP32 inputs and C=AB semantics. No explicit threading.
        // Allocation, inputs, reference, warmups, verification and checksums are untimed.
        // C-zeroing in ikj/blocked is part of those kernels and IS timed.
        for(auto v:variants){v.kernel(A.data(),B.data(),C.data(),n,n,n,v.tile);verify(C,expected);}
        for(int r=0;r<repeats;++r) for(std::size_t k=0;k<variants.size();++k) {
            const auto index=(k+r)%variants.size(); // Rotate order to reduce order bias.
            const auto v=variants[index];
            std::atomic_signal_fence(std::memory_order_seq_cst);
            const auto start=std::chrono::steady_clock::now();
            v.kernel(A.data(),B.data(),C.data(),n,n,n,v.tile);
            const auto stop=std::chrono::steady_clock::now();
            std::atomic_signal_fence(std::memory_order_seq_cst);
            samples[index].push_back(std::chrono::duration<double,std::milli>(stop-start).count());
            errors[index]=std::max(errors[index],verify(C,expected));
            double checksum=0;for(float x:C)checksum+=x;
            observedChecksum=checksum;checksums[index]=checksum;
        }
        std::cout<<"# compiler: "<<__VERSION__<<"\n# single thread; reused inputs; warmups=1 per variant; no DRAM counters\n";
        std::cout<<"variant,tile,N,repeats,min_ms,median_ms,max_ms,gflops,max_abs_error,checksum\n"<<std::setprecision(10);
        for(std::size_t i=0;i<variants.size();++i) {
            auto times=samples[i];std::sort(times.begin(),times.end());
            const auto middle=times.size()/2;
            const double median=times.size()%2?times[middle]:(times[middle-1]+times[middle])/2;
            std::cout<<variants[i].name<<','<<variants[i].tile<<','<<n<<','<<repeats<<','<<times.front()<<','<<median<<','<<times.back()<<','<<2.0*n*n*n/(median*1e6)<<','<<errors[i]<<','<<checksums[i]<<'\n';
        }
        return 0;
    }catch(const std::exception& e){std::cerr<<"ERROR: "<<e.what()<<'\n';return 1;}
}
