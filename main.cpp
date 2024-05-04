#include <iostream>
#include "DemuxThread.h"
int main(int argc ,char **argv) {
    std::cout << "Hello, World!" << std::endl;
    DemuxThread demuxThread;
    demuxThread.Init(argv[1]);
    return 0;
}
