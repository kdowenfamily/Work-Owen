#include <iostream>
#include <thread>

std::mutex mtx;
static const int num_threads = 10;

//function to be called from a thread
void call_from_thread(int tid) {
    std::lock_guard<std::mutex> lock(mtx);
    std::cout << "Hello from thread " << tid << std::endl;
}

int main() {
    //Create a group of threads
    std::thread t[num_threads];

    call_from_thread(-99);

    //Launch a group of threads
    for (int i = 0; i < num_threads; ++i) {
        t[i] = std::thread(call_from_thread, i);
    }

    //Join the threads with the main thread
    for (int i = 0; i < num_threads; ++i) {
        t[i].join();
    }

    return 0;
}
