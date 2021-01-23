#include <iostream>
#include <thread>


static const int num_threads = 10;

//function to be called from a thread
void call_from_thread(int tid) {
    std::cout << "Hello from thread " << tid << std::endl;
}

int main() {
    //Create a group of threads
    std::thread t[num_threads];

    //Launch a group of threads
    for (int i = 0; i < num_threads; ++i) {
        t[i] = std::thread(call_from_thread, i);
    }

    std::cout << "Hello from the main\n";

    //Join the threads with the main thread
    for (int i = 0; i < num_threads; ++i) {
        t[i].join();
    }

    return 0;
}
