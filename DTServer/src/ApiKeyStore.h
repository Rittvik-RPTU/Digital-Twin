#pragma once

#include <string>
#include <map>
#include <mutex>

namespace DIGITAL_TWIN_SERVER {

    struct Principal;

    class ApiKeyStore {
    public:
        ApiKeyStore();
        ~ApiKeyStore();

        void loadKeys(const std::string& configPath);
        bool validateApiKey(const std::string& apiKey, Principal& outPrincipal);

    private:
        struct DeviceConfig {
            std::string deviceId;
            std::string projectId;
        };
        std::map<std::string, DeviceConfig> _deviceAcls;
        std::recursive_mutex _storeMutex;
    };

} // namespace DIGITAL_TWIN_SERVER
