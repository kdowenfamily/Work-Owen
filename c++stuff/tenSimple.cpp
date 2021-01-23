#include <iostream>
#include <thread>

static const int num_threads = 10;

//function to be called from a thread
void call_from_thread() {
    std::cout << "Hello, World" << std::endl;
}

int main() {
    //Create a group of threads
    std::thread t[num_threads];

    //Launch a group of threads
    for (int i = 0; i < num_threads; ++i) {
        t[i] = std::thread(call_from_thread);
    }

    std::cout << "Launched from main\n";

    //Join the threads with the main thread
    for (int i = 0; i < num_threads; ++i) {
        t[i].join();
    }

    return 0;
}
