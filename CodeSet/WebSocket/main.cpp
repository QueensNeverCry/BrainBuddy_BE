#include <uWebSockets/App.h>
#include <iostream>

int main() {
    uWS::App().get("/*", [](auto *res, auto *req) {
        res->end("Hello from uWebSockets!");
    }).listen(9001, [](auto *token) {
        if (token) {
            std::cout << "Server listening on port 9001" << std::endl;
        } else {
            std::cout << "Failed to listen on port 9001" << std::endl;
        }
    }).run();

    std::cout << "Server has stopped." << std::endl;
    return 0;
}
