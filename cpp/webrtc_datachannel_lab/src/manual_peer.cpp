#include <rtc/rtc.hpp>

#include <nlohmann/json.hpp>

#include <atomic>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <mutex>
#include <set>
#include <string>
#include <thread>

using json = nlohmann::json;
namespace fs = std::filesystem;

namespace {

struct Options {
    std::string role;
    fs::path signalDir = "runtime/webrtc-signal";
    std::string stun = "stun:stun.l.google.com:19302";
};

void printUsage(const char *argv0)
{
    std::cerr
        << "Usage:\n"
        << "  " << argv0 << " --role offer --signal-dir runtime/webrtc-signal\n"
        << "  " << argv0 << " --role answer --signal-dir runtime/webrtc-signal\n";
}

Options parseOptions(int argc, char **argv)
{
    Options options;
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--role" && i + 1 < argc) {
            options.role = argv[++i];
        } else if (arg == "--signal-dir" && i + 1 < argc) {
            options.signalDir = argv[++i];
        } else if (arg == "--stun" && i + 1 < argc) {
            options.stun = argv[++i];
        } else {
            throw std::runtime_error("Unknown or incomplete argument: " + arg);
        }
    }

    if (options.role != "offer" && options.role != "answer") {
        throw std::runtime_error("--role must be offer or answer");
    }
    return options;
}

std::string remoteRole(const std::string &role)
{
    return role == "offer" ? "answer" : "offer";
}

fs::path descriptionPath(const fs::path &dir, const std::string &role)
{
    return dir / (role + "_description.json");
}

fs::path candidatesPath(const fs::path &dir, const std::string &role)
{
    return dir / (role + "_candidates.jsonl");
}

void writeJsonFile(const fs::path &path, const json &value)
{
    fs::create_directories(path.parent_path());
    const fs::path tmp = path.string() + ".tmp";
    {
        std::ofstream out(tmp);
        out << value.dump(2) << "\n";
    }
    fs::rename(tmp, path);
}

json readJsonFile(const fs::path &path)
{
    std::ifstream in(path);
    json value;
    in >> value;
    return value;
}

void appendJsonLine(const fs::path &path, const json &value)
{
    fs::create_directories(path.parent_path());
    std::ofstream out(path, std::ios::app);
    out << value.dump() << "\n";
}

rtc::Configuration makeConfiguration(const Options &options)
{
    rtc::Configuration config;
    if (!options.stun.empty()) {
        config.iceServers.emplace_back(options.stun);
    }
    return config;
}

template <typename State>
void printState(const std::string &label, State state)
{
    std::cout << label << ": " << state << std::endl;
}

} // namespace

int main(int argc, char **argv)
{
    try {
        const Options options = parseOptions(argc, argv);
        const std::string otherRole = remoteRole(options.role);

        fs::create_directories(options.signalDir);
        rtc::InitLogger(rtc::LogLevel::Info);

        auto pc = std::make_shared<rtc::PeerConnection>(makeConfiguration(options));
        std::shared_ptr<rtc::DataChannel> dataChannel;
        std::mutex dataChannelMutex;
        std::atomic<bool> running = true;

        pc->onStateChange([](rtc::PeerConnection::State state) {
            printState("PeerConnection state", state);
        });

        pc->onGatheringStateChange([](rtc::PeerConnection::GatheringState state) {
            printState("ICE gathering state", state);
        });

        pc->onLocalDescription([&](rtc::Description description) {
            json message = {
                {"type", description.typeString()},
                {"sdp", std::string(description)},
            };
            writeJsonFile(descriptionPath(options.signalDir, options.role), message);
            std::cout << "Local description ready: "
                      << descriptionPath(options.signalDir, options.role) << std::endl;
        });

        pc->onLocalCandidate([&](rtc::Candidate candidate) {
            json message = {
                {"candidate", std::string(candidate)},
                {"mid", candidate.mid()},
            };
            appendJsonLine(candidatesPath(options.signalDir, options.role), message);
            std::cout << "Local candidate: " << candidate.mid() << std::endl;
        });

        auto setupDataChannel = [&](const std::shared_ptr<rtc::DataChannel> &dc) {
            dc->onOpen([dc]() {
                std::cout << "DataChannel open: " << dc->label() << std::endl;
                dc->send("hello from C++ " + dc->label());
            });

            dc->onClosed([]() {
                std::cout << "DataChannel closed" << std::endl;
            });

            dc->onMessage([](auto data) {
                if (std::holds_alternative<std::string>(data)) {
                    std::cout << "DataChannel message: " << std::get<std::string>(data) << std::endl;
                } else {
                    std::cout << "DataChannel binary message, bytes="
                              << std::get<rtc::binary>(data).size() << std::endl;
                }
            });
        };

        pc->onDataChannel([&](std::shared_ptr<rtc::DataChannel> dc) {
            std::cout << "Remote DataChannel received: " << dc->label() << std::endl;
            setupDataChannel(dc);
            std::lock_guard<std::mutex> lock(dataChannelMutex);
            dataChannel = std::move(dc);
        });

        if (options.role == "offer") {
            auto dc = pc->createDataChannel("chat");
            setupDataChannel(dc);
            std::lock_guard<std::mutex> lock(dataChannelMutex);
            dataChannel = std::move(dc);
        }

        std::thread signalingThread([&]() {
            bool remoteDescriptionApplied = false;
            std::set<std::string> appliedCandidates;

            while (running) {
                const fs::path remoteDescriptionPath = descriptionPath(options.signalDir, otherRole);
                if (!remoteDescriptionApplied && fs::exists(remoteDescriptionPath)) {
                    json message = readJsonFile(remoteDescriptionPath);
                    pc->setRemoteDescription(
                        rtc::Description(message.at("sdp").get<std::string>(),
                                         message.at("type").get<std::string>()));
                    remoteDescriptionApplied = true;
                    std::cout << "Remote description applied: " << remoteDescriptionPath << std::endl;
                }

                const fs::path remoteCandidatesPath = candidatesPath(options.signalDir, otherRole);
                if (remoteDescriptionApplied && fs::exists(remoteCandidatesPath)) {
                    std::ifstream in(remoteCandidatesPath);
                    std::string line;
                    while (std::getline(in, line)) {
                        if (line.empty() || appliedCandidates.count(line) != 0) {
                            continue;
                        }
                        json message = json::parse(line);
                        pc->addRemoteCandidate(
                            rtc::Candidate(message.at("candidate").get<std::string>(),
                                           message.at("mid").get<std::string>()));
                        appliedCandidates.insert(line);
                        std::cout << "Remote candidate applied: "
                                  << message.at("mid").get<std::string>() << std::endl;
                    }
                }

                std::this_thread::sleep_for(std::chrono::milliseconds(200));
            }
        });

        std::cout << "Role: " << options.role << std::endl;
        std::cout << "Signal directory: " << options.signalDir << std::endl;
        std::cout << "Type messages and press Enter to send over DataChannel." << std::endl;
        std::cout << "Type /quit to stop." << std::endl;

        std::string line;
        while (std::getline(std::cin, line)) {
            if (line == "/quit") {
                break;
            }

            std::shared_ptr<rtc::DataChannel> dc;
            {
                std::lock_guard<std::mutex> lock(dataChannelMutex);
                dc = dataChannel;
            }

            if (!dc || !dc->isOpen()) {
                std::cout << "DataChannel is not open yet." << std::endl;
                continue;
            }
            dc->send(line);
        }

        running = false;
        if (signalingThread.joinable()) {
            signalingThread.join();
        }
        dataChannel.reset();
        pc->close();
        pc.reset();
        return 0;
    } catch (const std::exception &exc) {
        std::cerr << "Error: " << exc.what() << std::endl;
        printUsage(argv[0]);
        return 1;
    }
}
