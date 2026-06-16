#include "ApiKeyStore.h"
#include "AuthenticationService.h"
#include <iostream>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/json_parser.hpp>
#include <openssl/evp.h>
#include <iomanip>
#include <sstream>

namespace DIGITAL_TWIN_SERVER {

    static std::string computeSHA256(const std::string& unhashed) {
        EVP_MD_CTX* context = EVP_MD_CTX_new();
        const EVP_MD* md = EVP_sha256();
        unsigned char hash[EVP_MAX_MD_SIZE];
        unsigned int lengthOfHash = 0;

        EVP_DigestInit_ex(context, md, nullptr);
        EVP_DigestUpdate(context, unhashed.c_str(), unhashed.length());
        EVP_DigestFinal_ex(context, hash, &lengthOfHash);
        EVP_MD_CTX_free(context);

        std::stringstream ss;
        for (unsigned int i = 0; i < lengthOfHash; ++i) {
            ss << std::hex << std::setw(2) << std::setfill('0') << (int)hash[i];
        }
        return ss.str();
    }

    ApiKeyStore::ApiKeyStore() {
        loadKeys("pt_api_keys.json");
    }

    ApiKeyStore::~ApiKeyStore() {}

    void ApiKeyStore::loadKeys(const std::string& configPath) {
        std::lock_guard<std::recursive_mutex> lock(_storeMutex);
        try {
            boost::property_tree::ptree pt;
            boost::property_tree::read_json(configPath, pt);
            
            _deviceAcls.clear();
            for (auto& device : pt) {
                std::string apiKey = device.first;
                DeviceConfig config;
                config.deviceId = device.second.get<std::string>("device_id");
                config.projectId = device.second.get<std::string>("project");
                _deviceAcls[apiKey] = config;
            }
            std::cout << "[ApiKeyStore] Loaded API Key config with " << _deviceAcls.size() << " devices.\n";
        } catch (const std::exception& e) {
            std::cerr << "[ApiKeyStore] Failed to load config from " << configPath << ": " << e.what() << "\n";
        }
    }

    bool ApiKeyStore::validateApiKey(const std::string& apiKey, Principal& outPrincipal) {
        std::lock_guard<std::recursive_mutex> lock(_storeMutex);
        // Reload for dynamic updates
        loadKeys("pt_api_keys.json");

        std::string hashedKey = computeSHA256(apiKey);
        auto it = _deviceAcls.find(hashedKey);
        if (it != _deviceAcls.end()) {
            outPrincipal.id = it->second.deviceId;
            outPrincipal.authorizedProjectIds = { it->second.projectId };
            outPrincipal.isPhysicalTwin = true;
            
            std::cout << "[ApiKeyStore] Physical Twin '" << outPrincipal.id 
                      << "' authenticated successfully via API Key.\n";
            return true;
        }
        
        std::cout << "[ApiKeyStore] Physical Twin authentication failed: Invalid API Key.\n";
        return false;
    }

} // namespace DIGITAL_TWIN_SERVER
